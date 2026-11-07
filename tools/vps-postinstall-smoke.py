#!/usr/bin/env python3
"""Read-only JavaidPanel post-install smoke checks for a disposable VPS.

Does not print configuration secrets, make migrations, restart services,
open firewall ports, install packages or attempt a VPN tunnel.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys

ROOT = Path("/opt/alirezapanel")
CONFIG = Path("/etc/alirezapanel")
SERVICES = ("alirezapanel.service","alirezapanel-vpn.service","alirezapanel-dns.service")


def result(code: str, ok: bool, message: str, manual: bool=False) -> dict:
    return {"check":code, "status":"manual" if manual else ("pass" if ok else "fail"),"detail":message}


def private_file(path: Path, maximum_mode: int) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    mode=stat.S_IMODE(path.stat().st_mode)
    return (mode & ~maximum_mode) == 0


def inspect_db(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        return result("database_integrity",False,"Expected VPN database is missing or unsafe")
    try:
        # Read-only SQLite connection does not create databases or run migrations.
        db=sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,timeout=4)
        try:
            answer=db.execute("PRAGMA quick_check(1)").fetchone()
        finally:
            db.close()
        return result("database_integrity",answer is not None and answer[0]=="ok",
                      "SQLite quick_check completed" if answer and answer[0]=="ok" else "SQLite quick_check reported an error")
    except (sqlite3.Error,OSError,ValueError):
        return result("database_integrity",False,"SQLite read-only integrity check failed")


def inspect_config(config: Path=CONFIG) -> list[dict]:
    checks=[]
    access=config/"access.json"
    gateway=config/"gateway.json"
    checks.append(result("access_file_permissions",private_file(access,0o600),
                         "Access credentials are restricted to owner" if private_file(access,0o600) else "Access file missing/symlink or permissions too broad"))
    checks.append(result("gateway_file_permissions",private_file(gateway,0o640),
                         "Gateway settings permissions restricted" if private_file(gateway,0o640) else "Gateway config missing/symlink or permissions too broad"))
    if not private_file(gateway,0o640):
        return checks
    try:
        data=json.loads(gateway.read_text(encoding="utf-8"))
        port=data.get("port")
        tls=data.get("tls_mode")
        if type(port) is not int or not (1<=port<=65535):
            checks.append(result("gateway_config_schema",False,"Gateway port invalid"))
        elif tls not in ("domain","ip-acme","ip","none"):
            checks.append(result("gateway_config_schema",False,"Gateway TLS mode invalid"))
        else:
            checks.append(result("gateway_config_schema",True,"Gateway port and access mode valid (no secrets shown)"))
            checks.append(result("trusted_tls",False,
                                 "Actual external trusted HTTPS and ACME renewal still require separate validation",
                                 manual=True))
    except (OSError,ValueError,UnicodeError):
        checks.append(result("gateway_config_schema",False,"Cannot parse private gateway config"))
    return checks


def run_check(source_root: Path=ROOT, config: Path=CONFIG) -> list[dict]:
    checks=inspect_config(config)
    checks.append(inspect_db(source_root/"vpn/vpn-ui.db"))
    manager=source_root/"gateway/manage.py"
    checks.append(result("gateway_manager_exists",manager.is_file() and not manager.is_symlink(),
                         "Gateway management module present" if manager.is_file() and not manager.is_symlink() else "Gateway management module missing"))
    for unit in SERVICES:
        try:
            process=subprocess.run(["systemctl","is-active","--quiet",unit],timeout=8,check=False,
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            checks.append(result("service_"+unit,process.returncode==0,
                                 "Service is active" if process.returncode==0 else "Service is not active"))
        except (OSError,subprocess.TimeoutExpired):
            checks.append(result("service_"+unit,False,"Could not query systemd"))
    if manager.is_file() and not manager.is_symlink():
        try:
            proc=subprocess.run([sys.executable,str(manager),"probe"],timeout=15,check=False,
                                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            checks.append(result("gateway_readiness_probe",proc.returncode==0,
                                 "Gateway's own readiness probe succeeded" if proc.returncode==0 else "Gateway's own readiness probe failed"))
        except (OSError,subprocess.TimeoutExpired):
            checks.append(result("gateway_readiness_probe",False,"Gateway readiness probe unavailable/timed out"))
    checks.extend([
        result("administrator_login",False,"Manual login and password reset in browser required",manual=True),
        result("client_vpn_connection",False,"Real client VPN and traffic test required",manual=True),
        result("backup_restore",False,"Backup/restore must be tested on a separate VPS",manual=True)
    ])
    return checks


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="Read-only JavaidPanel VPS post-install smoke test")
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true",help="Check Python and files required by this tool, without accessing installed services")
    group.add_argument("--run",action="store_true",help="Read-only checks on an installed test VPS")
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    if args.check:
        print("JavaidPanel smoke-check tool syntax OK. No server inspection performed.")
        return 0
    if os.geteuid()!=0:
        print("ERROR: --run requires sudo to inspect the protected local installation",file=sys.stderr)
        return 2
    checks=run_check()
    if args.json:
        print(json.dumps({"checks":checks,"production_verified":False},ensure_ascii=False,indent=2))
    else:
        for item in checks:
            print(f"[{item['status'].upper()}] {item['check']}: {item['detail']}")
        print("No administrator secret, passwords or tokens have been printed.")
    return 2 if any(c["status"]=="fail" for c in checks) else 0


if __name__=="__main__":
    raise SystemExit(main())
