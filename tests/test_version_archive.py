"""Release archive source-of-truth and anti-fabrication regression tests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("version_archive",ROOT/"tools/version-archive.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ArchiveTests(unittest.TestCase):
    def test_current_changelog_matches_version(self):
        self.assertEqual(mod.validate(ROOT),[])

    def test_archive_is_generated_from_changelog(self):
        self.assertEqual((ROOT/"docs/VERSION_ARCHIVE.md").read_text(),mod.render(ROOT))

    def test_history_does_not_claim_github_releases(self):
        items=mod.collect(ROOT)
        self.assertGreaterEqual(len(items),7)
        self.assertTrue(all(x["kind"]=="development_history" for x in items))
        self.assertTrue(all(x["github_release_verified"] is False for x in items))
        self.assertTrue(all(x["git_tag_verified"] is False for x in items))

    def test_duplicate_historical_version_is_preserved_not_invented(self):
        items=mod.collect(ROOT)
        duplicates=[x for x in items if x["version"]=="1.1.108-dev"]
        self.assertGreaterEqual(len(duplicates),2)

    def test_bad_version_and_missing_notes_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"VERSION").write_text("1.2.0-dev\n")
            (root/"CHANGELOG.md").write_text("## 1.2.0-dev — Empty\n")
            self.assertTrue(mod.validate(root))
            (root/"CHANGELOG.md").write_text("## 1.2.0-dev — Real\n- Added tested archive.\n")
            self.assertEqual(mod.validate(root),[])

if __name__=="__main__":
    unittest.main()
