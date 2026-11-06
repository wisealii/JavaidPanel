#!/usr/bin/env python3
"""Auditable, read-only release gate for JavaidPanel.

Does NOT install services, request certificates, or claim any VPS was tested.
A successful CI check of this script means the *gate itself* works; it does
not imply that the product is production ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import asdict, dataclass

ROOT = pathlib.Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    code: str
    status: str  # pass, blocked or manual
    message: str
    next_action: str

    @property
    def ready(self) -> bool:
        return self.status == "pass"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def run_checks(root: pathlib.Path | None = None) -> list[Check]:
    global ROOT
    if root is not None:
        ROOT = pathlib.Path(root)
    checks: list[Check] = []
    def add(code: str, status: str, message: str, action: str = "") -> None:
        checks.append(Check(code, status, message, action))

    # Match authoritative version with the entry point actually delivered.
    version_file = ROOT / "VERSION"
    script_file = ROOT / "install.sh"
    if not version_file.is_file() or not script_file.is_file():
        add("release_metadata", "blocked", "VERSION or install.sh missing", "Restore entrypoint and version file")
        return checks
    version = version_file.read_text(encoding="utf-8").strip()
    entrypoint = script_file.read_text(encoding="utf-8")
    found = re.search(r"^VERSION=([^\n#]+)$", entrypoint, re.M)
    literal = found.group(1).strip().replace(chr(34), "").replace(chr(39), "") if found else ""
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", version):
        add("release_metadata", "blocked", "Invalid VERSION syntax", "Use SemVer or a -dev suffix")
    elif version != literal:
        add("release_metadata", "blocked",
            f"VERSION is {version} but install.sh declares {literal!r}",
            "Keep installer VERSION and root VERSION consistent")
    else:
        add("release_metadata", "pass", f"Release metadata aligned: {version}")

    core = ROOT / "installer/core.sh"
    pin = re.search(r'^CORE_SHA256="([0-9a-f]{64})"$', entrypoint, re.M)
    if not core.is_file() or pin is None:
        add("pinned_engine", "blocked", "Missing pinned integration engine / checksum")
    else:
        actual = hashlib.sha256(core.read_bytes()).hexdigest()
        if actual != pin.group(1):
            add("pinned_engine", "blocked", "Pinned engine SHA-256 does not match",
                "Verify supply chain; update checksum only after source review")
        else:
            add("pinned_engine", "pass", "Pinned integration engine checksum matches")

    for path in ["install.sh", "installer/core.sh", "node-agent-install.sh",
                 "tools/install-control-plane.sh", "tools/ssl-wizard.sh"]:
        if not (ROOT / path).is_file():
            add("shell_" + path.replace("/", "_"), "blocked", f"Missing {path}")
            continue
        try:
            result = subprocess.run(["bash", "-n", str(ROOT / path)],
                                    capture_output=True, text=True, timeout=10)
            status = "pass" if result.returncode == 0 else "blocked"
            add("shell_" + path.replace("/", "_"), status,
                f"Shell syntax {'OK' if status == 'pass' else 'failed'}: {path}")
        except (OSError, subprocess.TimeoutExpired):
            add("shell_" + path.replace("/", "_"), "blocked", f"Could not check shell: {path}")

    # The intended one-command entry point remains the local pinned bootstrap.
    if "CORE_SHA256" in entrypoint and "sha256sum --check" in entrypoint:
        add("one_command_entrypoint", "pass", "Pinned one-command bootstrap exists (not VPS-tested)")
    else:
        add("one_command_entrypoint", "blocked", "Installer checksum protection unavailable")

    # A file labeled production must not advertise a broken deployment method.
    compose = ROOT / "docker-compose.production.yml"
    if compose.is_file():
        missing = [name for name in ("Dockerfile", "nginx/nginx.conf")
                   if not (ROOT / name).is_file()]
        if missing:
            add("compose_production", "blocked",
                "Production Compose references missing files: " + ", ".join(missing),
                "Implement and test matching Dockerfile/Nginx, or retire untested Compose")
        else:
            add("compose_production", "manual",
                "Compose input files exist but production build was not tested",
                "Run Compose validation and integration tests")
    else:
        add("compose_production", "pass",
            "No untested alternative production Compose path advertised")

    essential = ["src/javid_panel/nodes/api.py", "src/javid_panel/nodes/runtime.py",
                 "src/javid_panel/nodes/agent.py", "src/javid_panel/nodes/dashboard.html",
                 "src/javid_panel/nodes/dashboard.js", "src/javid_panel/nodes/dashboard.css",
                 "node-agent-install.sh"]
    missing = [p for p in essential if not (ROOT / p).is_file()]
    if missing:
        add("node_control_files", "blocked", "Node files missing: " + ", ".join(missing))
    else:
        add("node_control_files", "pass", "Standalone node control and dashboard sources present")

    # These cannot be verified by inspecting a repository or a CI build alone.
    add("gateway_integration", "manual",
        "Standalone node UI is not yet authenticated by the main Gateway",
        "Implement/test shared gateway identities and RBAC before public access")
    add("administrator_setup", "manual",
        "Initial domain, SSL, admin credentials, database and login not E2E-tested",
        "Demonstrate successful fresh install/login with sanitized logs and screenshots")
    add("real_vps_install", "manual",
        "No signed/manual-reviewed evidence of fresh Ubuntu/Debian VPS installation",
        "Test on isolated VPS, verify services, SSL and reboots, record environment")
    add("real_two_vps_node", "manual",
        "No evidence of secure enrollment and heartbeat between two actual VPS",
        "Test certificate validation, token expiry/revocation, disconnect/reconnect")
    add("vpn_protocols", "manual",
        "No protocol-by-protocol real client connection and recovery matrix",
        "Run E2E VPN client tests, traffic and restart checks")
    add("backup_restore", "manual",
        "No real server backup/restore/migration and rollback proof",
        "Test restore in separate VPS/VM with persistent data")
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="JavaidPanel release-readiness audit (read only)")
    parser.add_argument("--json", action="store_true", help="Machine readable checks")
    parser.add_argument("--strict", action="store_true",
                        help="Fail unless all release gates have evidence and pass")
    parser.add_argument("--fail-on-blocked", action="store_true",
                        help="Fail on source defects, but allow unverified manual gates")
    args = parser.parse_args(argv)
    checks = run_checks()
    ready = all(c.ready for c in checks)
    if args.json:
        print(json.dumps({"production_ready": ready, "checks": [asdict(c) for c in checks]},
                         ensure_ascii=False, indent=2))
    else:
        for c in checks:
            print(f"[{c.status.upper():7}] {c.code}: {c.message}")
            if c.status != "pass" and c.next_action:
                print(f"             Next: {c.next_action}")
        print(f"\nVPS PRODUCTION READY: {'YES' if ready else 'NO (verification incomplete)'}")
    if args.strict and not ready:
        return 2
    if args.fail_on_blocked and any(c.status == "blocked" for c in checks):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
