"""Unit tests for read-only VPS smoke checks; no systemctl or live VPS calls."""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("vps_smoke",ROOT/"tools/vps-postinstall-smoke.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        self.config=self.root/"etc"
        self.config.mkdir()
        self.access=self.config/"access.json"
        self.access.write_text(json.dumps({"username":"admin","password":"SECRET-MUST-NOT-PRINT"}))
        self.access.chmod(0o600)
        self.gateway=self.config/"gateway.json"
        self.gateway.write_text(json.dumps({"port":8443,"tls_mode":"domain","password":"PRIVATE-MUST-NOT-PRINT"}))
        self.gateway.chmod(0o640)

    def test_config_checks_never_include_secrets(self):
        checks=mod.inspect_config(self.config)
        self.assertTrue(all(c["status"]!="fail" for c in checks))
        data=json.dumps(checks)
        self.assertNotIn("SECRET-MUST-NOT-PRINT",data)
        self.assertNotIn("PRIVATE-MUST-NOT-PRINT",data)
        self.assertTrue(any(x["check"]=="trusted_tls" and x["status"]=="manual" for x in checks))

    def test_world_readable_secrets_rejected(self):
        self.access.chmod(0o644)
        checks=mod.inspect_config(self.config)
        item=next(x for x in checks if x["check"]=="access_file_permissions")
        self.assertEqual(item["status"],"fail")

    def test_config_symlinks_rejected(self):
        self.access.unlink()
        self.access.symlink_to(self.gateway)
        checks=mod.inspect_config(self.config)
        self.assertEqual(checks[0]["status"],"fail")

    def test_valid_sqlite_read_only(self):
        db=self.root/"vpn.db"
        conn=sqlite3.connect(db)
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        self.assertEqual(mod.inspect_db(db)["status"],"pass")

    def test_missing_sqlite(self):
        self.assertEqual(mod.inspect_db(self.root/"missing.db")["status"],"fail")
        self.assertFalse((self.root/"missing.db").exists())

    def test_check_mode_does_not_query_server(self):
        self.assertEqual(mod.main(["--check"]),0)

if __name__=="__main__":
    unittest.main()
