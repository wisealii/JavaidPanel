"""Offline tests for one-time node enrollment persistence.

No listening port, API, SSH, VPN or other network operation is performed.
"""
from __future__ import annotations
import hashlib
import os
import pathlib
import sqlite3
import sys
import tempfile
import threading
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from javid_panel.nodes.enrollment import EnrollmentError, EnrollmentStore, normalize_host

FINGERPRINT = "ab" * 32

class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.time = [1_800_000_000]
        self.path = pathlib.Path(self.temp.name) / "nodes.sqlite3"
        self.store = EnrollmentStore(self.path, clock=lambda: self.time[0])

    def test_token_only_stored_as_hash(self):
        inv = self.store.create("Germany-1", "node.example.org")
        raw = self.path.read_bytes()
        self.assertNotIn(inv.token.encode(), raw)
        with sqlite3.connect(self.path) as con:
            digest,=con.execute("SELECT token_sha256 FROM enrollments WHERE id=?", (inv.enrollment_id,)).fetchone()
        self.assertEqual(digest,hashlib.sha256(inv.token.encode()).hexdigest())
        if os.name=="posix":
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_claim_single_use(self):
        inv = self.store.create("Test", "203.0.113.5")
        claimed = self.store.claim(inv.enrollment_id, inv.token, FINGERPRINT)
        self.assertEqual(claimed.node_id, inv.node_id)
        self.assertEqual(self.store.state(inv.node_id), "claimed")
        with self.assertRaises(EnrollmentError):
            self.store.claim(inv.enrollment_id, inv.token, "bc"*32)

    def test_wrong_token_does_not_consume(self):
        inv = self.store.create("Test", "2001:db8::1")
        with self.assertRaises(EnrollmentError):
            self.store.claim(inv.enrollment_id, "x"*44, FINGERPRINT)
        self.assertEqual(self.store.state(inv.node_id), "pending")
        self.store.claim(inv.enrollment_id, inv.token, FINGERPRINT)

    def test_expired_token_rejected(self):
        inv = self.store.create("Test", "node.example.org", ttl_seconds=60)
        self.time[0] += 60
        with self.assertRaises(EnrollmentError):
            self.store.claim(inv.enrollment_id, inv.token, FINGERPRINT)

    def test_revocation(self):
        inv = self.store.create("Test", "node.example.org")
        self.assertTrue(self.store.revoke(inv.enrollment_id))
        self.assertFalse(self.store.revoke(inv.enrollment_id))
        with self.assertRaises(EnrollmentError):
            self.store.claim(inv.enrollment_id, inv.token, FINGERPRINT)

    def test_invalid_hosts_rejected(self):
        for host in ["", "localhost", "foo bar", "example..org", "x;rm -rf /", "a/../b", "a@b.com", "192.0.2.999"]:
            with self.subTest(host=host):
                with self.assertRaises(EnrollmentError):
                    self.store.create("Test", host)
        self.assertEqual(normalize_host("NODE.Example.ORG."), "node.example.org")
        self.assertEqual(normalize_host("2001:db8::1"), "2001:db8::1")

    def test_ttl_validation(self):
        for value in [0, 30, 1801, True, "60"]:
            with self.subTest(value=value):
                with self.assertRaises(EnrollmentError):
                    self.store.create("Test", "node.example.org", value)

    def test_bad_fingerprint_rejected_without_claim(self):
        inv = self.store.create("Test", "node.example.org")
        with self.assertRaises(EnrollmentError):
            self.store.claim(inv.enrollment_id, inv.token, "not-a-key")
        self.store.claim(inv.enrollment_id, inv.token, FINGERPRINT)

    def test_concurrent_claim_at_most_one(self):
        inv = self.store.create("Test", "node.example.org")
        won=[]
        failures=[]
        def worker():
            store=EnrollmentStore(self.path,clock=lambda: self.time[0])
            try:
                won.append(store.claim(inv.enrollment_id, inv.token, FINGERPRINT))
            except EnrollmentError as exc:
                failures.append(str(exc))
        threads=[threading.Thread(target=worker) for _ in range(6)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(len(won),1)
        self.assertEqual(len(failures),5)

if __name__=="__main__":
    unittest.main()
