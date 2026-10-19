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

INDEX_HEADER = (
    "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
    "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
)

class TestSpecChecker(unittest.TestCase):
    """Test suite for spec_checker.py."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_valid_package(self, pkg_dir: Path, req_ids=("REQ-001", "REQ-002")):
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n\n" + "\n".join(f"- {r}: Descr" for r in req_ids) + "\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR-001: Architecture decision\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text(f"# Design\nAddresses: {', '.join(req_ids)}\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n" + "\n".join(f"- [ ] {r}" for r in req_ids) + "\n", encoding="utf-8")

    def test_normalize_status(self):
        """Test status normalization across case, whitespace, hyphens, and underscores."""
        cases = [("In Progress", "in-progress"), ("Approved ", "approved"), ("  DRAFT  ", "draft"), ("in_progress", "in-progress"), ("PLANNING", "planning")]
        for raw, expected in cases:
            self.assertEqual(spec_checker.normalize_status(raw), expected)

    def test_extract_requirement_ids(self):
        """Test requirement ID extraction excludes placeholders like REQ-xxx/REQ-XXX."""
        reqs = spec_checker.extract_requirement_ids("Normative: REQ-001, REQ-002, FLOW-010, ALIGN-100, and placeholder REQ-xxx and REQ-XXX.")
        self.assertEqual(reqs, ["ALIGN-100", "FLOW-010", "REQ-001", "REQ-002"])
        self.assertNotIn("REQ-xxx", reqs)
        self.assertNotIn("REQ-XXX", reqs)

    def test_parse_specs_index_escaped_pipes(self):
        """Test parsing markdown table in INDEX.md with escaped pipes in cell content."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n" +
            INDEX_HEADER + "| `feat-1` | Feature One | Planning | `REQ-001` | ADR-01 \\| ADR-02 | `./feat-1/spec.md` |\n"
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
        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("Missing required specification file", err)

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
        (pkg / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n- [ ] Task REQ-002\n", encoding="utf-8")
        self.assertIn("design.md is missing", spec_checker.validate_spec_package(pkg)[1])

        (pkg / "design.md").write_text("# Design\nAddresses REQ-001, REQ-002\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n", encoding="utf-8")
        self.assertIn("tasks.md is missing", spec_checker.validate_spec_package(pkg)[1])

        (pkg / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n- [ ] Task REQ-002\n", encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nPlain text without decision records\n", encoding="utf-8")
        self.assertIn("decisions.md must contain at least one ADR-", spec_checker.validate_spec_package(pkg)[1])

    def test_validate_spec_package_verify_evidence(self):
        """Test verification.md requirement when verify_evidence is True."""
        pkg = self.workspace / "pkg"
        self._create_valid_package(pkg, ("REQ-001", "REQ-002"))
        self.assertTrue(spec_checker.validate_spec_package(pkg, verify_evidence=False)[0])
        self.assertIn("Missing required specification file: verification.md", spec_checker.validate_spec_package(pkg, verify_evidence=True)[1])

        (pkg / "verification.md").write_text("# Evidence\nVerified: REQ-001\n", encoding="utf-8")
        self.assertIn("verification.md is missing requirement IDs", spec_checker.validate_spec_package(pkg, verify_evidence=True)[1])

        (pkg / "verification.md").write_text("# Evidence\nVerified: REQ-001\nVerified: REQ-002\n", encoding="utf-8")
        self.assertTrue(spec_checker.validate_spec_package(pkg, verify_evidence=True)[0])

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
            INDEX_HEADER + "| `feat-bad` | Bad | Approved | `REQ-001` | ADR-001 | `../../outside/spec.md` |\n",
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
            INDEX_HEADER + "| `feat-plan` | Planning Feature | Planning | `REQ-001` | ADR-001 | `./feat-plan/spec.md` |\n",
            encoding="utf-8",
        )

        res = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "unapproved_spec")

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
            INDEX_HEADER + "| `feat-1` | Feature 1 | Approved | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n"
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
            INDEX_HEADER + "| `feat-good` | Good Feature | Approved | `REQ-001` | ADR-001 | `./feat-good/spec.md` |\n"
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
        (specs_dir / "INDEX.md").write_text(INDEX_HEADER + "| `feat-1` | Feature 1 | Approved | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n", encoding="utf-8")
        self.assertEqual(spec_checker.main(["--workspace", str(self.workspace), "--json"]), 0)

        (specs_dir / "INDEX.md").write_text(INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n", encoding="utf-8")
        self.assertEqual(spec_checker.main(["--workspace", str(self.workspace), "--json"]), 1)
        self.assertEqual(spec_checker.main(["--workspace", str(self.workspace), "--allow-planning", "--json"]), 0)

    def test_parse_specs_index_malformed_row_raises(self):
        """Test that a row with <6 columns raises ValueError and triggers corrupt_index status."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n" +
            INDEX_HEADER + "| `feat-1` | Incomplete columns |\n",
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
            INDEX_HEADER + "| `feat-good` | Good Feature | Approved | `REQ-001` | ADR-001 | `./feat-good/spec.md` |\n"
            "| `feat-broken` | Broken Feature | Approved | `REQ-002` | ADR-002 | `./feat-broken/spec.md` |\n",
            encoding="utf-8",
        )

        res = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "incomplete_package")
        self.assertEqual(res.get("feature_id"), "feat-broken")

    def test_declared_requirement_ids_ignores_prose_mentions(self):
        """Test that extract_declared_requirement_ids ignores prose mentions and only captures declarations."""
        spec_text = (
            "# Spec Title\n\n"
            "In previous iterations, we worked on REQ-099 and FLOW-999 in legacy services.\n\n"
            "### REQ-001: First Core Requirement\n"
            "System must do X.\n\n"
            "- **REQ-002**: Second Core Requirement\n"
            "- Note: this interacts with REQ-088 in prose.\n\n"
            "| Requirement ID | Description |\n"
            "| `ALIGN-003` | Third Core Requirement |\n"
        )
        declared = spec_checker.extract_declared_requirement_ids(spec_text)
        self.assertEqual(declared, ["ALIGN-003", "REQ-001", "REQ-002"])
        for p in ("REQ-099", "FLOW-999", "REQ-088"):
            self.assertNotIn(p, declared)

        # Test validation of package where spec.md has prose mentions:
        pkg = self.workspace / "pkg-prose"
        pkg.mkdir()
        (pkg / "spec.md").write_text(spec_text, encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nADR-001: Architecture decision\n", encoding="utf-8")
        (pkg / "design.md").write_text("# Design\nAddresses: ALIGN-003, REQ-001, REQ-002\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] ALIGN-003\n- [ ] REQ-001\n- [ ] REQ-002\n", encoding="utf-8")

        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertTrue(valid, f"Validation failed with: {err}")

    def test_governing_spec_link_does_not_bypass_design_traceability(self):
        """Governing Specification link in design.md must NOT bypass requirement ID traceability."""
        pkg = self.workspace / "pkg-gov"
        pkg.mkdir()
        (pkg / "spec.md").write_text("# Spec\n### REQ-001: Statement\n", encoding="utf-8")
        (pkg / "decisions.md").write_text("# Decisions\nADR-001: Decision\n", encoding="utf-8")
        (pkg / "design.md").write_text("# Design\nGoverning Specification: spec.md\nNo requirement IDs here.\n", encoding="utf-8")
        (pkg / "tasks.md").write_text("# Tasks\n- [ ] REQ-001\n", encoding="utf-8")

        valid, err = spec_checker.validate_spec_package(pkg)
        self.assertFalse(valid)
        self.assertIn("design.md is missing requirement IDs declared in spec.md: REQ-001", err)

    def test_parse_specs_index_extra_columns_raises(self):
        """Table row with more than 6 columns raises ValueError and results in corrupt_index."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "# Feature Specifications\n\n"
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path | Extra Col |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature One | Planning | `REQ-001` | ADR-01 | `./feat-1/spec.md` | Spurious |\n",
            encoding="utf-8",
        )

        with self.assertRaises(ValueError) as ctx:
            spec_checker.parse_specs_index(index_file)
        self.assertIn("Malformed table row", str(ctx.exception))
        self.assertIn("expected 6 columns, got 7", str(ctx.exception))

        res = spec_checker.verify_active_specification(self.workspace)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "corrupt_index")

    def test_verify_terminal_implemented_spec_with_feature_and_verify_evidence(self):
        """Terminal Implemented/Completed specs pass with --feature or --verify-evidence."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        pkg_done = specs_dir / "feat-done"
        self._create_valid_package(pkg_done, req_ids=("REQ-001",))
        (pkg_done / "verification.md").write_text("# Verification\nEvidence for REQ-001: PASSED\n", encoding="utf-8")
        (specs_dir / "INDEX.md").write_text(INDEX_HEADER + "| `feat-done` | Done | Implemented | `REQ-001` | ADR-001 | `./feat-done/spec.md` |\n", encoding="utf-8")

        res1 = spec_checker.verify_active_specification(self.workspace, require_approved=True)
        self.assertFalse(res1["valid"])
        self.assertEqual(res1["status"], "no_active_spec")

        res2 = spec_checker.verify_active_specification(self.workspace, feature_id="feat-done")
        self.assertTrue(res2["valid"])
        self.assertEqual(res2["status"], "valid")

        res3 = spec_checker.verify_active_specification(self.workspace, verify_evidence=True)
        self.assertTrue(res3["valid"])

        (pkg_done / "verification.md").unlink()
        res4 = spec_checker.verify_active_specification(self.workspace, feature_id="feat-done")
        self.assertFalse(res4["valid"])
        self.assertEqual(res4["status"], "incomplete_package")

    def test_parse_specs_index_text(self):
        """Test parse_specs_index_text parses 6-column markdown table and raises ValueError on malformed rows."""
        table_text = (
            INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 \\| ADR-002 | `./feat-1/spec.md` |\n"
            "| `feat-2` | Feature 2 | Approved | `REQ-002` | None | [Spec](./feat-2/spec.md) |\n"
        )
        records = spec_checker.parse_specs_index_text(table_text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["feature_id"], "feat-1")
        self.assertEqual(records[0]["title"], "Feature 1")
        self.assertEqual(records[0]["status"], "Planning")
        self.assertEqual(records[0]["key_decisions"], "ADR-001 | ADR-002")
        self.assertEqual(records[0]["spec_path"], "./feat-1/spec.md")
        self.assertEqual(records[1]["feature_id"], "feat-2")
        self.assertEqual(records[1]["status"], "Approved")
        self.assertEqual(records[1]["spec_path"], "./feat-2/spec.md")

        # Malformed row with 5 columns raises ValueError
        malformed = (
            INDEX_HEADER + "| `feat-bad` | Bad Row | Planning | `REQ-001` | `./feat-bad/spec.md` |\n"
        )
        with self.assertRaises(ValueError) as ctx:
            spec_checker.parse_specs_index_text(malformed)
        self.assertIn("expected 6 columns, got 5", str(ctx.exception))

    def test_resolve_package_dir(self):
        """Test resolve_package_dir resolves valid package directories and enforces workspace containment."""
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "my-feature"
        pkg_dir.mkdir(parents=True)

        spec = {"feature_id": "my-feature", "spec_path": "./my-feature/spec.md"}
        # 1. Valid resolution via dict spec with explicit specs_dir
        resolved, err = spec_checker.resolve_package_dir(spec, self.workspace, specs_dir)
        self.assertIsNone(err)
        self.assertEqual(resolved, pkg_dir.resolve())

        # 2. Valid resolution via dict spec with default specs_dir
        resolved2, err2 = spec_checker.resolve_package_dir(spec, self.workspace)
        self.assertIsNone(err2)
        self.assertEqual(resolved2, pkg_dir.resolve())

        # 3. Invalid characters in feature_id
        res_inv, err_inv = spec_checker.resolve_package_dir({"feature_id": "../escaped", "spec_path": "./escaped/spec.md"}, self.workspace, specs_dir)
        self.assertIsNone(res_inv)
        self.assertTrue(err_inv.startswith("invalid_path:") and "invalid path characters" in err_inv)

        # 4. Escaping workspace root via spec_path
        res_esc, err_esc = spec_checker.resolve_package_dir({"feature_id": "my-feature", "spec_path": "../../../outside/spec.md"}, self.workspace, specs_dir)
        self.assertIsNone(res_esc)
        self.assertTrue(err_esc.startswith("invalid_path:") and "escapes workspace root" in err_esc)

        # 5. Missing package directory
        res_miss, err_miss = spec_checker.resolve_package_dir({"feature_id": "nonexistent-feat", "spec_path": "./nonexistent-feat/spec.md"}, self.workspace, specs_dir)
        self.assertIsNone(res_miss)
        self.assertTrue(err_miss.startswith("missing_dir:") and "not found" in err_miss)

    def test_compute_spec_package_hash(self):
        """Test compute_spec_package_hash deterministic hashing."""
        pkg = self.workspace / "pkg-hash"
        self._create_valid_package(pkg, ("REQ-001",))
        h1 = spec_checker.compute_spec_package_hash(pkg, include_verification=False)
        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, spec_checker.compute_spec_package_hash(pkg, include_verification=False))
        (pkg / "verification.md").write_text("# Verif\n- REQ-001 passed\n", encoding="utf-8")
        self.assertNotEqual(h1, spec_checker.compute_spec_package_hash(pkg, include_verification=True))

    def test_validate_semantic_traceability_receipt(self):
        """Test validate_semantic_traceability with valid, flash, stale, and invalid receipts."""
        pkg = self.workspace / "pkg-sem"
        self._create_valid_package(pkg, ("REQ-001",))
        spec_hash = spec_checker.compute_spec_package_hash(pkg, include_verification=False)

        self.assertFalse(spec_checker.validate_semantic_traceability(pkg)[0])
        audit_file = pkg / "traceability_audit.json"
        audit = {
            "spec_hash": spec_hash, "auditor_model": "gemini-2.5-flash", "verdict": "PASS",
            "requirements_evaluated": {"REQ-001": {"design_aligned": True, "design_rationale": "ok", "tasks_actionable": True, "tasks_rationale": "ok", "decisions_consistent": True}}
        }
        audit_file.write_text(json.dumps(audit), encoding="utf-8")
        ok, err = spec_checker.validate_semantic_traceability(pkg)
        self.assertFalse(ok)
        self.assertIn("not flash", err)

        audit["auditor_model"] = "claude-opus-4-6"
        audit_file.write_text(json.dumps(audit), encoding="utf-8")
        self.assertTrue(spec_checker.validate_semantic_traceability(pkg)[0])

        audit["spec_hash"] = "0" * 64
        audit_file.write_text(json.dumps(audit), encoding="utf-8")
        ok, err = spec_checker.validate_semantic_traceability(pkg)
        self.assertFalse(ok)
        self.assertIn("spec_hash does not match", err)

        audit["spec_hash"] = spec_hash
        audit["requirements_evaluated"]["REQ-001"]["design_rationale"] = ""
        audit_file.write_text(json.dumps(audit), encoding="utf-8")
        self.assertFalse(spec_checker.validate_semantic_traceability(pkg)[0])


if __name__ == "__main__":
    unittest.main()
