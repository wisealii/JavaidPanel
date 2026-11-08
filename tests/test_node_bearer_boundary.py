"""Regression tests for the existing standalone node-control admin bearer boundary.

These tests are offline and intentionally do not modify the API or create roles.
"""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from javid_panel.nodes.api import API


class AdminBearerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.token = "A" * 44
        self.api = API(None, self.token)

    def test_exact_admin_bearer_is_accepted(self):
        self.assertTrue(self.api.authenticated("Bearer " + self.token))

    def test_missing_or_modified_bearer_is_rejected(self):
        for header in (
            None,
            "",
            self.token,
            "bearer " + self.token,
            "Bearer",
            "Bearer ",
            "Bearer " + self.token + " ",
            "Bearer " + self.token + "extra",
            "Bearer " + self.token[:-1],
            "Basic " + self.token,
        ):
            with self.subTest(header=repr(header)):
                self.assertFalse(self.api.authenticated(header))

    def test_admin_token_minimum_length_remains_enforced(self):
        with self.assertRaises(ValueError):
            API(None, "x" * 31)


if __name__ == "__main__":
    unittest.main()
