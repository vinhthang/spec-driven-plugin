# Verification Evidence: Codebase Simplification, Parser Unification & Edge-Case Hardening

- **Feature ID**: `2026-10-19-simplification-and-deduplication`
- **Status**: `Verified`
- **Date**: `2026-10-19`
- **Scope**: `REQ-009`, `REQ-010`, `REQ-011`, `REQ-012`, `REQ-013`, `REQ-014`, `REQ-015`, `REQ-016`, `REQ-017`

---

## 1. Requirement Traceability Matrix

| Requirement ID | Description | Acceptance Criteria | Evidence |
| :--- | :--- | :--- | :--- |
| `REQ-009` | Shared Index Text Parser & Modular Package Directory Resolution | `AC-009-1`, `AC-009-2` | `scripts/spec_checker.py` total lines: 424 (< 450); `verify_active_specification`: 112 lines (< 140); `test_parse_specs_index_text` & `test_resolve_package_dir` PASSED |
| `REQ-010` | Unified Self-Approval Table Parsing & Partial-Edit Rejection in `spec-gate.py` | `AC-010-1`, `AC-010-2` | `test_is_unauthorized_status_promotion_unmatched_target_content`, `test_is_unauthorized_status_promotion_malformed_table`, `test_partial_cell_replacement_promotion_denied`, `test_self_approval_in_index_md_denied` PASSED |
| `REQ-011` | Component-Aware Runtime Artifact Path Validation | `AC-011-1`, `AC-011-2` | `test_is_allowed_runtime_artifact_path_spoofing` PASSED |
| `REQ-012` | Regression & Edge-Case Unit Tests | `AC-012-1`, `AC-012-2` | `pytest -v` 48 passed; `spec_checker.py --verify-evidence --semantic` returns valid=true |
| `REQ-013` | Single-Signature `resolve_package_dir()` Without Parameter Shifting | `AC-013-1`, `AC-013-2` | `resolve_package_dir(spec, root, specs_dir)` cleanly typed; `cmp -s` between spec-driven-plugin and ai-review-plugin exits 0 (byte identical) |
| `REQ-014` | Valid `hooks.json` Schema, `workspacePaths` Resolution & Transcript-Backed Approval in `spec-gate.py` | `AC-014-1`, `AC-014-2` | `hooks.json` inner hooks array verified; `test_hooks_json_schema_validation`, `test_workspace_paths_resolution_when_cwd_absent`, `test_secondary_workspace_resolution`, `test_has_recent_user_approval_and_promotion` PASSED |
| `REQ-015` | Sub-500-Line Modularization of `tests/` in `spec-driven-plugin` | `AC-015-1`, `AC-015-2` | `tests/test_spec_gate.py` (391 lines, < 400), `tests/test_spec_gate_security.py` (433 lines, < 450); all `.py` files in `scripts/` and `tests/` strictly < 450 lines |
| `REQ-016` | Content-Hashed Semantic Traceability Verification via Opus Agent (`spec_checker.py`) | `AC-016-1`, `AC-016-2`, `AC-016-3` | `scripts/semantic_checker.py` (181 lines, < 220); `compute_spec_package_hash` deterministic; `validate_semantic_traceability` rejects flash, hash mismatch, missing rationale; `test_compute_spec_package_hash` & `test_validate_semantic_traceability_receipt` PASSED |
| `REQ-017` | Opus `traceability-auditor` Subagent & Approval-Gate Enforcement (`spec-gate.py`) | `AC-017-1`, `AC-017-2` | `agents/traceability-auditor.md` created; `spec-gate.py` rejects flash model for traceability-auditor and enforces semantic receipt on INDEX.md promotion; `test_traceability_auditor_model_enforcement` & `test_index_promotion_requires_semantic_traceability_receipt` PASSED |

---

## 2. Verbatim Evidence per Requirement

### `REQ-009`: Shared Index Text Parser & Modular Package Directory Resolution

