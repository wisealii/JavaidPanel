"""Javid Node enrollment records (offline core; NOT a network/API or mTLS service).

Secure properties provided here:
- CSPRNG bearer tokens shown once; only SHA-256 digests stored.
- SQLite transactions enforce one-time claims under concurrent workers.
- Short, bounded TTL, explicit revocation, IP/hostname validation.
- No shell execution, no SSH credentials, no server-side arbitrary commands.

Missing for deployment: authenticated administrator API, client proof of private-key
possession, TLS trust, actual certificates, node agent and heartbeat validation.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

_MAX_TTL_SECONDS = 1800
_MIN_TTL_SECONDS = 60
_HOST_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")
_FINGERPRINT = re.compile(r"^[a-fA-F0-9]{64}$")


class EnrollmentError(Exception):
    """Invalid input or non-consumable enrollment token."""


@dataclass(frozen=True)
class Invitation:
    node_id: str
    enrollment_id: str
    token: str  # Only returned to caller, never saved as plaintext.
    expires_at: int


@dataclass(frozen=True)
class ClaimedNode:
    node_id: str
    name: str
    host: str
    fingerprint: str
    claimed_at: int


def normalize_host(host: str) -> str:
    if not isinstance(host, str):
        raise EnrollmentError("Host must be a string")
    host = host.strip()
    if not host or len(host) > 253 or any(x in host for x in ("/", "\\", " ", "\t", "\n", "@", ":")):
        # Colons are accepted only through the IPv6 parser below.
        try:
            return str(ipaddress.ip_address(host))
        except ValueError as exc:
            raise EnrollmentError("Invalid IP or DNS hostname") from exc
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        pass
    if not all(_HOST_LABEL.fullmatch(label) for label in host.rstrip(".").split(".")):
        raise EnrollmentError("Invalid DNS hostname")
    if "." not in host or host.endswith(".."):
        raise EnrollmentError("Fully qualified hostname required")
    return host.rstrip(".").lower()


def _db_connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=10000")
    return con


class EnrollmentStore:
    """Persistence-only layer. Callers MUST implement admin auth and rate limits."""

    def __init__(self, db_path: str | Path, clock: Callable[[], float] = time.time):
        self.db_path = str(db_path)
        self.clock = clock
        parent = Path(self.db_path).parent
        if not parent.is_dir():
            raise EnrollmentError("Parent directory of enrollment DB must exist")
        # The deployment layer must create its parent directory with mode 0700.
        with _db_connect(self.db_path) as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'pending',
                    fingerprint TEXT UNIQUE,
                    claimed_at INTEGER,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS enrollments (
                    id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL REFERENCES nodes(id),
                    token_sha256 TEXT NOT NULL UNIQUE,
                    expires_at INTEGER NOT NULL,
                    used_at INTEGER,
                    revoked_at INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_enrollments_node
                    ON enrollments(node_id);
            """)
        # This permission is for the file only; directory permissions are
        # intentionally outside the library's control.
        Path(self.db_path).chmod(0o600)

    def create(self, name: str, host: str, ttl_seconds: int = 600) -> Invitation:
        if not isinstance(name, str) or not (1 <= len(name.strip()) <= 100):
            raise EnrollmentError("Node name length must be 1..100")
        if any(ord(ch) < 32 for ch in name):
            raise EnrollmentError("Node name may not contain control chars")
        if type(ttl_seconds) is not int or not (_MIN_TTL_SECONDS <= ttl_seconds <= _MAX_TTL_SECONDS):
            raise EnrollmentError("TTL must be an integer between 60 and 1800 seconds")
        host = normalize_host(host)
        now = int(self.clock())
        node_id, invitation_id = str(uuid.uuid4()), str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode("ascii")).hexdigest()
        with _db_connect(self.db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute(
                    "INSERT INTO nodes(id, name, host, created_at) VALUES(?, ?, ?, ?)",
                    (node_id, name.strip(), host, now),
                )
                con.execute(
                    "INSERT INTO enrollments(id, node_id, token_sha256, expires_at) VALUES(?, ?, ?, ?)",
                    (invitation_id, node_id, digest, now + ttl_seconds),
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        return Invitation(node_id, invitation_id, token, now + ttl_seconds)

    def claim(self, enrollment_id: str, token: str, fingerprint: str) -> ClaimedNode:
        """Consume once; caller must independently verify key possession/TLS."""
        if not isinstance(enrollment_id, str) or not isinstance(token, str) or not isinstance(fingerprint, str):
            raise EnrollmentError("Invalid claim fields")
        if len(token) > 256 or len(token) < 32 or not _FINGERPRINT.fullmatch(fingerprint):
            raise EnrollmentError("Invalid token or public key fingerprint")
        now = int(self.clock())
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with _db_connect(self.db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                row = con.execute(
                    """SELECT e.node_id, n.name, n.host
                       FROM enrollments e JOIN nodes n ON n.id=e.node_id
                       WHERE e.id=? AND e.token_sha256=?
                       AND e.used_at IS NULL AND e.revoked_at IS NULL
                       AND e.expires_at>? AND n.state='pending'""",
                    (enrollment_id, digest, now),
                ).fetchone()
                if row is None:
                    raise EnrollmentError("Invalid, expired, used or revoked enrollment")
                node_id, name, host = row
                result = con.execute(
                    "UPDATE enrollments SET used_at=? WHERE id=? AND used_at IS NULL",
                    (now, enrollment_id),
                )
                if result.rowcount != 1:
                    raise EnrollmentError("Enrollment already used")
                con.execute(
                    "UPDATE nodes SET fingerprint=?, state='claimed', claimed_at=? WHERE id=?",
                    (fingerprint.lower(), now, node_id),
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        return ClaimedNode(node_id, name, host, fingerprint.lower(), now)

    def revoke(self, enrollment_id: str) -> bool:
        if not isinstance(enrollment_id, str):
            raise EnrollmentError("Invalid enrollment ID")
        with _db_connect(self.db_path) as con:
            con.execute("BEGIN IMMEDIATE")
            result = con.execute(
                "UPDATE enrollments SET revoked_at=? WHERE id=? AND used_at IS NULL AND revoked_at IS NULL",
                (int(self.clock()), enrollment_id),
            )
            con.execute("COMMIT")
        return result.rowcount == 1

    def state(self, node_id: str) -> str | None:
        with _db_connect(self.db_path) as con:
            row = con.execute("SELECT state FROM nodes WHERE id=?", (node_id,)).fetchone()
        return row[0] if row else None
