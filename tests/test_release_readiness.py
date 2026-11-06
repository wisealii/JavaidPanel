"""Release readiness tests: do not assert production readiness."""
from __future__ import annotations
import hashlib
import importlib.util
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("release_readiness",ROOT/"tools/release-readiness.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

class ReadinessTests(unittest.TestCase):
    def test_metadata_and_pinned_engine_are_valid(self):
        checks={c.code:c for c in mod.run_checks(ROOT)}
        self.assertEqual(checks["release_metadata"].status,"pass")
        self.assertEqual(checks["pinned_engine"].status,"pass")
        self.assertEqual(checks["one_command_entrypoint"].status,"pass")

    def test_not_claiming_unverified_live_vps(self):
        checks={c.code:c for c in mod.run_checks(ROOT)}
        self.assertEqual(checks["real_vps_install"].status,"manual")
        self.assertEqual(checks["real_two_vps_node"].status,"manual")
        self.assertNotEqual(mod.main(["--strict"]),0)

    def test_flags_are_not_equivalent_to_production_certification(self):
        self.assertEqual(mod.main(["--json"]),0)
        self.assertNotEqual(mod.main(["--strict","--json"]),0)

    def test_changed_bootstrap_version_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)
            (p/"VERSION").write_text("7.2.1-dev\n")
            (p/"install.sh").write_text("VERSION=1.0.0-dev\n")
            checks={c.code:c for c in mod.run_checks(p)}
            self.assertEqual(checks["release_metadata"].status,"blocked")
        mod.ROOT=ROOT

    def test_alternative_production_compose_is_not_misrepresented(self):
        checks={c.code:c for c in mod.run_checks(ROOT)}
        self.assertEqual(checks["compose_production"].status,"pass")
        self.assertIn("No untested alternative",checks["compose_production"].message)

if __name__=="__main__":
    unittest.main()
