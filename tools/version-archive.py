#!/usr/bin/env python3
"""Build and validate a source-backed development version archive.

CHANGELOG headings are evidence of documented development milestones, NOT
evidence that a Git tag, GitHub Release or installable artifact exists.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
HEADING=re.compile(r"^##\s+(\d+\.\d+\.\d+(?:-dev)?)(?:\s*[—–-]\s*(.*))?\s*$")
VERSION=re.compile(r"^\d+\.\d+\.\d+(?:-dev)?$")


def collect(root: Path=ROOT) -> list[dict]:
    changelog=(root/"CHANGELOG.md").read_text(encoding="utf-8")
    items=[]
    for line in changelog.splitlines():
        match=HEADING.match(line)
        if match:
            items.append({"version":match.group(1),"title":(match.group(2) or "").strip(),
                          "features":[],"notes":[],"kind":"development_history",
                          "github_release_verified":False,"git_tag_verified":False})
        elif items and line.startswith("- "):
            note=line[2:].strip()
            if note:
                items[-1]["notes"].append(note)
                if not re.search(r"\b(?:not|no |without|pending|unverified|remain|does not|still|未)\b",note,re.I):
                    items[-1]["features"].append(note)
    return items


def validate(root: Path=ROOT) -> list[str]:
    errors=[]
    version=(root/"VERSION").read_text(encoding="utf-8").strip()
    if not VERSION.fullmatch(version):
        errors.append("VERSION format invalid")
    records=collect(root)
    if not records or records[0]["version"]!=version:
        errors.append("First CHANGELOG entry must match VERSION")
    if not records:
        return errors
    if not records[0]["notes"]:
        errors.append("Latest CHANGELOG entry has no release notes")
    for item in records:
        if not item["notes"]:
            errors.append("Empty changelog entry: "+item["version"])
    return errors


def render(root: Path=ROOT) -> str:
    records=collect(root)
    lines=["# آرشیو نسخه‌های توسعه JavaidPanel","",
           "> این فهرست به‌صورت خودکار از CHANGELOG.md تولید می‌شود. "
           "ورودی‌های تاریخی به معنی وجود Git tag، GitHub Release یا فایل نصب مستقل نیستند.",
           "",
           "نسخه فعال: **"+(root/"VERSION").read_text().strip()+"**",
           "",
           "| نسخه ثبت‌شده | تغییرات مستند | نوع |",
           "|---|---|---|"]
    for i,item in enumerate(records):
        label=item["title"].replace("|","\\|") or "تغییرات توسعه"
        lines.append("| `"+item["version"]+"` | "+label+" | "+("توسعه فعلی" if i==0 else "تاریخچه توسعه")+" |")
    lines+=["","## جزئیات نسخه‌ها",""]
    for item in records:
        lines.append("### "+item["version"]+((" — "+item["title"]) if item["title"] else ""))
        lines.append("")
        lines.extend("- "+note for note in item["notes"])
        lines.append("")
    lines+=["## تفاوت تاریخچه و انتشار رسمی","",
            "- **Development milestone:** مدرک آن ورودی CHANGELOG است؛ ممکن است تگ یا بستهٔ مستقل نداشته باشد.",
            "- **Git tag:** تنها وقتی معتبر است که واقعاً روی Commit مشخص ایجاد و تأیید شود.",
            "- **GitHub Release:** تنها وقتی معتبر است که در GitHub منتشر شده و URL واقعی داشته باشد.",
            "- **Production release:** نیازمند موفقیت تست VPS، SSL، بازیابی و اتصال کلاینت واقعی است.",
            "",
            "تا زمان وجود شواهد کافی، هیچ نسخه‌ای را پایدار یا تأییدشده روی VPS معرفی نکنید.",
            "",
            "[CHANGELOG](../CHANGELOG.md) · [قواعد انتشار](RELEASE_PROCESS.md) · [آمادگی نصب](RELEASE_READINESS.md)",
            ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description="Verify/generate development version history")
    p.add_argument("--check",action="store_true",help="Check archive matches changelog without writing")
    p.add_argument("--json",action="store_true",help="Print structured history")
    args=p.parse_args(argv)
    errors=validate()
    if errors:
        for e in errors:
            print("RELEASE HISTORY ERROR: "+e,file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"current_version":(ROOT/"VERSION").read_text().strip(),
                          "records":collect(),"production_verified":False},ensure_ascii=False,indent=2))
        return 0
    archive=ROOT/"docs/VERSION_ARCHIVE.md"
    expected=render()
    if args.check:
        if not archive.is_file() or archive.read_text(encoding="utf-8")!=expected:
            print("RELEASE HISTORY ERROR: regenerate docs/VERSION_ARCHIVE.md",file=sys.stderr)
            return 2
        print("Version archive matches CHANGELOG and VERSION.")
        return 0
    archive.write_text(expected,encoding="utf-8")
    print("Updated",archive)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
