#!/usr/bin/env python3
"""Validate the JavaidPanel source-version catalog and release-note archive.

This is a local metadata gate, NOT verification that Git tags, GitHub Releases,
upstream binaries or live VPS installs exist.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+-dev$")
HEADING_PATTERN = re.compile(r"^## (\d+\.\d+\.\d+-dev)\b", re.M)


def check(root: pathlib.Path = ROOT) -> list[str]:
    problems = []
    def read(path: str) -> str:
        full = root / path
        if not full.is_file() or full.is_symlink():
            problems.append("Missing or unsafe file: " + path)
            return ""
        return full.read_text(encoding="utf-8")

    current = read("VERSION").strip()
    manifest_text = read("docs/versions.json")
    try:
        index = json.loads(manifest_text)
    except json.JSONDecodeError:
        return problems + ["Invalid JSON in docs/versions.json"]
    records = index.get("versions", [])
    if index.get("schema_version") != 1 or not isinstance(records, list) or not records:
        return problems + ["Unsupported or empty release catalog"]
    if index.get("current_version") != current:
        problems.append("Manifest current_version must equal VERSION")
    installer = read("install.sh")
    if not re.search(r"^VERSION=" + re.escape(current) + r"\s*$", installer, re.M):
        problems.append("Installer VERSION does not match VERSION")
    readme = read("README.md")
    if "version-" + current.replace("-", "--") not in readme or "**" + current + "**" not in readme:
        problems.append("README badge and displayed version must match VERSION")
    features = read("docs/CURRENT_FEATURES.json")
    try:
        feature_catalog = json.loads(features)
        if feature_catalog.get("version") != current:
            problems.append("CURRENT_FEATURES.json version mismatch")
    except json.JSONDecodeError:
        problems.append("Invalid CURRENT_FEATURES.json")
    changelog = read("CHANGELOG.md")
    read("docs/VERSIONS.md")
    read("docs/RELEASING.md")
    seen = set()
    ordered = []
    for record in records:
        if not isinstance(record, dict):
            problems.append("Invalid release record object")
            continue
        version = record.get("version", "")
        if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
            problems.append("Invalid version label: " + repr(version))
            continue
        if version in seen:
            problems.append("Duplicate archived version: " + version)
        seen.add(version)
        ordered.append(tuple(map(int, version[:-4].split("."))))
        if record.get("phase") != "dev":
            problems.append("Development archive cannot claim stable: " + version)
        if record.get("git_tag") is not None or record.get("github_release_published") is not False:
            problems.append("Unverified tag/release claimed: " + version)
        for field in ("features", "changes"):
            value = record.get(field)
            if not isinstance(value, list) or not value or not all(isinstance(x, str) and x.strip() for x in value):
                problems.append("Empty/invalid " + field + " for " + version)
        expected = "docs/releases/" + version + ".md"
        if record.get("archive") != expected:
            problems.append("Release archive path mismatch: " + version)
        notes = read(expected)
        if "# JavaidPanel " + version not in notes:
            problems.append("Release notes heading mismatch: " + version)
        for feature in record.get("features", []):
            if isinstance(feature, str) and feature not in notes:
                problems.append("Feature omitted from archive: " + version)
        if version not in read("docs/VERSIONS.md"):
            problems.append("Version missing from public index: " + version)
        if version not in HEADING_PATTERN.findall(changelog):
            problems.append("Version missing from CHANGELOG: " + version)
        validation = record.get("verification", {})
        if validation.get("live_vps_install") is not False:
            problems.append("VPS result must remain unverified until separately evidenced: " + version)
        prs = record.get("pr_numbers")
        if not isinstance(prs, list) or any(type(n) is not int or n <= 0 for n in prs):
            problems.append("Invalid PR references: " + version)
    if ordered != sorted(ordered):
        problems.append("Version archive is not sorted ascending")
    if records[-1].get("version") != current:
        problems.append("Last archived version must be current VERSION")
    if current not in HEADING_PATTERN.findall(changelog):
        problems.append("Current version missing from CHANGELOG")
    if "stable" in index.get("archive_policy", "").lower() and "not" not in index["archive_policy"].lower():
        problems.append("Misleading archive policy")
    archive_dir = root / "docs/releases"
    if archive_dir.is_dir():
        undeclared = sorted(path.name for path in archive_dir.glob("*.md")
                            if path.name[:-3] not in seen)
        if undeclared:
            problems.append("Unlisted release archives: " + ", ".join(undeclared))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="JavaidPanel version/feature archive consistency audit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    issues = check()
    if args.json:
        print(json.dumps({"valid": not issues, "errors": issues}, ensure_ascii=False, indent=2))
    else:
        if issues:
            for issue in issues:
                print("RELEASE ARCHIVE ERROR: " + issue, file=sys.stderr)
        else:
            print("OK: VERSION, README, installer, CHANGELOG, catalog, public index and release archives are consistent.")
            print("NOTE: This is metadata validation, not Git tag/Release/VPS verification.")
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
