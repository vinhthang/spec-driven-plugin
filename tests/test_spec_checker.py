#!/usr/bin/env python3
"""Unit tests for shared specification checker (REQ-032)."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import spec_checker


class TestSpecChecker(unittest.TestCase):
    """Test suite for spec_checker.py."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_specs_index_valid(self):
        """Test parsing valid markdown table in INDEX.md."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n"
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature One | Planning | `REQ-001` - `REQ-010` | ADR-01 | `./feat-1/spec.md` |\n"
            "| `feat-2` | Feature Two | Completed | `REQ-011` | ADR-02 | [Spec](./feat-2/spec.md) |\n",
            encoding="utf-8",
        )

        records = spec_checker.parse_specs_index(index_file)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["feature_id"], "feat-1")
        self.assertEqual(records[0]["status"], "Planning")
        self.assertEqual(records[0]["spec_path"], "./feat-1/spec.md")
        self.assertEqual(records[1]["feature_id"], "feat-2")
        self.assertEqual(records[1]["status"], "Completed")
        self.assertEqual(records[1]["spec_path"], "./feat-2/spec.md")

    def test_parse_specs_index_file_not_found(self):
        """Test FileNotFoundError when index file does not exist."""
        non_existent = self.workspace / "missing" / "INDEX.md"
        with self.assertRaises(FileNotFoundError):
            spec_checker.parse_specs_index(non_existent)

    def test_verify_active_specification_no_framework(self):
        """Test workspace without docs/specs directory."""
        res = spec_checker.verify_active_specification(self.workspace)
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "no_spec_framework")

    def test_verify_active_specification_missing_index(self):
        """Test workspace with docs/specs but missing INDEX.md."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "invalid")
        self.assertIn("Missing docs/specs/INDEX.md", res["reason"])

    def test_verify_active_specification_no_active_spec(self):
        """Test INDEX.md with only completed specifications."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-done` | Completed Feature | Completed | `REQ-001` | ADR | `./feat-done/spec.md` |\n",
            encoding="utf-8",
        )
        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "no_active_spec")

    def test_verify_active_specification_valid_package(self):
        """Test workspace with valid active spec and complete package."""
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "feat-active"
        pkg_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-active` | Active Feature | Planning | `REQ-001` | ADR | `./feat-active/spec.md` |\n",
            encoding="utf-8",
        )
        (pkg_dir / "spec.md").write_text("# Spec\n\nREQ-001: Description\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR content\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text("# Design\nDesign details\n", encoding="utf-8")

        res = spec_checker.verify_active_specification(self.workspace)
        self.assertTrue(res["valid"])
        self.assertEqual(res["status"], "valid")
        self.assertIn("feat-active", res["active_features"])

    def test_verify_active_specification_incomplete_package(self):
        """Test workspace with active spec but missing required files."""
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "feat-active"
        pkg_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-active` | Active Feature | Planning | `REQ-001` | ADR | `./feat-active/spec.md` |\n",
            encoding="utf-8",
        )
        (pkg_dir / "spec.md").write_text("# Spec\n\nREQ-001: Description\n", encoding="utf-8")
        # Missing decisions.md and design.md

        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "incomplete_package")


if __name__ == "__main__":
    unittest.main()