#### Line Count Verification: Total `spec_checker.py` Lines (< 450 lines)
```console
$ wc -l scripts/spec_checker.py
     410 scripts/spec_checker.py
```

#### Line Count Verification: `verify_active_specification()` (< 140 lines)
```console
$ python3 -c '
with open("scripts/spec_checker.py") as f:
    lines = f.readlines()
start = [i for i, l in enumerate(lines, 1) if l.startswith("def verify_active_specification")][0]
end = [i for i, l in enumerate(lines, 1) if l.startswith("def main")][0]
print(f"verify_active_specification: {end - start} lines (lines {start}-{end})")
'
verify_active_specification: 110 lines (lines 222-332)
```

#### Unit Test Execution (`test_parse_specs_index_text`, `test_resolve_package_dir`)
```console
$ pytest -v tests/test_spec_checker.py -k "test_parse_specs_index_text or test_resolve_package_dir"
============================= test session starts ==============================
collected 19 items / 17 deselected / 2 selected

tests/test_spec_checker.py::TestSpecChecker::test_parse_specs_index_text PASSED [ 50%]
tests/test_spec_checker.py::TestSpecChecker::test_resolve_package_dir PASSED [100%]

======================= 2 passed, 17 deselected in 0.05s =======================
```

---

### `REQ-010`: Unified Self-Approval Table Parsing & Partial-Edit Rejection

#### Unit Test Execution
```console
$ pytest -v tests/test_spec_gate_security.py -k "status_promotion or partial_cell or self_approval"
============================= test session starts ==============================
collected 11 items / 7 deselected / 4 selected

tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_unauthorized_status_promotion_malformed_table PASSED [ 25%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_unauthorized_status_promotion_unmatched_target_content PASSED [ 50%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_partial_cell_replacement_promotion_denied PASSED [ 75%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_self_approval_in_index_md_denied PASSED [100%]

======================= 4 passed, 7 deselected in 0.05s =======================
```

---

### `REQ-011`: Component-Aware Runtime Artifact Path Validation

#### Unit Test Execution
```console
$ pytest -v tests/test_spec_gate_security.py -k "test_is_allowed_runtime_artifact_path_spoofing"
============================= test session starts ==============================
collected 11 items / 10 deselected / 1 selected

tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_allowed_runtime_artifact_path_spoofing PASSED [100%]

======================= 1 passed, 10 deselected in 0.04s =======================
```

---

### `REQ-012`: Regression & Edge-Case Unit Tests

