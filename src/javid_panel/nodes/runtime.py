"""Javid Node control-plane persistence and authenticated heartbeats.

Enrollment tokens are single-use and short-lived. Node HMAC keys are derived from
an operator-held master secret, never stored in SQLite. This is an experimental
control-plane layer: it does not run VPN tunnels or implement mTLS.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

HOST_LABEL = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$')
FINGERPRINT = re.compile(r'^[a-f0-9]{64}$')
UUID = re.compile(r'^[0-9a-fA-F-]{36}$')


class NodeError(ValueError):
    pass


def validate_host(raw: str) -> str:
    if not isinstance(raw, str) or not raw or len(raw) > 253 or raw != raw.strip():
        raise NodeError('Invalid node host')
    if any(ch in raw for ch in ('/', '\\', ' ', '\n', '\r', '\t', '@', '?', '#')):
        raise NodeError('Invalid node host')
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        if ':' in raw or re.fullmatch(r'[0-9.]+', raw):
            raise NodeError('Invalid node IP address')
    hostname = raw.rstrip('.').lower()
    if '.' not in hostname or not all(HOST_LABEL.fullmatch(x) for x in hostname.split('.')):
        raise NodeError('Fully qualified hostname required')
    return hostname


def _connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA busy_timeout=10000')
    return con


def canonical_message(node_id: str, counter: int, at: int, payload: dict) -> bytes:
    return json.dumps({'node_id': node_id, 'counter': counter, 'timestamp': at,
                       'payload': payload}, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True).encode('ascii')


@dataclass(frozen=True)
class Invite:
    node_id: str
    enrollment_id: str
    token: str
    expires_at: int


@dataclass(frozen=True)
class NodeCredential:
    node_id: str
    key: str  # base64url ASCII secret; returned once over a protected HTTPS connection


class NodeRegistry:
    def __init__(self, path: str | Path, master_key: bytes, clock: Callable[[], float] = time.time):
        if not isinstance(master_key, bytes) or len(master_key) < 32:
            raise NodeError('Node master key must contain at least 32 random bytes')
        self.path = str(path)
        self.master_key = master_key
        self.clock = clock
        parent = Path(self.path).parent
        if not parent.is_dir() or (parent.stat().st_mode & 0o077):
            raise NodeError('Database parent directory must exist and be private (0700)')
        if Path(self.path).exists() and Path(self.path).stat().st_mode & 0o077:
            raise NodeError('Refusing database with insecure file permissions')
        with _connect(self.path) as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS nodes (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, host TEXT NOT NULL,
              state TEXT NOT NULL DEFAULT 'pending',
              key_id TEXT UNIQUE, created_at INTEGER NOT NULL,
              claimed_at INTEGER, last_seen INTEGER, last_counter INTEGER NOT NULL DEFAULT 0,
              last_payload TEXT, revoked_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS enrollments (
              id TEXT PRIMARY KEY, node_id TEXT NOT NULL REFERENCES nodes(id),
              token_sha256 TEXT NOT NULL UNIQUE, expires_at INTEGER NOT NULL,
              used_at INTEGER, revoked_at INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_seen ON nodes(last_seen);
            ''')
        Path(self.path).chmod(0o600)

    def _key(self, node_id: str, key_id: str) -> bytes:
        return hmac.new(self.master_key, (node_id + ':' + key_id).encode('ascii'), hashlib.sha256).digest()

    def create(self, name: str, host: str, ttl: int = 600) -> Invite:
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100 or any(ord(c) < 32 for c in name):
            raise NodeError('Node name must be 1..100 printable characters')
        host = validate_host(host)
        if type(ttl) is not int or not 60 <= ttl <= 1800:
            raise NodeError('Enrollment TTL must be 60..1800 seconds')
        now = int(self.clock())
        node_id, enrollment_id = str(uuid.uuid4()), str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode('ascii')).hexdigest()
        with _connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            con.execute('INSERT INTO nodes(id,name,host,created_at) VALUES(?,?,?,?)',
                        (node_id, name.strip(), host, now))
            con.execute('INSERT INTO enrollments(id,node_id,token_sha256,expires_at) VALUES(?,?,?,?)',
                        (enrollment_id, node_id, digest, now + ttl))
            con.execute('COMMIT')
        return Invite(node_id, enrollment_id, token, now + ttl)

    def claim(self, enrollment_id: str, token: str) -> NodeCredential:
        if not isinstance(enrollment_id, str) or not UUID.fullmatch(enrollment_id):
            raise NodeError('Invalid enrollment ID')
        if not isinstance(token, str) or not 32 <= len(token) <= 256:
            raise NodeError('Invalid enrollment token')
        digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
        now = int(self.clock())
        with _connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            try:
                row = con.execute('''SELECT e.node_id FROM enrollments e JOIN nodes n ON n.id=e.node_id
                    WHERE e.id=? AND e.token_sha256=? AND e.used_at IS NULL
                    AND e.revoked_at IS NULL AND e.expires_at>? AND n.state='pending' ''',
                    (enrollment_id, digest, now)).fetchone()
                if row is None:
                    raise NodeError('Enrollment expired, invalid, revoked or already used')
                node_id = row[0]
                key_id = secrets.token_hex(24)
                con.execute('UPDATE enrollments SET used_at=? WHERE id=?', (now, enrollment_id))
                con.execute('UPDATE nodes SET state=?, key_id=?, claimed_at=? WHERE id=?',
                            ('claimed', key_id, now, node_id))
                con.execute('COMMIT')
            except Exception:
                con.execute('ROLLBACK')
                raise
        import base64
        secret = base64.urlsafe_b64encode(self._key(node_id, key_id)).decode('ascii').rstrip('=')
        return NodeCredential(node_id, secret)

    def heartbeat(self, node_id: str, counter: int, at: int, payload: dict, signature: str) -> None:
        if not isinstance(node_id, str) or not UUID.fullmatch(node_id):
            raise NodeError('Invalid node ID')
        if type(counter) is not int or not 1 <= counter <= 2**63-1:
            raise NodeError('Invalid heartbeat sequence')
        now = int(self.clock())
        if type(at) is not int or abs(now - at) > 120:
            raise NodeError('Heartbeat timestamp outside allowed window')
        if not isinstance(payload, dict) or len(payload) > 20:
            raise NodeError('Invalid heartbeat payload')
        if not isinstance(signature, str) or not FINGERPRINT.fullmatch(signature):
            raise NodeError('Invalid signature')
        encoded = canonical_message(node_id, counter, at, payload)
        if len(encoded) > 2048:
            raise NodeError('Heartbeat payload too large')
        with _connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            try:
                row = con.execute('SELECT key_id,last_counter,state,revoked_at FROM nodes WHERE id=?', (node_id,)).fetchone()
                if row is None or row[0] is None or row[2] not in ('claimed','online') or row[3] is not None:
                    raise NodeError('Node not enrolled or revoked')
                key_id, prev, _, _ = row
                expected = hmac.new(self._key(node_id, key_id), encoded, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(signature, expected):
                    raise NodeError('Heartbeat signature invalid')
                if counter <= prev:
                    raise NodeError('Replayed heartbeat sequence')
                con.execute('''UPDATE nodes SET state='online', last_seen=?, last_counter=?, last_payload=?
                    WHERE id=?''', (now, counter, json.dumps(payload, sort_keys=True), node_id))
                con.execute('COMMIT')
            except Exception:
                con.execute('ROLLBACK')
                raise

    def revoke(self, node_id: str) -> bool:
        now = int(self.clock())
        with _connect(self.path) as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute("UPDATE nodes SET state='revoked',revoked_at=?,key_id=NULL WHERE id=? AND revoked_at IS NULL",
                              (now, node_id))
            con.execute('UPDATE enrollments SET revoked_at=? WHERE node_id=? AND used_at IS NULL', (now, node_id))
            con.execute('COMMIT')
        return row.rowcount == 1

    def list_nodes(self, stale_after: int = 90) -> list[dict]:
        now = int(self.clock())
        with _connect(self.path) as con:
            rows = con.execute('''SELECT id,name,host,state,created_at,claimed_at,last_seen,last_counter,
                revoked_at,last_payload FROM nodes ORDER BY created_at DESC''').fetchall()
        result = []
        for id_,name,host,state,created,claimed,seen,counter,revoked,payload in rows:
            visible = 'offline' if state == 'online' and (seen is None or now-seen > stale_after) else state
            result.append({'id': id_, 'name': name, 'host': host, 'state': visible,
                           'created_at': created, 'claimed_at': claimed, 'last_seen': seen,
                           'last_counter': counter, 'revoked_at': revoked,
                           'health': json.loads(payload) if payload else None})
        return result
