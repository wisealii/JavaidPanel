"""Audit existing feature inventory without pretending that real VPS has been tested."""
import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audit_current_features",ROOT/"tools/audit-current-features.py")
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

class CurrentFeaturesAuditTests(unittest.TestCase):
    def test_all_declared_features_have_real_source_evidence(self):
        entries,errors=mod.audit(ROOT)
        self.assertEqual(errors,[])
        self.assertGreaterEqual(len(entries),18)
        self.assertTrue(all(not x["vps_verified"] for x in entries))

    def test_core_and_addon_not_confused(self):
        entries,_=mod.audit(ROOT)
        core=[x for x in entries if x["scope"]=="core"]
        addon=[x for x in entries if x["scope"]=="addon"]
        self.assertGreaterEqual(len(core),12)
        self.assertGreaterEqual(len(addon),5)
        self.assertTrue(any(x["name"]=="داشبورد خصوصی مدیریت نود" for x in addon))

    def test_report_command_succeeds(self):
        self.assertEqual(mod.main(["--json"]),0)

if __name__=="__main__":
    unittest.main()