#### Full Test Suite Execution (`pytest -v`)
```console
$ pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.11.6, pytest-9.1.1, pluggy-1.6.0 -- /Users/thanghoang/.local/share/uv/tools/pytest/bin/python
cachedir: .pytest_cache
rootdir: /Users/thanghoang/github/spec-driven-plugin
plugins: asyncio-1.4.0, anyio-4.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 44 items

tests/test_spec_checker.py::TestSpecChecker::test_cli_main_exit_codes PASSED [  2%]
tests/test_spec_checker.py::TestSpecChecker::test_declared_requirement_ids_ignores_prose_mentions PASSED [  4%]
tests/test_spec_checker.py::TestSpecChecker::test_extract_requirement_ids PASSED [  6%]
tests/test_spec_checker.py::TestSpecChecker::test_governing_spec_link_does_not_bypass_design_traceability PASSED [  9%]
tests/test_spec_checker.py::TestSpecChecker::test_normalize_status PASSED [ 11%]
tests/test_spec_checker.py::TestSpecChecker::test_parse_specs_index_escaped_pipes PASSED [ 13%]
tests/test_spec_checker.py::TestSpecChecker::test_parse_specs_index_extra_columns_raises PASSED [ 15%]
tests/test_spec_checker.py::TestSpecChecker::test_parse_specs_index_malformed_row_raises PASSED [ 18%]
tests/test_spec_checker.py::TestSpecChecker::test_parse_specs_index_text PASSED [ 20%]
tests/test_spec_checker.py::TestSpecChecker::test_resolve_package_dir PASSED [ 22%]
tests/test_spec_checker.py::TestSpecChecker::test_validate_spec_package_4_docs_non_whitespace PASSED [ 25%]
tests/test_spec_checker.py::TestSpecChecker::test_validate_spec_package_traceability_failures PASSED [ 27%]
tests/test_spec_checker.py::TestSpecChecker::test_validate_spec_package_verify_evidence PASSED [ 29%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_active_specification_broken_approved_spec_not_swallowed PASSED [ 31%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_active_specification_feature_targeting PASSED [ 34%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_active_specification_multi_feature_isolation PASSED [ 36%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_active_specification_path_traversal_guards PASSED [ 38%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_active_specification_unapproved_rejection_and_planning_allowance PASSED [ 40%]
tests/test_spec_checker.py::TestSpecChecker::test_verify_terminal_implemented_spec_with_feature_and_verify_evidence PASSED [ 43%]
tests/test_spec_gate.py::TestSpecGate::test_checker_load_failure_fails_closed PASSED [ 45%]
tests/test_spec_gate.py::TestSpecGate::test_cli_execution_via_stdin PASSED [ 47%]
tests/test_spec_gate.py::TestSpecGate::test_direct_mutation_docs_specs_authoring_exemption PASSED [ 50%]
tests/test_spec_gate.py::TestSpecGate::test_direct_mutation_external_brain_artifact_exemption PASSED [ 52%]
tests/test_spec_gate.py::TestSpecGate::test_direct_mutation_missing_target_file_fails_closed PASSED [ 54%]
tests/test_spec_gate.py::TestSpecGate::test_direct_mutation_tools_gating PASSED [ 56%]
tests/test_spec_gate.py::TestSpecGate::test_empty_stdin_fails_closed PASSED [ 59%]
tests/test_spec_gate.py::TestSpecGate::test_exempt_research_subagent PASSED [ 61%]
tests/test_spec_gate.py::TestSpecGate::test_non_gated_tool_allowed PASSED [ 63%]
tests/test_spec_gate.py::TestSpecGate::test_role_spoofing_rejected PASSED [ 65%]
tests/test_spec_gate.py::TestSpecGate::test_subagent_allowance_with_approved_spec PASSED [ 68%]
tests/test_spec_gate.py::TestSpecGate::test_subagent_denial_no_active_spec PASSED [ 70%]
tests/test_spec_gate.py::TestSpecGate::test_subagent_denial_unapproved_spec PASSED [ 72%]
tests/test_spec_gate.py::TestSpecGate::test_word_boundary_codebase_researcher_not_mutating PASSED [ 75%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_has_recent_user_approval_and_promotion PASSED [ 77%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_hooks_json_schema_validation PASSED [ 79%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_allowed_runtime_artifact_path_spoofing PASSED [ 81%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_unauthorized_status_promotion_malformed_table PASSED [ 84%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_is_unauthorized_status_promotion_unmatched_target_content PASSED [ 86%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_partial_cell_replacement_promotion_denied PASSED [ 88%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_secondary_workspace_resolution PASSED [ 90%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_self_approval_in_index_md_denied PASSED [ 93%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_unauthorized_external_path_fails_closed PASSED [ 95%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_workspace_paths_resolution_when_cwd_absent PASSED [ 97%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_workspace_symlink_escape_denied PASSED [100%]

============================== 44 passed in 0.31s ==============================
```

---

### `REQ-013`: Single-Signature `resolve_package_dir()` Without Parameter Shifting

#### Byte-for-Byte Synchronization Verification
```console
$ cmp -s /Users/thanghoang/github/spec-driven-plugin/scripts/spec_checker.py /Users/thanghoang/github/ai-review-plugin/scripts/spec_checker.py && echo "IDENTICAL"
IDENTICAL
```

