#!/usr/bin/env python3
"""Read-only audit: verify evidence paths and source markers for CURRENT_FEATURES.json.

Do not equate presence in source with working VPN, SSL or production readiness.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def audit(root: pathlib.Path=ROOT) -> tuple[list[dict], list[str]]:
    data=json.loads((root/"docs/CURRENT_FEATURES.json").read_text(encoding="utf-8"))
    errors=[]
    result=[]
    if data.get("version") != (root/"VERSION").read_text().strip():
        errors.append("Catalog version differs from project VERSION")
    features=data.get("features",[])
    ids=set()
    for idx,item in enumerate(features):
        label=item.get("name","")
        key=(item.get("area"),label)
        if not label or key in ids:
            errors.append(f"Invalid or duplicate inventory item {idx}")
        ids.add(key)
        rel=item.get("file","")
        evidence=item.get("marker","")
        path=root/rel
        if path.is_symlink() or not path.is_file() or not str(path.resolve()).startswith(str(root.resolve())+"/"):
            errors.append(f"Missing/unsafe source for {label}: {rel}")
            continue
        source=path.read_text(encoding="utf-8")
        if not evidence or evidence not in source:
            errors.append(f"Evidence not found for {label}: {evidence}")
        result.append({"area":item["area"],"name":label,"scope":item["scope"],"source_evidence":rel,
                       "review_status":item["status"],"vps_verified":False})
    return result,errors

def main(argv=None):
    parser=argparse.ArgumentParser(description="Source-only JavaidPanel current capabilities inventory")
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    features,errors=audit()
    if args.json:
        print(json.dumps({"features":features,"errors":errors,"vps_verified":False},ensure_ascii=False,indent=2))
    else:
        for f in features:
            print(f"[{f['review_status']}] {f['area']}: {f['name']}  ({f['source_evidence']})")
        for err in errors:
            print("AUDIT ERROR: "+err,file=sys.stderr)
        print(f"Inventory: {len(features)} checked, {len(errors)} source errors. VPS validation not performed.")
    return 2 if errors else 0

if __name__=="__main__":
    raise SystemExit(main())
