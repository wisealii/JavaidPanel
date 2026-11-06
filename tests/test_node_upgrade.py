"""Safe upgrade regression tests: all file operations in isolated temp dirs."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("upgrade_control_plane", ROOT / "tools" / "upgrade-control-plane.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
UpgradeError = module.UpgradeError
audit_source = module.audit_source
upgrade = module.upgrade
validate_install = module.validate_install
main = module.main


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "checkout" / "src"
        self.target = self.root / "deployment" / "src"
        shutil.copytree(ROOT / "src", self.source)
        self.target.parent.mkdir()
        shutil.copytree(ROOT / "src", self.target)
        self.old_api = self.target / "javid_panel/nodes/api.py"
        self.old_api.write_text("# OLD deployment\n")
        self.config = self.root / "private" / "node-control.json"
        self.config.parent.mkdir(mode=0o700)
        self.config.write_text('{"database":"private-db","admin_token":"keep-me"}')
        self.config.chmod(0o600)
        self.unit = self.root / "javid-node-control.service"
        self.unit.write_text(
            "[Service]\nEnvironment=PYTHONPATH=" + str(self.target) +
            "\nExecStart=python3 -m javid_panel.nodes.api serve --host 127.0.0.1\n"
        )

    def test_read_only_plan(self):
        digest = hashlib.sha256(self.config.read_bytes()).digest()
        before = self.old_api.read_text()
        self.assertEqual(main(["--plan", "--source", str(self.source), "--target", str(self.target),
                               "--config", str(self.config), "--unit", str(self.unit)]), 0)
        self.assertEqual(before, self.old_api.read_text())
        self.assertEqual(digest, hashlib.sha256(self.config.read_bytes()).digest())

    def test_success_preserves_config_and_keeps_backup(self):
        old = self.old_api.read_bytes()
        checksum = hashlib.sha256(self.config.read_bytes()).hexdigest()
        calls = []
        def restart():
            calls.append("restart")
            return True
        backup = upgrade(self.source, self.target, self.config, self.unit,
                         restart=restart, healthy=lambda: True)
        self.assertTrue(backup.is_dir())
        self.assertEqual((backup / "javid_panel/nodes/api.py").read_bytes(), old)
        self.assertNotEqual(self.old_api.read_bytes(), old)
        self.assertEqual(hashlib.sha256(self.config.read_bytes()).hexdigest(), checksum)
        self.assertEqual(len(calls), 1)

    def test_restart_failure_rolls_back(self):
        old = self.old_api.read_bytes()
        calls = []
        def restart():
            calls.append(1)
            return len(calls) > 1
        with self.assertRaisesRegex(UpgradeError, "restored"):
            upgrade(self.source, self.target, self.config, self.unit,
                    restart=restart, healthy=lambda: True)
        self.assertEqual(self.old_api.read_bytes(), old)
        self.assertEqual(len(calls), 2)
        self.assertTrue(list(self.target.parent.glob("src.failed-*")))

    def test_new_health_failure_rolls_back(self):
        old = self.old_api.read_bytes()
        checks = [True] + [False] * 8 + [True]
        def healthy():
            return checks.pop(0)
        with self.assertRaisesRegex(UpgradeError, "restored"):
            upgrade(self.source, self.target, self.config, self.unit,
                    restart=lambda: True, healthy=healthy)
        self.assertEqual(self.old_api.read_bytes(), old)

    def test_unhealthy_old_service_blocks_mutation(self):
        before = self.old_api.read_bytes()
        with self.assertRaisesRegex(UpgradeError, "not healthy"):
            upgrade(self.source, self.target, self.config, self.unit,
                    restart=lambda: True, healthy=lambda: False)
        self.assertEqual(self.old_api.read_bytes(), before)

    def test_config_permissions_and_symlinks_rejected(self):
        self.config.chmod(0o644)
        with self.assertRaises(UpgradeError):
            validate_install(self.target, self.config, self.unit)
        self.config.chmod(0o600)
        (self.source / "javid_panel/nodes/link.py").symlink_to("/etc/passwd")
        with self.assertRaises(UpgradeError):
            audit_source(self.source)

    def test_missing_source_fails_before_mutation(self):
        (self.source / "javid_panel/nodes/dashboard.js").unlink()
        with self.assertRaises(UpgradeError):
            audit_source(self.source)
        self.assertEqual(self.old_api.read_text(), "# OLD deployment\n")


if __name__ == "__main__":
    unittest.main()
