#!/usr/bin/env python3
"""Atomic-ish, rollback-capable upgrade of the standalone Javid Node controller.

Replaces ONLY /opt/javid-control/src; does not alter config, database,
systemd unit, Nginx, certificates or other JavaidPanel services.

The two directory renames form a short non-atomic swap. If restart or
loopback health fails, the former source directory is restored.
A real VPS upgrade has NOT been tested; run --plan before --apply.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from urllib import error, request


class UpgradeError(RuntimeError):
    pass


REQUIRED = (
    "javid_panel/__init__.py",
    "javid_panel/nodes/__init__.py",
    "javid_panel/nodes/api.py",
    "javid_panel/nodes/runtime.py",
    "javid_panel/nodes/agent.py",
    "javid_panel/nodes/dashboard.html",
    "javid_panel/nodes/dashboard.js",
    "javid_panel/nodes/dashboard.css",
)


def audit_source(source: pathlib.Path) -> dict[str, str]:
    """Verify all target assets and reject symlinks in deployable source."""
    if not source.is_dir() or source.is_symlink():
        raise UpgradeError("Source directory is missing or is a symlink")
    for file in source.rglob("*"):
        if file.is_symlink():
            raise UpgradeError(f"Symlinks are not permitted in the source tree: {file}")
    checksums = {}
    for rel in REQUIRED:
        path = source / rel
        if not path.is_file() or path.is_symlink():
            raise UpgradeError(f"Missing required source: {rel}")
        raw = path.read_bytes()
        if rel.endswith(".py"):
            compile(raw, str(path), "exec")
        checksums[rel] = hashlib.sha256(raw).hexdigest()
    return checksums


def validate_install(target: pathlib.Path, config: pathlib.Path, unit: pathlib.Path) -> None:
    if not target.is_dir() or target.is_symlink():
        raise UpgradeError("Controller source not installed; use --install on a test VPS")
    if not (target / "javid_panel/nodes/api.py").is_file():
        raise UpgradeError("Existing controller API missing")
    if config.is_symlink() or not config.is_file() or config.stat().st_mode & 0o077:
        raise UpgradeError("Private controller config missing or has unsafe permissions")
    if unit.is_symlink() or not unit.is_file():
        raise UpgradeError("Expected systemd unit missing")
    text = unit.read_text(encoding="utf-8")
    if "javid_panel.nodes.api serve" not in text or "127.0.0.1" not in text:
        raise UpgradeError("Unexpected systemd service; refusing to modify its source")
    if f"PYTHONPATH={target}" not in text:
        raise UpgradeError("systemd unit does not use the target controller path")


@contextmanager
def exclusive_lock(path: pathlib.Path):
    # The directory is managed by root in production; lock is never in /tmp.
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "r+") as locked:
            fcntl.flock(locked.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
    except BlockingIOError as exc:
        raise UpgradeError("Another node controller upgrade is already running") from exc


def systemctl_restart() -> bool:
    return subprocess.run(
        ["systemctl", "restart", "javid-node-control.service"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=30,
    ).returncode == 0


def loopback_healthy() -> bool:
    try:
        with request.urlopen("http://127.0.0.1:9443/healthz", timeout=2) as resp:
            if resp.status != 200:
                return False
            return b'"status":"ok"' in resp.read(4096)
    except (error.URLError, OSError, TimeoutError):
        return False


def wait_for_health(check, tries: int = 8, pause: float = 1.0) -> bool:
    for attempt in range(tries):
        if check():
            return True
        if attempt < tries - 1:
            time.sleep(pause)
    return False


def upgrade(source: pathlib.Path, target: pathlib.Path, config: pathlib.Path,
            unit: pathlib.Path, restart=systemctl_restart,
            healthy=loopback_healthy) -> pathlib.Path:
    source, target, config, unit = map(pathlib.Path, (source, target, config, unit))
    audit_source(source)
    validate_install(target, config, unit)
    target_parent = target.parent
    if target_parent.is_symlink() or not target_parent.is_dir():
        raise UpgradeError("Controller parent directory is unsafe")
    if source.resolve() == target.resolve():
        raise UpgradeError("Source and target must be different")

    with exclusive_lock(target_parent / ".javid-upgrade.lock"):
        # Check again after lock in case another operator changed deployment.
        validate_install(target, config, unit)
        if not healthy():
            raise UpgradeError("Old controller is not healthy; refusing unsafe upgrade")
        suffix = uuid.uuid4().hex[:12]
        staged = target_parent / (target.name + ".staging-" + suffix)
        backup = target_parent / (target.name + ".backup-" + suffix)
        if staged.exists() or backup.exists():
            raise UpgradeError("Unexpected staging or backup collision")

        # Capture file bytes, not just paths: any in-place credential mutation
        # by an unrelated component would invalidate the upgrade.
        before = hashlib.sha256(config.read_bytes()).digest()
        moved_old = False
        moved_new = False
        try:
            shutil.copytree(source, staged, symlinks=False)
            audit_source(staged)
            os.replace(target, backup)
            moved_old = True
            os.replace(staged, target)
            moved_new = True
            if not restart() or not wait_for_health(healthy):
                raise UpgradeError("New controller restart/health check failed")
            if hashlib.sha256(config.read_bytes()).digest() != before:
                raise UpgradeError("Controller config changed unexpectedly")
            return backup
        except Exception as exc:
            # Never wipe a backup when rollback fails. Preserve evidence and
            # let the operator recover manually.
            try:
                if moved_old:
                    if moved_new:
                        failed = target_parent / (target.name + ".failed-" + suffix)
                        os.replace(target, failed)
                    os.replace(backup, target)
                    if not restart() or not wait_for_health(healthy):
                        raise UpgradeError("Rollback restored source, but service health failed")
            except Exception as rollback_exc:
                raise UpgradeError(
                    f"Upgrade failed; manual recovery required. Backup: {backup}. "
                    f"Rollback error: {rollback_exc}"
                ) from exc
            raise UpgradeError(f"Upgrade aborted and old source restored: {exc}") from exc
        finally:
            if staged.exists():
                shutil.rmtree(staged)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Safe Javid Node controller source upgrade")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="Read-only checks; never restart")
    group.add_argument("--apply", action="store_true", help="Upgrade + rollback on failure")
    parser.add_argument("--source", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1] / "src")
    parser.add_argument("--target", type=pathlib.Path, default=pathlib.Path("/opt/javid-control/src"))
    parser.add_argument("--config", type=pathlib.Path,
                        default=pathlib.Path("/etc/javid-panel/node-control.json"))
    parser.add_argument("--unit", type=pathlib.Path,
                        default=pathlib.Path("/etc/systemd/system/javid-node-control.service"))
    args = parser.parse_args(argv)
    try:
        digest = audit_source(args.source)
        validate_install(args.target, args.config, args.unit)
        print(f"Source audit: {len(digest)} required files OK")
        print(f"Installed controller: {args.target}")
        print("Secrets/config and SQLite database are preserved, never overwritten.")
        if args.plan:
            print("PLAN only: no changes, restarts, or live health checks performed.")
            return 0
        if os.geteuid() != 0:
            raise UpgradeError("--apply requires root/sudo")
        if args.target != pathlib.Path("/opt/javid-control/src"):
            # Nonstandard target is for unit tests only, not CLI mutation.
            raise UpgradeError("CLI --apply restricted to standard controller path")
        backup = upgrade(args.source, args.target, args.config, args.unit)
        print(f"Upgrade succeeded. Old source backup kept at: {backup}")
        print("Verify live node heartbeats and take an external secure backup.")
        return 0
    except (UpgradeError, SyntaxError, OSError, ValueError) as exc:
        print(f"Javid Node upgrade ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