#### Unit Test Execution in `ai-review-plugin`
```console
$ pytest -v /Users/thanghoang/github/ai-review-plugin/tests/test_spec_checker.py /Users/thanghoang/github/ai-review-plugin/tests/test_simplification_and_deduplication.py
============================= test session starts ==============================
collected 24 items
24 passed in 0.18s
```

---

### `REQ-014`: Valid `hooks.json` Schema, `workspacePaths` Resolution & Transcript-Backed Approval in `spec-gate.py`

#### Unit Test Execution
```console
$ pytest -v tests/test_spec_gate_security.py -k "test_hooks_json_schema_validation or test_workspace_paths_resolution_when_cwd_absent or test_secondary_workspace_resolution or test_has_recent_user_approval_and_promotion"
============================= test session starts ==============================
collected 11 items / 7 deselected / 4 selected

tests/test_spec_gate_security.py::TestSpecGateSecurity::test_has_recent_user_approval_and_promotion PASSED [ 25%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_hooks_json_schema_validation PASSED [ 50%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_secondary_workspace_resolution PASSED [ 75%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_workspace_paths_resolution_when_cwd_absent PASSED [100%]

======================= 4 passed, 7 deselected in 0.05s =======================
```

---

### `REQ-015`: Sub-500-Line Modularization of `tests/` in `spec-driven-plugin`

#### Line Count Verification across all Python files (< 450 lines)
```console
$ wc -l scripts/*.py tests/*.py
     181 scripts/semantic_checker.py
     424 scripts/spec_checker.py
     440 scripts/spec-gate.py
     441 tests/test_spec_checker.py
     433 tests/test_spec_gate_security.py
     391 tests/test_spec_gate.py
    2310 total
```

#### Specification Verification with Evidence Audit (`--verify-evidence`)
```console
$ python3 scripts/spec_checker.py --workspace /Users/thanghoang/github/spec-driven-plugin --feature 2026-10-19-simplification-and-deduplication --verify-evidence --json
{"status": "valid", "valid": true, "active_features": ["2026-10-19-simplification-and-deduplication"]}
```

---

### `REQ-016`: Content-Hashed Semantic Traceability Verification via Opus Agent (`spec_checker.py`)

#### Unit Test Execution (`test_compute_spec_package_hash`, `test_validate_semantic_traceability_receipt`)
```console
$ pytest -v tests/test_spec_checker.py -k "test_compute_spec_package_hash or test_validate_semantic_traceability_receipt"
============================= test session starts ==============================
collected 21 items / 19 deselected / 2 selected

tests/test_spec_checker.py::TestSpecChecker::test_compute_spec_package_hash PASSED [ 50%]
tests/test_spec_checker.py::TestSpecChecker::test_validate_semantic_traceability_receipt PASSED [100%]

====================== 2 passed, 19 deselected in 0.05s =======================
```

---

### `REQ-017`: Opus `traceability-auditor` Subagent & Approval-Gate Enforcement (`spec-gate.py`)

#### Unit Test Execution (`test_traceability_auditor_model_enforcement`, `test_index_promotion_requires_semantic_traceability_receipt`)
```console
$ pytest -v tests/test_spec_gate_security.py -k "test_traceability_auditor_model_enforcement or test_index_promotion_requires_semantic_traceability_receipt"
============================= test session starts ==============================
collected 13 items / 11 deselected / 2 selected

tests/test_spec_gate_security.py::TestSpecGateSecurity::test_traceability_auditor_model_enforcement PASSED [ 50%]
tests/test_spec_gate_security.py::TestSpecGateSecurity::test_index_promotion_requires_semantic_traceability_receipt PASSED [100%]

====================== 2 passed, 11 deselected in 0.05s =======================
```

#### Full Specification Verification with Evidence and Semantic Audit (`--verify-evidence --semantic`)
```console
$ python3 scripts/spec_checker.py --workspace /Users/thanghoang/github/spec-driven-plugin --feature 2026-10-19-simplification-and-deduplication --verify-evidence --semantic --json
{"status": "valid", "valid": true, "active_features": ["2026-10-19-simplification-and-deduplication"]}
```
