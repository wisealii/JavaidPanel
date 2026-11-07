"""Version archive metadata and historical provenance regression checks."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_version_archive", ROOT / "tools/verify-version-archive.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class VersionArchiveTests(unittest.TestCase):
    def test_archive_and_installer_are_consistent(self):
        self.assertEqual(module.check(ROOT), [])

    def test_historical_metadata_never_invents_releases(self):
        manifest = json.loads((ROOT / "docs/versions.json").read_text())
        self.assertGreaterEqual(len(manifest["versions"]), 11)
        for version in manifest["versions"]:
            self.assertIsNone(version["git_tag"])
            self.assertFalse(version["github_release_published"])
            self.assertFalse(version["verification"]["live_vps_install"])

    def test_version_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for path in ["VERSION", "install.sh", "README.md", "CHANGELOG.md",
                         "docs/versions.json", "docs/VERSIONS.md",
                         "docs/RELEASING.md", "docs/CURRENT_FEATURES.json"]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            shutil.copytree(ROOT / "docs/releases", root / "docs/releases")
            (root / "VERSION").write_text("9.9.999-dev\n")
            errors = module.check(root)
            self.assertTrue(any("Manifest current_version" in e for e in errors))
            self.assertTrue(any("Installer VERSION" in e for e in errors))

    def test_archive_file_missing_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            for path in ["VERSION", "install.sh", "README.md", "CHANGELOG.md",
                         "docs/versions.json", "docs/VERSIONS.md",
                         "docs/RELEASING.md", "docs/CURRENT_FEATURES.json"]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, target)
            shutil.copytree(ROOT / "docs/releases", root / "docs/releases")
            (root / "docs/releases/1.1.111-dev.md").unlink()
            self.assertTrue(any("Missing or unsafe file" in e for e in module.check(root)))


if __name__ == "__main__":
    unittest.main()
