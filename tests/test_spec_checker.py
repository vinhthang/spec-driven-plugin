#!/usr/bin/env python3
"""Unit tests for shared specification checker (REQ-001, REQ-002, REQ-003, REQ-006, REQ-008)."""

import json
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

    def _create_valid_package(self, pkg_dir: Path, req_ids=("REQ-001", "REQ-002")):
        pkg_dir.mkdir(parents=True, exist_ok=True)
        req_lines = "\n".join(f"- {r}: Description for {r}" for r in req_ids)
        (pkg_dir / "spec.md").write_text(f"# Spec\n\n{req_lines}\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR-001: Architecture decision\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text(f"# Design\nAddresses: {', '.join(req_ids)}\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text(f"# Tasks\n" + "\n".join(f"- [ ] Task for {r}" for r in req_ids) + "\n", encoding="utf-8")

    def test_normalize_status(self):
        """Test status normalization across case, whitespace, hyphens, and underscores."""
        self.assertEqual(spec_checker.normalize_status("In Progress"), "in-progress")
        self.assertEqual(spec_checker.normalize_status("Approved "), "approved")
        self.assertEqual(spec_checker.normalize_status("  DRAFT  "), "draft")
        self.assertEqual(spec_checker.normalize_status("in_progress"), "in-progress")
        self.assertEqual(spec_checker.normalize_status("PLANNING"), "planning")

    def test_extract_requirement_ids(self):
        """Test requirement ID extraction excludes placeholders like REQ-xxx/REQ-XXX."""
        text = "Normative: REQ-001, REQ-002, FLOW-010, ALIGN-100, and placeholder REQ-xxx and REQ-XXX."
        reqs = spec_checker.extract_requirement_ids(text)
        self.assertEqual(reqs, ["ALIGN-100", "FLOW-010", "REQ-001", "REQ-002"])
        self.assertNotIn("REQ-xxx", reqs)
        self.assertNotIn("REQ-XXX", reqs)

    def test_parse_specs_index_escaped_pipes(self):
        """Test parsing markdown table in INDEX.md with escaped pipes in cell content."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n"
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature One | Planning | `REQ-001` | ADR-01 \\| ADR-02 | `./feat-1/spec.md` |\n"
            "| `feat-2` | Feature Two | Completed | `REQ-011` | None | [Spec](./feat-2/spec.md) |\n",
            encoding="utf-8",
        )

        records = spec_checker.parse_specs_index(index_file)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["feature_id"], "feat-1")
        self.assertEqual(records[0]["status"], "Planning")
        self.assertEqual(records[0]["key_decisions"], "ADR-01 | ADR-02")
        self.assertEqual(records[0]["spec_path"], "./feat-1/spec.md")

    def test_validate_spec_package_4_docs_non_whitespace(self):
        """Test 4 core documents required and non-whitespace check."""
        pkg = self.workspace / "pkg"
        pkg.mkdir()

        # Missing files
        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("Missing required specification file", err)

        # Create files but leave tasks.md whitespace-only
        (pkg / "spec.md").write_text("# Spec\nREQ-001: Details\n", encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nADR-001: Rationale\n", encoding="utf-8")
        (pkg / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("   \n\t  \n", encoding="utf-8")

        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("Specification file is empty: tasks.md", err)

    def test_validate_spec_package_traceability_failures(self):
        """Test failure when spec requirements are unmapped in design, tasks, or decisions."""
        pkg = self.workspace / "pkg"
        pkg.mkdir()

        (pkg / "spec.md").write_text("# Spec\n- REQ-001: A\n- REQ-002: B\n", encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nADR-001: Note\n", encoding="utf-8")
        # Missing REQ-002 in design.md
        (pkg / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n- [ ] Task REQ-002\n", encoding="utf-8")

        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("design.md is missing requirement IDs declared in spec.md: REQ-002", err)

        # Fix design.md, break tasks.md
        (pkg / "design.md").write_text("# Design\nAddresses REQ-001, REQ-002\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n", encoding="utf-8")
        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("tasks.md is missing requirement IDs declared in spec.md: REQ-002", err)

        # Fix tasks.md, break decisions.md (no ADR and no REQ)
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n- [ ] Task REQ-002\n", encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nPlain text without decision records\n", encoding="utf-8")
        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("decisions.md must contain at least one ADR-", err)

    def test_validate_spec_package_verify_evidence(self):
        """Test verification.md requirement when verify_evidence is True."""
        pkg = self.workspace / "pkg"
        self._create_valid_package(pkg, ("REQ-001", "REQ-002"))

        # Without verify_evidence -> passes
        valid, err = spec_checker.validate_spec_package(pkg, verify_evidence=False)
        self.assertTrue(valid)

        # With verify_evidence -> missing verification.md
        valid, err = spec_checker.validate_spec_package(pkg, verify_evidence=True)
        self.assertFalse(valid)
        self.assertIn("Missing required specification file: verification.md", err)

        # Create verification.md missing REQ-002
        (pkg / "verification.md").write_text("# Evidence\nVerified: REQ-001\n", encoding="utf-8")
        valid, err = spec_checker.validate_spec_package(pkg, verify_evidence=True)
        self.assertFalse(valid)
        self.assertIn("verification.md is missing requirement IDs declared in spec.md: REQ-002", err)

        # Complete verification.md
        (pkg / "verification.md").write_text("# Evidence\nVerified: REQ-001\nVerified: REQ-002\n", encoding="utf-8")
        valid, err = spec_checker.validate_spec_package(pkg, verify_evidence=True)
        self.assertTrue(valid)

    def test_verify_active_specification_path_traversal_guards(self):
        """Test path traversal rejection in feature_id and candidate directories."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        # feature_id with ..
        res = spec_checker.verify_active_specification(self.workspace, feature_id="../escape")
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "invalid_path")

        # In INDEX.md, a spec_path escaping root
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-bad` | Bad | Approved | `REQ-001` | ADR-001 | `../../outside/spec.md` |\n",
            encoding="utf-8",
        )
        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "invalid_path")

    def test_verify_active_specification_unapproved_rejection_and_planning_allowance(self):
        """Test that unapproved specifications are rejected by default but permitted with require_approved=False."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg_dir = specs_dir / "feat-plan"
        self._create_valid_package(pkg_dir)

        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-plan` | Planning Feature | Planning | `REQ-001` | ADR-001 | `./feat-plan/spec.md` |\n",
            encoding="utf-8",
        )

        # Default (require_approved=True) -> unapproved_spec
        res = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "unapproved_spec")

        # With require_approved=False -> valid
        res_allow = spec_checker.verify_active_specification(self.workspace, require_approved=False)
        self.assertTrue(res_allow["valid"])
        self.assertEqual(res_allow["status"], "valid")

    def test_verify_active_specification_feature_targeting(self):
        """Test targeting a specific feature ID."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg1 = specs_dir / "feat-1"
        self._create_valid_package(pkg1)

        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Approved | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n"
            "| `feat-2` | Feature 2 | Planning | `REQ-002` | ADR-002 | `./feat-2/spec.md` |\n",
            encoding="utf-8",
        )

        # Targeting feat-1 passes
        res1 = spec_checker.verify_active_specification(self.workspace, feature_id="feat-1")
        self.assertTrue(res1["valid"])
        self.assertEqual(res1["active_features"], ["feat-1"])

        # Targeting non-existent feature fails
        res_none = spec_checker.verify_active_specification(self.workspace, feature_id="feat-none")
        self.assertFalse(res_none["valid"])
        self.assertEqual(res_none["status"], "feature_not_found")

    def test_verify_active_specification_multi_feature_isolation(self):
        """Test that an incomplete draft spec does not block execution of a valid approved spec."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg_good = specs_dir / "feat-good"
        self._create_valid_package(pkg_good)

        # Incomplete draft spec (directory doesn't exist)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-good` | Good Feature | Approved | `REQ-001` | ADR-001 | `./feat-good/spec.md` |\n"
            "| `feat-draft` | Draft Feature | Draft | `REQ-002` | ADR-002 | `./feat-draft/spec.md` |\n",
            encoding="utf-8",
        )

        res = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertTrue(res["valid"])
        self.assertEqual(res["active_features"], ["feat-good"])

    def test_cli_main_exit_codes(self):
        """Test CLI main exit codes (0 for valid, 1 for invalid, 2 for corrupt/error)."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg = specs_dir / "feat-1"
        self._create_valid_package(pkg)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Approved | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )

        code_valid = spec_checker.main(["--workspace", str(self.workspace), "--json"])
        self.assertEqual(code_valid, 0)

        # Unapproved -> exit 1
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )
        code_unapproved = spec_checker.main(["--workspace", str(self.workspace), "--json"])
        self.assertEqual(code_unapproved, 1)

        # Allow planning -> exit 0
        code_plan = spec_checker.main(["--workspace", str(self.workspace), "--allow-planning", "--json"])
        self.assertEqual(code_plan, 0)

    def test_parse_specs_index_malformed_row_raises(self):
        """Test that a row with <6 columns raises ValueError and triggers corrupt_index status."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n"
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Incomplete columns |\n",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError) as ctx:
            spec_checker.parse_specs_index(index_file)
        self.assertIn("Malformed table row", str(ctx.exception))
        self.assertIn("expected 6 columns", str(ctx.exception))

        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "corrupt_index")
        self.assertIn("Malformed table row", res["reason"])

    def test_verify_active_specification_broken_approved_spec_not_swallowed(self):
        """Test that if two approved specs exist and one is broken, verify_active_specification returns valid: False."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg_good = specs_dir / "feat-good"
        self._create_valid_package(pkg_good)

        # feat-broken directory does not exist
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-good` | Good Feature | Approved | `REQ-001` | ADR-001 | `./feat-good/spec.md` |\n"
            "| `feat-broken` | Broken Feature | Approved | `REQ-002` | ADR-002 | `./feat-broken/spec.md` |\n",
            encoding="utf-8",
        )

        res = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "incomplete_package")
        self.assertEqual(res.get("feature_id"), "feat-broken")


if __name__ == "__main__":
    unittest.main()
