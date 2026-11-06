"""Offline regression tests for the JavaidPanel pinned bootstrap.

These tests never attempt to install packages, modify services, or access GitHub.
"""
from __future__ import annotations
import hashlib
import pathlib
import re
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "install.sh"
CORE = ROOT / "installer" / "core.sh"
NODE_SCRIPT = ROOT / "node-agent-install.sh"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args], cwd=ROOT,
        capture_output=True, text=True, timeout=25,
    )


class BootstrapTests(unittest.TestCase):
    def test_shell_syntax(self) -> None:
        for path in (SCRIPT, CORE, NODE_SCRIPT):
            with self.subTest(path=path.name):
                result = subprocess.run(["bash", "-n", str(path)],
                                        capture_output=True, text=True, timeout=12)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_exact_pinned_sha256(self) -> None:
        source = SCRIPT.read_text()
        match = re.search(r'^CORE_SHA256="([0-9a-f]{64})"$', source, re.M)
        self.assertIsNotNone(match)
        actual = hashlib.sha256(CORE.read_bytes()).hexdigest()
        self.assertEqual(match.group(1), actual)

    def test_help_is_read_only(self) -> None:
        p = run("--help")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("one-command", p.stdout)
        self.assertIn("--self-test", p.stdout)

    def test_doctor_is_read_only(self) -> None:
        p = run("--doctor")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Architecture:", p.stdout)
        self.assertIn("Physical RAM:", p.stdout)
        self.assertIn("Free disk under /opt:", p.stdout)

    def test_rejects_extra_arguments(self) -> None:
        p = run("--doctor", "unexpected")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Only one command flag", p.stderr)

    def test_rejects_unknown_mode(self) -> None:
        p = run("--this-should-not-exist")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Unknown option", p.stderr)

    def test_core_embedded_code_compiles(self) -> None:
        p = run("--self-test")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("No installation performed.", p.stdout)

    def test_node_check_no_install(self) -> None:
        p = subprocess.run(["bash", str(NODE_SCRIPT), "--check"],
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("NOT INCLUDED", p.stdout)

    def test_no_placeholder_services_in_core(self) -> None:
        core = CORE.read_text()
        self.assertNotIn("sleep infinity", core)
        self.assertIn("alirezapanel-vpn.service", core)


if __name__ == "__main__":
    unittest.main()
