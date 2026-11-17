"""Non-mocked test suite for spec-driven validate_specs.py."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "skills" / "spec-driven" / "scripts"
EXAMPLE_MD = PLUGIN_ROOT / "skills" / "spec-driven" / "references" / "example.md"
_AI_REVIEW_SCRIPTS = (
    Path(
        os.environ.get(
            "AI_REVIEW_PLUGIN_DIR",
            str(Path.home() / ".gemini/config/plugins/ai-review-plugin"),
        )
    )
    / "scripts"
)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if _AI_REVIEW_SCRIPTS.is_dir() and str(_AI_REVIEW_SCRIPTS) not in sys.path:
    sys.path.append(str(_AI_REVIEW_SCRIPTS))

from validate_specs import (  # noqa: E402
    heading_slug,
    main,
    strip_fenced_code_blocks,
    validate_workspace,
)


def _extract_example_files(example_path: Path) -> dict[str, str]:
    """Parse `## `path`` + fenced markdown blocks from references/example.md."""
    text = example_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^## `(?P<relpath>[^`]+)`\s*\n\s*\n(?P<fence>`{3,4})markdown\n(?P<body>.*?)\n(?P=fence)(?:\n|$)",
        re.MULTILINE | re.DOTALL,
    )
    extracted: dict[str, str] = {}
    for match in pattern.finditer(text):
        extracted[match.group("relpath")] = match.group("body") + "\n"
    return extracted


def _write_tree(base: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _make_package_files(
    feature_id: str = "2026-11-18-sample-feature",
    *,
    status: str = "In-Testing",
    first_entered: str = "2026-11-18",
    req_id: str = "REQ-001",
    ac_num: str = "001",
    adr_block: str = "",
    adr_index: str = "None",
    gate1_status: str = "PASS",
    gate2_status: str = "PASS — verified mapping",
    gate2_extra_status: str = "PASS",
    task_checked: bool = True,
    execution_ref: str = "[Run 1](#run-1--2026-11-18)",
    execution_evidence: str | None = None,
    real_world_obs: str = "No real-world confirmation has been recorded.",
    provisional: bool = False,
    include_derived: bool = True,
) -> dict[str, str]:
    """Build a valid or mutated 5-document package under docs/specs/."""
    pkg = f"docs/specs/{feature_id}"
    req_heading_suffix = " [PROVISIONAL]" if provisional else ""
    req_extra_meta = (
        "- Open question: Exact timeout ceiling?\n"
        "- Owner deferral: Deferred by Sam on 2026-11-18.\n"
        f"- Blocked scope: AC-{ac_num}-2 and dependent tasks.\n"
        if provisional
        else ""
    )
    ac2_label = "Deferred [PROVISIONAL]" if provisional else "Boundary/failure"
    spec_md = (
        f"# Sample feature\n\n"
        f"- Feature ID: {feature_id}\n"
        f"- Type: enhancement\n"
        f"- Status: {status}\n"
        f"- First entered In-Testing: {first_entered}\n"
        f"- Related specifications: None\n\n"
        f"## Problem and source intent\n\n"
        f'User request: "Add deterministic validation for sample feature."\n\n'
        f"## Repository grounding\n\n"
        f"Checked `src/app.py::run` and `tests/test_app.py`.\n\n"
        f"## Non-goals\n\n"
        f"- Changing unrelated CLI flags.\n\n"
        f"## Requirements\n\n"
        f"### {req_id}: Validate sample input{req_heading_suffix}\n\n"
        f"- Source intent: User request.\n"
        f"{req_extra_meta}"
        f"- Statement: WHEN `run` receives input, THE validator SHALL check invariants.\n"
        f"- AC-{ac_num}-1 — Success: Returns valid outcome for well-formed input.\n"
        f"- AC-{ac_num}-2 — {ac2_label}: Raises ValueError on negative count.\n\n"
        f"## Assumptions and owner-deferred questions\n\n"
        f"None.\n\n"
        f"## Approvals and lifecycle history\n\n"
        f"- 2026-11-18 (`Planning -> {status}`): Approved for test.\n"
    )

    decisions_md = (
        f"# Decisions: Sample feature\n\n"
        f"Governing specification: [spec.md](./spec.md)\n\n"
        f"## Architectural rationale\n\n"
        f"- Governs: {req_id}\n\n"
        f"Constrained to Python stdlib.\n\n"
        f"{adr_block}"
        f"## Gate 1: normative review\n\n"
        f"| Check | Status | Evidence / required correction |\n"
        f"| --- | --- | --- |\n"
        f"| Codebase grounding | {gate1_status} | Inspected `src/app.py`. |\n"
        f"| Attributable intent and explicit scope | {gate1_status} | Scoped to `{req_id}`. |\n"
        f"| Observable requirements and meaningful acceptance criteria | {gate1_status} | Criteria AC-{ac_num}-1/2 observable. |\n"
        f"| Assumptions and owner-deferred questions are explicit | {gate1_status} | Explicit assumptions recorded. |\n"
        f"| Architectural rationale respects requirements | {gate1_status} | Constrained rationale covers `{req_id}`. |\n"
        f"| IDs, references, and revision route are consistent | {gate1_status} | Registered in `INDEX.md`. |\n"
    )

    index_md = (
        f"# Feature specifications\n\n"
        f"| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |\n"
        f"| --- | --- | --- | --- | --- | --- |\n"
        f"| {feature_id} | Sample feature | {status} | {req_id} | {adr_index} | [spec](./{feature_id}/spec.md) |\n"
    )

    files: dict[str, str] = {
        "docs/specs/INDEX.md": index_md,
        f"{pkg}/spec.md": spec_md,
        f"{pkg}/decisions.md": decisions_md,
    }
    if not include_derived:
        return files

    adr_link = (
        "[ADR-001](./decisions.md#adr-001-choice)"
        if adr_block
        else "[Rationale](./decisions.md#architectural-rationale)"
    )
    checkbox = "[x]" if task_checked else "[ ]"
    if execution_evidence is None:
        execution_evidence = (
            "### Run 1 — 2026-11-18\n\n"
            f"- Checked: {req_id} / AC-{ac_num}-1, AC-{ac_num}-2 (`local`)\n"
            "- Command: `pytest -q tests/test_app.py` (exit code: `0`)\n"
            "- Output excerpt:\n"
            "  ```text\n"
            "  2 passed in 0.02s\n"
            "  ```\n"
            f"- Result: AC-{ac_num}-1 `PASS`, AC-{ac_num}-2 `PASS` — verified.\n"
        )

    files[f"{pkg}/design.md"] = (
        "# Design: Sample feature\n\n"
        "Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)\n\n"
        "## Components\n\n"
        "| Requirement / AC | Path and symbol | Responsibility / change |\n"
        "| --- | --- | --- |\n"
        f"| {req_id} / AC-{ac_num}-1, AC-{ac_num}-2 | `src/app.py::run` | Validate input. |\n\n"
        "## Interfaces and flow\n\n"
        "- `run(count: int) -> bool`\n\n"
        "## Boundaries and recovery\n\n"
        "- Raise `ValueError` when `count < 0`.\n\n"
        "## Dependencies and unresolved design work\n\n"
        "None.\n"
    )

    files[f"{pkg}/tasks.md"] = (
        "# Tasks: Sample feature\n\n"
        "Sources: [spec.md](./spec.md), [design.md](./design.md)\n\n"
        "## Task 1: Implement validation\n\n"
        f"- {checkbox} Complete the work and its applicable checks.\n"
        f"- Covers: {req_id} / AC-{ac_num}-1, AC-{ac_num}-2\n"
        "- Dependencies: None\n"
        "- Blocked by: None\n"
        "- Work: Update `src/app.py::run`.\n"
        "- Completion evidence: Verified.\n\n"
        "## Gate 2: traceability and readiness\n\n"
        "| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        f"| {req_id} | AC-{ac_num}-1 | {adr_link} | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-implement-validation) | [AC-{ac_num}-1](./verification.md#ac-{ac_num}-1-req-{ac_num}) | {gate2_status} |\n"
        f"| {req_id} | AC-{ac_num}-2 | {adr_link} | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-{ac_num}-2](./verification.md#ac-{ac_num}-2-req-{ac_num}) | {gate2_status} |\n\n"
        f"- Backward scope check: {gate2_extra_status}\n"
        f"- Reference and catalog consistency: {gate2_extra_status}\n"
    )

    files[f"{pkg}/verification.md"] = (
        "# Verification: Sample feature\n\n"
        "Governing specification: [spec.md](./spec.md)\n\n"
        "## Planned checks\n\n"
        f"### AC-{ac_num}-1 ({req_id})\n\n"
        "- Method: Unit test in `tests/test_app.py`.\n"
        "- Expected outcome: Valid input returns True.\n"
        f"- Execution: {execution_ref}\n\n"
        f"### AC-{ac_num}-2 ({req_id})\n\n"
        "- Method: Unit test with `count=-1`.\n"
        "- Expected outcome: Raises `ValueError`.\n"
        f"- Execution: {execution_ref}\n\n"
        "## Execution evidence\n\n"
        f"{execution_evidence}\n"
        "## Real-world observations\n\n"
        f"{real_world_obs}\n"
    )
    return files


def test_golden_example_end_to_end(tmp_path: Path) -> None:
    extracted = _extract_example_files(EXAMPLE_MD)
    assert len(extracted) == 6
    _write_tree(tmp_path, extracted)

    result = validate_workspace(tmp_path)
    assert result["valid"] is True
    assert result["errors"] == []


def test_golden_example_ai_review_spec_checker_compat(tmp_path: Path) -> None:
    spec_checker = pytest.importorskip("spec_checker", reason="ai-review-plugin not installed")

    extracted = _extract_example_files(EXAMPLE_MD)
    _write_tree(tmp_path, extracted)
    pkg_dir = tmp_path / "docs" / "specs" / "2026-11-18-queue-retry-jitter"
    assert spec_checker.validate_spec_package(pkg_dir, verify_evidence=True) == (True, "")

    in_prog_root = tmp_path / "active_ws"
    _write_tree(
        in_prog_root,
        _make_package_files(
            status="In-Progress",
            first_entered="Never",
            task_checked=False,
            execution_ref="Not run.",
            execution_evidence="No checks have been executed.",
        ),
    )
    active_res = spec_checker.verify_active_specification(in_prog_root, verify_evidence=True)
    assert active_res["valid"] is True
    assert active_res["active_features"] == ["2026-11-18-sample-feature"]


def test_heading_slug_and_fence_stripping() -> None:
    assert heading_slug("Run 1 — 2026-11-18") == "run-1--2026-11-18"
    assert heading_slug("AC-001-1 (REQ-001)") == "ac-001-1-req-001"
    assert (
        heading_slug("Task 1: Add seeded full-jitter sampling to `compute_backoff_ms`")
        == "task-1-add-seeded-full-jitter-sampling-to-compute_backoff_ms"
    )
    assert heading_slug("[Link Text](./other.md) & `code`") == "link-text--code"

    md = (
        "Before <keep>\n"
        "  ```text\n"
        "  <ignored-placeholder> TODO FIXME\n"
        "  ```\n"
        "````markdown\n"
        "## Not a heading\n"
        "````\n"
        "After\n"
    )
    stripped = strip_fenced_code_blocks(md)
    assert "<ignored-placeholder>" not in stripped
    assert "## Not a heading" not in stripped
    assert "Before <keep>" in stripped
    assert "After" in stripped


def test_stage_gate1_planning_valid_and_invalid(tmp_path: Path) -> None:
    files = _make_package_files(
        status="Planning",
        first_entered="Never",
        gate1_status="PASS",
        include_derived=False,
    )
    _write_tree(tmp_path, files)
    res = validate_workspace(tmp_path / "docs" / "specs" / "2026-11-18-sample-feature", stage="gate1")
    assert res["valid"] is True
    assert res["errors"] == []

    for bad_status in ("UNCHECKED", "FAIL"):
        ws = tmp_path / f"bad_{bad_status}"
        _write_tree(
            ws,
            _make_package_files(
                status="Planning",
                first_entered="Never",
                gate1_status=bad_status,
                include_derived=False,
            ),
        )
        bad_res = validate_workspace(ws / "docs" / "specs" / "2026-11-18-sample-feature", stage="gate1")
        assert bad_res["valid"] is False
        assert any("Gate 1" in e for e in bad_res["errors"])


def test_planning_full_package_valid(tmp_path: Path) -> None:
    files = _make_package_files(
        status="Planning",
        first_entered="Never",
        gate1_status="PASS",
        gate2_status="PASS — ready for approval",
        task_checked=False,
        execution_ref="Not run.",
        execution_evidence="No checks have been executed.",
    )
    _write_tree(tmp_path, files)
    res = validate_workspace(tmp_path / "docs" / "specs" / "2026-11-18-sample-feature", stage="full")
    assert res["valid"] is True
    assert res["errors"] == []


def test_in_progress_with_provisional_and_blocked(tmp_path: Path) -> None:
    files = _make_package_files(
        feature_id="2026-11-18-provisional",
        status="In-Progress",
        first_entered="Never",
        req_id="REQ-002",
        ac_num="002",
        provisional=True,
        task_checked=False,
    )
    # Set AC-002-2 Gate 2 row to BLOCKED and verification stub to Blocked pending...
    pkg = "docs/specs/2026-11-18-provisional"
    files[f"{pkg}/tasks.md"] = files[f"{pkg}/tasks.md"].replace(
        "| REQ-002 | AC-002-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-002-2](./verification.md#ac-002-2-req-002) | PASS — verified mapping |",
        "| REQ-002 | AC-002-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-002-2](./verification.md#ac-002-2-req-002) | BLOCKED — awaiting owner answer |",
    )
    files[f"{pkg}/verification.md"] = files[f"{pkg}/verification.md"].replace(
        "### AC-002-2 (REQ-002)\n\n- Method: Unit test with `count=-1`.\n- Expected outcome: Raises `ValueError`.\n- Execution: [Run 1](#run-1--2026-11-18)",
        "### AC-002-2 (REQ-002)\n\n- Method: Blocked pending REQ-002 [PROVISIONAL] resolution.\n- Expected outcome: Raises `ValueError`.\n- Execution: Blocked pending REQ-002 [PROVISIONAL] resolution.",
    )
    _write_tree(tmp_path, files)
    res = validate_workspace(tmp_path)
    assert res["valid"] is True
    assert res["errors"] == []

    # Fails if Gate 1 or Gate 2 has UNCHECKED or FAIL
    for bad in ("UNCHECKED", "FAIL"):
        ws_g1 = tmp_path / f"g1_{bad}"
        bad_files = dict(files)
        bad_files[f"{pkg}/decisions.md"] = bad_files[f"{pkg}/decisions.md"].replace("| PASS |", f"| {bad} |", 1)
        _write_tree(ws_g1, bad_files)
        r1 = validate_workspace(ws_g1)
        assert r1["valid"] is False
        assert any("Gate 1" in e for e in r1["errors"])

        ws_g2 = tmp_path / f"g2_{bad}"
        bad_files2 = dict(files)
        bad_files2[f"{pkg}/tasks.md"] = bad_files2[f"{pkg}/tasks.md"].replace("| PASS — verified mapping |", f"| {bad} |", 1)
        _write_tree(ws_g2, bad_files2)
        r2 = validate_workspace(ws_g2)
        assert r2["valid"] is False
        assert any("Gate 2" in e for e in r2["errors"])


@pytest.mark.parametrize(
    "case_name,overrides,expected_substr",
    [
        ("first_entered_never", {"first_entered": "Never"}, "First entered In-Testing"),
        ("first_entered_unknown", {"first_entered": "Unknown"}, "First entered In-Testing"),
        ("provisional_remains", {"provisional": True}, "PROVISIONAL"),
        ("gate1_unchecked", {"gate1_status": "UNCHECKED"}, "Gate 1"),
        ("gate1_fail", {"gate1_status": "FAIL"}, "Gate 1"),
        ("gate2_unchecked", {"gate2_status": "UNCHECKED"}, "Gate 2"),
        ("gate2_fail", {"gate2_status": "FAIL"}, "Gate 2"),
        ("gate2_blocked", {"gate2_status": "BLOCKED — pending"}, "Gate 2"),
        ("unchecked_task", {"task_checked": False}, "unchecked task"),
        ("execution_not_run", {"execution_ref": "Not run."}, "Not run"),
        (
            "no_run_evidence",
            {"execution_evidence": "No checks have been executed."},
            "Execution evidence",
        ),
    ],
)
def test_in_testing_failures(
    tmp_path: Path,
    case_name: str,
    overrides: dict,
    expected_substr: str,
) -> None:
    ws = tmp_path / case_name
    _write_tree(ws, _make_package_files(status="In-Testing", **overrides))
    res = validate_workspace(ws)
    assert res["valid"] is False
    assert any(expected_substr.lower() in e.lower() for e in res["errors"]), res["errors"]


def test_verified_requires_real_world_observations(tmp_path: Path) -> None:
    ws_bad1 = tmp_path / "verified_default"
    _write_tree(
        ws_bad1,
        _make_package_files(
            status="Verified",
            real_world_obs="No real-world confirmation has been recorded.",
        ),
    )
    r1 = validate_workspace(ws_bad1)
    assert r1["valid"] is False
    assert any("Real-world" in e for e in r1["errors"])

    ws_bad2 = tmp_path / "verified_empty"
    _write_tree(ws_bad2, _make_package_files(status="Verified", real_world_obs=""))
    r2 = validate_workspace(ws_bad2)
    assert r2["valid"] is False
    assert any("Real-world" in e for e in r2["errors"])

    ws_ok = tmp_path / "verified_ok"
    _write_tree(
        ws_ok,
        _make_package_files(
            status="Verified",
            real_world_obs="Confirmed in production on 2026-11-19 by Sam.",
        ),
    )
    r_ok = validate_workspace(ws_ok)
    assert r_ok["valid"] is True
    assert r_ok["errors"] == []


def test_index_mismatches_and_duplicate_ids(tmp_path: Path) -> None:
    # Status mismatch
    ws_status = tmp_path / "status_mismatch"
    files = _make_package_files()
    files["docs/specs/INDEX.md"] = files["docs/specs/INDEX.md"].replace("| In-Testing |", "| Planning |")
    _write_tree(ws_status, files)
    r_status = validate_workspace(ws_status)
    assert r_status["valid"] is False
    assert any("status" in e.lower() for e in r_status["errors"])

    # REQ IDs mismatch
    ws_req = tmp_path / "req_mismatch"
    files2 = _make_package_files()
    files2["docs/specs/INDEX.md"] = files2["docs/specs/INDEX.md"].replace("| REQ-001 |", "| REQ-999 |")
    _write_tree(ws_req, files2)
    r_req = validate_workspace(ws_req)
    assert r_req["valid"] is False
    assert any("REQ" in e for e in r_req["errors"])

    # ADR IDs mismatch
    ws_adr = tmp_path / "adr_mismatch"
    files3 = _make_package_files()
    files3["docs/specs/INDEX.md"] = files3["docs/specs/INDEX.md"].replace("| None |", "| ADR-001 |")
    _write_tree(ws_adr, files3)
    r_adr = validate_workspace(ws_adr)
    assert r_adr["valid"] is False
    assert any("ADR" in e for e in r_adr["errors"])

    # Duplicate REQ-001 and ADR-001 across two distinct packages
    ws_dup = tmp_path / "dup"
    adr_blk = (
        "## ADR-001: Choice\n\n"
        "- Governs: REQ-001\n"
        "- State: Accepted\n"
        "- Decision: Stdlib.\n\n"
    )
    pkg1 = _make_package_files(
        feature_id="2026-11-18-pkg-one",
        adr_block=adr_blk,
        adr_index="ADR-001",
    )
    pkg2 = _make_package_files(
        feature_id="2026-11-19-pkg-two",
        adr_block=adr_blk,
        adr_index="ADR-001",
    )
    combined_index = (
        "# Feature specifications\n\n"
        "| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 2026-11-18-pkg-one | One | In-Testing | REQ-001 | ADR-001 | [spec](./2026-11-18-pkg-one/spec.md) |\n"
        "| 2026-11-19-pkg-two | Two | In-Testing | REQ-001 | ADR-001 | [spec](./2026-11-19-pkg-two/spec.md) |\n"
    )
    merged = {**pkg1, **pkg2, "docs/specs/INDEX.md": combined_index}
    _write_tree(ws_dup, merged)
    r_dup = validate_workspace(ws_dup)
    assert r_dup["valid"] is False
    assert any("duplicate" in e.lower() and "REQ-001" in e for e in r_dup["errors"])
    assert any("duplicate" in e.lower() and "ADR-001" in e for e in r_dup["errors"])


def test_placeholders_todos_missing_traceability_and_broken_links(tmp_path: Path) -> None:
    # Placeholder outside code block / backticks fails; inside code block / backticks passes
    ws_ok_code = tmp_path / "ok_code"
    files_ok = _make_package_files()
    files_ok["docs/specs/2026-11-18-sample-feature/design.md"] += (
        "\nNote: `<angle>` and `TODO` in backticks are literal examples; `x < 5` is math.\n"
        "```text\n<fenced-placeholder> TODO TBD FIXME\n```\n"
    )
    _write_tree(ws_ok_code, files_ok)
    assert validate_workspace(ws_ok_code)["valid"] is True

    ws_ph = tmp_path / "placeholder"
    files_ph = _make_package_files()
    files_ph["docs/specs/2026-11-18-sample-feature/spec.md"] += "\nExtra <unfilled-field> here.\n"
    _write_tree(ws_ph, files_ph)
    r_ph = validate_workspace(ws_ph)
    assert r_ph["valid"] is False
    assert any("placeholder" in e.lower() for e in r_ph["errors"])

    for marker in ("TODO", "TBD", "FIXME"):
        ws_todo = tmp_path / f"todo_{marker}"
        files_todo = _make_package_files()
        files_todo["docs/specs/2026-11-18-sample-feature/design.md"] += f"\n{marker}: finish later.\n"
        _write_tree(ws_todo, files_todo)
        r_todo = validate_workspace(ws_todo)
        assert r_todo["valid"] is False
        assert any(marker in e for e in r_todo["errors"])

    # Missing REQ-001 in each of design.md, tasks.md, verification.md, decisions.md
    for doc_name in ("design.md", "tasks.md", "verification.md", "decisions.md"):
        ws_miss_req = tmp_path / f"miss_req_{doc_name}"
        files_mr = _make_package_files()
        path_key = f"docs/specs/2026-11-18-sample-feature/{doc_name}"
        files_mr[path_key] = files_mr[path_key].replace("REQ-001", "REQ-999")
        _write_tree(ws_miss_req, files_mr)
        r_mr = validate_workspace(ws_miss_req)
        assert r_mr["valid"] is False
        assert any("REQ-001" in e and doc_name in e for e in r_mr["errors"])

    # Missing AC-001-2 row in Gate 2
    ws_miss_ac_g2 = tmp_path / "miss_ac_g2"
    files_ac2 = _make_package_files()
    files_ac2["docs/specs/2026-11-18-sample-feature/tasks.md"] = "\n".join(
        line
        for line in files_ac2["docs/specs/2026-11-18-sample-feature/tasks.md"].splitlines()
        if "| AC-001-2 |" not in line
    ) + "\n"
    _write_tree(ws_miss_ac_g2, files_ac2)
    r_ac2 = validate_workspace(ws_miss_ac_g2)
    assert r_ac2["valid"] is False
    assert any("AC-001-2" in e and "Gate 2" in e for e in r_ac2["errors"])

    # Missing ### AC-001-2 heading in verification.md
    ws_miss_ac_ver = tmp_path / "miss_ac_ver"
    files_ver = _make_package_files()
    files_ver["docs/specs/2026-11-18-sample-feature/verification.md"] = files_ver[
        "docs/specs/2026-11-18-sample-feature/verification.md"
    ].replace("### AC-001-2 (REQ-001)", "### Removed check")
    _write_tree(ws_miss_ac_ver, files_ver)
    r_ver = validate_workspace(ws_miss_ac_ver)
    assert r_ver["valid"] is False
    assert any("AC-001-2" in e for e in r_ver["errors"])

    # Broken relative link
    ws_link = tmp_path / "broken_link"
    files_link = _make_package_files()
    files_link["docs/specs/2026-11-18-sample-feature/design.md"] += "\nSee [missing](./missing.md).\n"
    _write_tree(ws_link, files_link)
    r_link = validate_workspace(ws_link)
    assert r_link["valid"] is False
    assert any("missing.md" in e for e in r_link["errors"])

    # Broken heading anchor
    ws_anchor = tmp_path / "broken_anchor"
    files_anchor = _make_package_files()
    files_anchor["docs/specs/2026-11-18-sample-feature/tasks.md"] += "\nSee [bad](./verification.md#wrong-anchor).\n"
    _write_tree(ws_anchor, files_anchor)
    r_anchor = validate_workspace(ws_anchor)
    assert r_anchor["valid"] is False
    assert any("wrong-anchor" in e for e in r_anchor["errors"])


def test_three_hop_delta_chain_valid_zero_false_duplicates(tmp_path: Path) -> None:
    spec_a = _make_package_files(
        feature_id="2026-11-01-spec-a",
        req_id="REQ-001",
        ac_num="001",
    )
    delta_b = _make_package_files(
        feature_id="2026-11-02-delta-b",
        req_id="REQ-002",
        ac_num="002",
    )
    delta_c = _make_package_files(
        feature_id="2026-11-03-delta-c",
        req_id="REQ-003",
        ac_num="003",
    )

    # Insert Current contract / Changes cross-package links and anchors
    spec_a["docs/specs/2026-11-01-spec-a/spec.md"] = spec_a[
        "docs/specs/2026-11-01-spec-a/spec.md"
    ].replace(
        "### REQ-001: Validate sample input\n\n",
        "### REQ-001: Validate sample input\n\n"
        "- Current contract: Changed by [2026-11-03-delta-c/REQ-003](../2026-11-03-delta-c/spec.md#req-003-validate-sample-input)\n",
    )
    delta_b["docs/specs/2026-11-02-delta-b/spec.md"] = delta_b[
        "docs/specs/2026-11-02-delta-b/spec.md"
    ].replace(
        "### REQ-002: Validate sample input\n\n",
        "### REQ-002: Validate sample input\n\n"
        "- Current contract: Changed by [2026-11-03-delta-c/REQ-003](../2026-11-03-delta-c/spec.md#req-003-validate-sample-input)\n"
        "- Changes: [2026-11-01-spec-a/REQ-001](../2026-11-01-spec-a/spec.md#req-001-validate-sample-input)\n",
    )
    delta_c["docs/specs/2026-11-03-delta-c/spec.md"] = delta_c[
        "docs/specs/2026-11-03-delta-c/spec.md"
    ].replace(
        "### REQ-003: Validate sample input\n\n",
        "### REQ-003: Validate sample input\n\n"
        "- Changes: [2026-11-02-delta-b/REQ-002](../2026-11-02-delta-b/spec.md#req-002-validate-sample-input)\n",
    )

    index_md = (
        "# Feature specifications\n\n"
        "| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 2026-11-01-spec-a | Spec A | In-Testing | REQ-001 | None | [spec](./2026-11-01-spec-a/spec.md) |\n"
        "| 2026-11-02-delta-b | Delta B | In-Testing | REQ-002 | None | [spec](./2026-11-02-delta-b/spec.md) |\n"
        "| 2026-11-03-delta-c | Delta C | In-Testing | REQ-003 | None | [spec](./2026-11-03-delta-c/spec.md) |\n"
    )
    merged = {**spec_a, **delta_b, **delta_c, "docs/specs/INDEX.md": index_md}
    _write_tree(tmp_path, merged)

    res = validate_workspace(tmp_path)
    assert res["valid"] is True
    assert res["errors"] == []


def test_cli_main_all_single_stage_and_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_tree(tmp_path, _make_package_files())
    monkeypatch.chdir(tmp_path)

    rc_all = main(["--all", "--json"])
    assert rc_all == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["errors"] == []
    assert payload["packages"] == ["2026-11-18-sample-feature"]

    rc_single = main(["docs/specs/2026-11-18-sample-feature", "--json"])
    assert rc_single == 0
    payload_single = json.loads(capsys.readouterr().out)
    assert payload_single["valid"] is True
    assert payload_single["packages"] == ["2026-11-18-sample-feature"]

    # --stage gate1 on minimal Planning package
    ws_g1 = tmp_path / "g1_cli"
    _write_tree(
        ws_g1,
        _make_package_files(
            status="Planning",
            first_entered="Never",
            include_derived=False,
        ),
    )
    rc_g1 = main([str(ws_g1 / "docs/specs/2026-11-18-sample-feature"), "--stage", "gate1", "--json"])
    assert rc_g1 == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True

    # Invalid package returns exit code 1 and valid=False
    bad_spec = tmp_path / "docs/specs/2026-11-18-sample-feature/spec.md"
    bad_spec.write_text(
        bad_spec.read_text(encoding="utf-8").replace("2026-11-18\n", "Never\n", 1),
        encoding="utf-8",
    )
    rc_fail = main(["--all", "--json"])
    assert rc_fail == 1
    fail_payload = json.loads(capsys.readouterr().out)
    assert fail_payload["valid"] is False
    assert len(fail_payload["errors"]) >= 1


def test_unique_adr_and_boundary_table_shapes(tmp_path: Path) -> None:
    # Single unique ADR must pass (kills >= 1 mutant on duplicate ADR check)
    ws_adr = tmp_path / "unique_adr"
    adr_blk = (
        "## ADR-001: Choice\n\n"
        "- Governs: REQ-001\n"
        "- State: Accepted\n"
        "- Decision: Stdlib.\n\n"
    )
    _write_tree(ws_adr, _make_package_files(adr_block=adr_blk, adr_index="ADR-001"))
    res_adr = validate_workspace(ws_adr)
    assert res_adr["valid"] is True, res_adr["errors"]

    # Direct specs dir missing INDEX.md (exercises resolved.name == "specs" branch)
    specs_only = tmp_path / "empty_ws" / "docs" / "specs"
    specs_only.mkdir(parents=True)
    res_missing_idx = validate_workspace(specs_only)
    assert res_missing_idx["valid"] is False
    assert any("INDEX.md" in e for e in res_missing_idx["errors"])

    # Exact 2-column Gate 1 rows pass (len(row) == 2 with all 6 rows)
    ws_g1_2col = tmp_path / "g1_2col"
    files_2col = _make_package_files()
    pkg = "docs/specs/2026-11-18-sample-feature"
    files_2col[f"{pkg}/decisions.md"] = (
        "# Decisions: Sample feature\n\n"
        "Governing specification: [spec.md](./spec.md)\n\n"
        "## Architectural rationale\n\n"
        "- Governs: REQ-001\n\n"
        "## Gate 1: normative review\n\n"
        "| Check | Status |\n"
        "| --- | --- |\n"
        "| Grounding | PASS |\n"
        "| Intent | PASS |\n"
        "| Criteria | PASS |\n"
        "| Assumptions | PASS |\n"
        "| Rationale | PASS |\n"
        "| IDs | PASS |\n"
    )
    _write_tree(ws_g1_2col, files_2col)
    assert validate_workspace(ws_g1_2col)["valid"] is True

    # 1-column Gate 2 row reports invalid status cleanly with '?' AC fallback
    ws_g2_1col = tmp_path / "g2_1col"
    files_g2_1col = _make_package_files()
    files_g2_1col[f"{pkg}/tasks.md"] = files_g2_1col[f"{pkg}/tasks.md"].replace(
        "\n\n- Backward scope check:",
        "\n| only-one-col |\n\n- Backward scope check:",
    )
    _write_tree(ws_g2_1col, files_g2_1col)
    res_g2_1col = validate_workspace(ws_g2_1col)
    assert res_g2_1col["valid"] is False
    assert any("'?' has invalid status" in e for e in res_g2_1col["errors"])

    # 2-column Gate 2 row maps AC-001-1/2 (len(row) == 2) without missing-row error
    ws_g2_2col = tmp_path / "g2_2col"
    files_g2_2col_exact = _make_package_files()
    files_g2_2col_exact[f"{pkg}/tasks.md"] = (
        "# Tasks: Sample feature\n\n"
        "## Task 1: Implement\n\n"
        "- [x] Done\n"
        "- Covers: REQ-001\n\n"
        "## Gate 2: traceability and readiness\n\n"
        "| Req | AC |\n"
        "| --- | --- |\n"
        "| REQ-001 | AC-001-1 |\n"
        "| REQ-001 | AC-001-2 |\n"
    )
    _write_tree(ws_g2_2col, files_g2_2col_exact)
    res_g2_2col = validate_workspace(ws_g2_2col)
    assert res_g2_2col["valid"] is False
    assert not any("missing Gate 2 row" in e for e in res_g2_2col["errors"])


def test_link_escaping_workspace_root_rejected(tmp_path: Path) -> None:
    # Valid link to repo file inside workspace root (outside docs/) must pass
    ws_ok = tmp_path / "repo_link_ws"
    files_ok = _make_package_files()
    files_ok["src/app.py"] = "def run(count: int) -> bool:\n    return count >= 0\n"
    files_ok["docs/specs/2026-11-18-sample-feature/design.md"] += "\nSee [app](../../../src/app.py).\n"
    _write_tree(ws_ok, files_ok)
    res_ok = validate_workspace(ws_ok)
    assert res_ok["valid"] is True, res_ok["errors"]

    # Link escaping workspace root must fail before filesystem probe
    ws = tmp_path / "escape_ws"
    files = _make_package_files()
    files["docs/specs/2026-11-18-sample-feature/design.md"] += "\nSee [escape](../../../../etc/hosts).\n"
    _write_tree(ws, files)

    res = validate_workspace(ws)
    assert res["valid"] is False
    assert any("escapes workspace root" in e for e in res["errors"]), res["errors"]


def test_gate1_requires_six_rows_and_gate2_requires_summary_bullets(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # 5-row Gate 1 fails
    ws_g1_5 = tmp_path / "g1_five_rows"
    files_5 = _make_package_files()
    dec_lines = files_5[f"{pkg}/decisions.md"].splitlines()
    files_5[f"{pkg}/decisions.md"] = "\n".join(dec_lines[:-1]) + "\n"
    _write_tree(ws_g1_5, files_5)
    res_5 = validate_workspace(ws_g1_5)
    assert res_5["valid"] is False
    assert any("Gate 1" in e and "6" in e for e in res_5["errors"]), res_5["errors"]

    # Missing either Gate 2 summary bullet fails
    for bullet in ("Backward scope check", "Reference and catalog consistency"):
        ws_b = tmp_path / f"missing_{bullet.replace(' ', '_')}"
        files_b = _make_package_files()
        files_b[f"{pkg}/tasks.md"] = "\n".join(
            line for line in files_b[f"{pkg}/tasks.md"].splitlines()
            if not line.startswith(f"- {bullet}:")
        ) + "\n"
        _write_tree(ws_b, files_b)
        res_b = validate_workspace(ws_b)
        assert res_b["valid"] is False
        assert any(f"missing Gate 2 '{bullet}' bullet" in e for e in res_b["errors"]), res_b["errors"]


def test_provisional_blocked_scoped_strictly_to_provisional_items(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-mixed-prov"

    def _build_mixed(ac1_status: str) -> dict[str, str]:
        spec_md = (
            "# Mixed provisional feature\n\n"
            "- Feature ID: 2026-11-18-mixed-prov\n"
            "- Type: enhancement\n"
            "- Status: In-Progress\n"
            "- First entered In-Testing: Never\n"
            "- Related specifications: None\n\n"
            "## Problem and source intent\n\n"
            'User request: "Handle settled REQ-001 and deferred REQ-002."\n\n'
            "## Repository grounding\n\n"
            "Checked `src/app.py`.\n\n"
            "## Non-goals\n\n"
            "- None beyond deferred scope.\n\n"
            "## Requirements\n\n"
            "### REQ-001: Settled requirement\n\n"
            "- Source intent: User request.\n"
            "- Statement: WHEN invoked, THE system SHALL succeed.\n"
            "- AC-001-1 — Success: Returns ok.\n\n"
            "### REQ-002: Deferred requirement [PROVISIONAL]\n\n"
            "- Source intent: User request.\n"
            "- Open question: Timeout value?\n"
            "- Owner deferral: Deferred on 2026-11-18.\n"
            "- Blocked scope: AC-002-1.\n"
            "- Statement: WHEN timed out, THE system SHALL abort.\n"
            "- AC-002-1 — Deferred [PROVISIONAL]: Pending timeout value.\n\n"
            "## Assumptions and owner-deferred questions\n\n"
            "- See REQ-002 [PROVISIONAL].\n\n"
            "## Approvals and lifecycle history\n\n"
            "- 2026-11-18 (`Planning -> In-Progress`): Authorized for REQ-001.\n"
        )
        decisions_md = (
            "# Decisions: Mixed provisional feature\n\n"
            "Governing specification: [spec.md](./spec.md)\n\n"
            "## Architectural rationale\n\n"
            "- Governs: REQ-001, REQ-002\n\n"
            "Constrained.\n\n"
            "## Gate 1: normative review\n\n"
            "| Check | Status | Evidence / required correction |\n"
            "| --- | --- | --- |\n"
            "| Codebase grounding | PASS | Checked `src/app.py`. |\n"
            "| Attributable intent and explicit scope | PASS | Scoped. |\n"
            "| Observable requirements and meaningful acceptance criteria | PASS | REQ-001 observable; REQ-002 reserved. |\n"
            "| Assumptions and owner-deferred questions are explicit | PASS | REQ-002 marked [PROVISIONAL]. |\n"
            "| Architectural rationale respects requirements | PASS | Covers REQ-001, REQ-002. |\n"
            "| IDs, references, and revision route are consistent | PASS | Registered. |\n"
        )
        design_md = (
            "# Design: Mixed provisional feature\n\n"
            "Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)\n\n"
            "## Components\n\n"
            "| Requirement / AC | Path and symbol | Responsibility / change |\n"
            "| --- | --- | --- |\n"
            "| REQ-001, REQ-002 | `src/app.py` | Handle both. |\n\n"
            "## Interfaces and flow\n\n- Flow.\n\n"
            "## Boundaries and recovery\n\n- Boundaries.\n\n"
            "## Dependencies and unresolved design work\n\n- REQ-002 deferred.\n"
        )
        tasks_md = (
            "# Tasks: Mixed provisional feature\n\n"
            "Sources: [spec.md](./spec.md), [design.md](./design.md)\n\n"
            "## Task 1: Implement settled REQ-001\n\n"
            "- [ ] Complete REQ-001.\n"
            "- Covers: REQ-001, REQ-002\n\n"
            "## Gate 2: traceability and readiness\n\n"
            "| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            f"| REQ-001 | AC-001-1 | [Rationale](./decisions.md#architectural-rationale) | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-implement-settled-req-001) | [AC-001-1](./verification.md#ac-001-1-req-001) | {ac1_status} |\n"
            "| REQ-002 | AC-002-1 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-settled-req-001) | [AC-002-1](./verification.md#ac-002-1-req-002) | BLOCKED — awaiting owner |\n\n"
            "- Backward scope check: PASS — scoped.\n"
            "- Reference and catalog consistency: PASS — consistent.\n"
        )
        verification_md = (
            "# Verification: Mixed provisional feature\n\n"
            "Governing specification: [spec.md](./spec.md)\n\n"
            "## Planned checks\n\n"
            "### AC-001-1 (REQ-001)\n\n- Method: Test.\n- Expected outcome: Ok.\n- Execution: Not run.\n\n"
            "### AC-002-1 (REQ-002)\n\n- Method: Blocked pending REQ-002 [PROVISIONAL] resolution.\n- Expected outcome: Abort.\n- Execution: Blocked pending REQ-002 [PROVISIONAL] resolution.\n\n"
            "## Execution evidence\n\nNo checks have been executed.\n\n"
            "## Real-world observations\n\nNo real-world confirmation has been recorded.\n"
        )
        index_md = (
            "# Feature specifications\n\n"
            "| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| 2026-11-18-mixed-prov | Mixed | In-Progress | REQ-001, REQ-002 | None | [spec](./2026-11-18-mixed-prov/spec.md) |\n"
        )
        return {
            "docs/specs/INDEX.md": index_md,
            f"{pkg}/spec.md": spec_md,
            f"{pkg}/decisions.md": decisions_md,
            f"{pkg}/design.md": design_md,
            f"{pkg}/tasks.md": tasks_md,
            f"{pkg}/verification.md": verification_md,
        }

    ws_ok = tmp_path / "mixed_ok"
    _write_tree(ws_ok, _build_mixed("PASS — settled"))
    res_ok = validate_workspace(ws_ok)
    assert res_ok["valid"] is True, res_ok["errors"]

    ws_bad = tmp_path / "mixed_bad"
    _write_tree(ws_bad, _build_mixed("BLOCKED — improperly blocked"))
    res_bad = validate_workspace(ws_bad)
    assert res_bad["valid"] is False
    assert any("AC-001-1" in e and "BLOCKED" in e for e in res_bad["errors"]), res_bad["errors"]

    # Prose mention of [PROVISIONAL] on a settled In-Testing package must NOT false-trigger
    ws_prose = tmp_path / "prose_prov"
    files_prose = _make_package_files(status="In-Testing")
    files_prose["docs/specs/2026-11-18-sample-feature/spec.md"] = files_prose[
        "docs/specs/2026-11-18-sample-feature/spec.md"
    ].replace("None.\n", "Zero [PROVISIONAL] items remain.\n", 1)
    _write_tree(ws_prose, files_prose)
    res_prose = validate_workspace(ws_prose)
    assert res_prose["valid"] is True, res_prose["errors"]


def test_requirements_section_and_per_req_ac_ownership(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # Missing ## Requirements heading
    ws_no_sec = tmp_path / "no_req_sec"
    files_no_sec = _make_package_files()
    files_no_sec[f"{pkg}/spec.md"] = files_no_sec[f"{pkg}/spec.md"].replace(
        "## Requirements\n\n", ""
    )
    _write_tree(ws_no_sec, files_no_sec)
    res_no_sec = validate_workspace(ws_no_sec)
    assert res_no_sec["valid"] is False
    assert any("## Requirements" in e for e in res_no_sec["errors"]), res_no_sec["errors"]

    # Declared REQ-002 with zero AC-002-* criteria
    ws_no_ac = tmp_path / "req_without_ac"
    files_no_ac = _make_package_files()
    files_no_ac["docs/specs/INDEX.md"] = files_no_ac["docs/specs/INDEX.md"].replace(
        "| REQ-001 |", "| REQ-001, REQ-002 |"
    )
    files_no_ac[f"{pkg}/spec.md"] = files_no_ac[f"{pkg}/spec.md"].replace(
        "## Assumptions and owner-deferred questions",
        "### REQ-002: Missing criteria requirement\n\n"
        "- Source intent: User request.\n"
        "- Statement: WHEN called, THE system SHALL log.\n\n"
        "## Assumptions and owner-deferred questions",
    )
    for doc_name in ("decisions.md", "design.md", "tasks.md", "verification.md"):
        files_no_ac[f"{pkg}/{doc_name}"] += "\nNote: REQ-002.\n"
    _write_tree(ws_no_ac, files_no_ac)
    res_no_ac = validate_workspace(ws_no_ac)
    assert res_no_ac["valid"] is False
    assert any("REQ-002 has no declared AC-002-* acceptance criteria" in e for e in res_no_ac["errors"]), res_no_ac["errors"]


def test_link_edge_cases_inline_labels_unquote_slash_dirs_and_io(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # Inline-code link label [`spec.md`](./missing.md) must NOT be bypassed
    ws_inline = tmp_path / "inline_label"
    files_inline = _make_package_files()
    files_inline[f"{pkg}/design.md"] += "\nSee [`spec.md`](./missing.md) and [``double``](./missing2.md).\n"
    _write_tree(ws_inline, files_inline)
    res_inline = validate_workspace(ws_inline)
    assert res_inline["valid"] is False
    assert any("missing.md" in e for e in res_inline["errors"])
    assert any("missing2.md" in e for e in res_inline["errors"])

    # URL-encoded path/anchor, leading-slash workspace-relative path, non-.md #L10 anchor, and dir link
    ws_valid = tmp_path / "link_valid"
    files_valid = _make_package_files()
    files_valid["src/my module.md"] = "# Café\n\nOk.\n"
    files_valid["src/app.py"] = "def run():\n    pass\n"
    files_valid[f"{pkg}/design.md"] += (
        "\nSee [mod](/src/my%20module.md#caf%C3%A9), [line](/src/app.py#L10), and [dir](/src).\n"
    )
    _write_tree(ws_valid, files_valid)
    res_valid = validate_workspace(ws_valid)
    assert res_valid["valid"] is True, res_valid["errors"]

    # Directory link WITH anchor must fail
    ws_dir_anchor = tmp_path / "dir_anchor"
    files_da = _make_package_files()
    files_da["src/sub/file.txt"] = "x"
    files_da[f"{pkg}/design.md"] += "\nSee [dir](/src/sub#sec).\n"
    _write_tree(ws_dir_anchor, files_da)
    res_da = validate_workspace(ws_dir_anchor)
    assert res_da["valid"] is False
    assert any("requires a file target" in e for e in res_da["errors"]), res_da["errors"]

    # Unreadable/non-UTF8 markdown target with anchor handled cleanly
    ws_bad_utf = tmp_path / "bad_utf8"
    files_bu = _make_package_files()
    files_bu[f"{pkg}/design.md"] += "\nSee [bin](./bad.md#head).\n"
    _write_tree(ws_bad_utf, files_bu)
    (ws_bad_utf / pkg / "bad.md").write_bytes(b"\xff\xfe\x00\x00")
    res_bu = validate_workspace(ws_bad_utf)
    assert res_bu["valid"] is False
    assert any("unreadable UTF-8 file" in e for e in res_bu["errors"]), res_bu["errors"]


def test_abandoned_and_workspace_planning_vs_single_target(tmp_path: Path) -> None:
    # Abandoned package with ONLY spec.md + INDEX.md passes workspace & single check
    ws = tmp_path / "lifecycle_ws"
    ab_files = _make_package_files(
        feature_id="2026-11-10-abandoned-idea",
        status="Abandoned",
        first_entered="Never",
        req_id="REQ-001",
        include_derived=False,
    )
    del ab_files["docs/specs/2026-11-10-abandoned-idea/decisions.md"]

    # Planning package in workspace with only spec.md + UNCHECKED decisions.md
    plan_files = _make_package_files(
        feature_id="2026-11-18-in-draft",
        status="Planning",
        first_entered="Never",
        req_id="REQ-002",
        ac_num="002",
        gate1_status="UNCHECKED",
        include_derived=False,
    )

    combined_index = (
        "# Feature specifications\n\n"
        "| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 2026-11-10-abandoned-idea | Old | Abandoned | REQ-001 | None | [spec](./2026-11-10-abandoned-idea/spec.md) |\n"
        "| 2026-11-18-in-draft | Draft | Planning | REQ-002 | None | [spec](./2026-11-18-in-draft/spec.md) |\n"
    )
    _write_tree(ws, {**ab_files, **plan_files, "docs/specs/INDEX.md": combined_index})

    # Workspace-wide sweep passes for Abandoned + Planning
    res_ws = validate_workspace(ws)
    assert res_ws["valid"] is True, res_ws["errors"]

    # CLI --all with a single package path honours --all and sweeps whole workspace
    assert main([str(ws / "docs/specs/2026-11-18-in-draft"), "--all"]) == 0

    # Targeting the Planning package directly still enforces --stage gate1 / full readiness
    res_single_g1 = validate_workspace(ws / "docs/specs/2026-11-18-in-draft", stage="gate1")
    assert res_single_g1["valid"] is False
    assert any("Gate 1" in e for e in res_single_g1["errors"])

    # Abandoned single-package check still passes
    res_single_ab = validate_workspace(ws / "docs/specs/2026-11-10-abandoned-idea")
    assert res_single_ab["valid"] is True, res_single_ab["errors"]


def test_p2_polish_html_dup_adr_missing_index_and_verification_runs(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # P2-1: HTML comments and safe HTML tags ignored
    ws_html = tmp_path / "html_ok"
    files_html = _make_package_files()
    files_html[f"{pkg}/design.md"] += (
        "\n<!-- <template-note> TODO FIXME -->\n"
        '<div class="note"><span>ok</span><img src="x" /></div>\n'
    )
    _write_tree(ws_html, files_html)
    assert validate_workspace(ws_html)["valid"] is True

    # P2-2: Intra-package duplicate ADR-001 rejected
    ws_dup_adr = tmp_path / "dup_adr"
    dup_adr_blk = (
        "## ADR-001: First\n\n- Governs: REQ-001\n- State: Accepted\n\n"
        "## ADR-001: Duplicate\n\n- Governs: REQ-001\n- State: Accepted\n\n"
    )
    _write_tree(ws_dup_adr, _make_package_files(adr_block=dup_adr_blk, adr_index="ADR-001"))
    res_dup_adr = validate_workspace(ws_dup_adr)
    assert res_dup_adr["valid"] is False
    assert any("duplicate ADR-NNN" in e for e in res_dup_adr["errors"]), res_dup_adr["errors"]

    # P2-4: Package dir whose parent lacks INDEX.md reports Missing catalog file
    ws_no_idx = tmp_path / "no_idx"
    files_ni = _make_package_files()
    del files_ni["docs/specs/INDEX.md"]
    _write_tree(ws_no_idx, files_ni)
    res_ni = validate_workspace(ws_no_idx / pkg)
    assert res_ni["valid"] is False
    assert any("Missing catalog file" in e for e in res_ni["errors"])

    # P2-5: Broadened PROVISIONAL_AC_RE (`- AC-001-2: [PROVISIONAL]`)
    ws_prov_ac = tmp_path / "prov_ac_short"
    files_pa = _make_package_files(status="In-Progress", first_entered="Never", task_checked=False)
    files_pa[f"{pkg}/spec.md"] = files_pa[f"{pkg}/spec.md"].replace(
        "- AC-001-2 — Boundary/failure: Raises ValueError on negative count.",
        "- AC-001-2: [PROVISIONAL] Deferred boundary.",
    )
    files_pa[f"{pkg}/tasks.md"] = files_pa[f"{pkg}/tasks.md"].replace(
        "| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-001-2](./verification.md#ac-001-2-req-001) | PASS — verified mapping |",
        "| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-001-2](./verification.md#ac-001-2-req-001) | BLOCKED — deferred |",
    )
    _write_tree(ws_prov_ac, files_pa)
    assert validate_workspace(ws_prov_ac)["valid"] is True

    # P2-6: Header-only Gate 1 table followed by another table does not bleed into 6 rows
    ws_hdr_only = tmp_path / "hdr_only"
    files_ho = _make_package_files()
    files_ho[f"{pkg}/decisions.md"] = (
        "# Decisions: Sample feature\n\n"
        "Governing specification: [spec.md](./spec.md)\n\n"
        "## Architectural rationale\n\n- Governs: REQ-001\n\n"
        "## Gate 1: normative review\n\n"
        "| Check | Status | Evidence |\n"
        "| --- | --- | --- |\n\n"
        "Extra table:\n\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | PASS |\n| 2 | PASS |\n| 3 | PASS |\n| 4 | PASS |\n| 5 | PASS |\n| 6 | PASS |\n"
    )
    _write_tree(ws_hdr_only, files_ho)
    res_ho = validate_workspace(ws_hdr_only)
    assert res_ho["valid"] is False
    assert any("missing Gate 1 table rows" in e for e in res_ho["errors"]), res_ho["errors"]

    # P2-7: `Execution: Not run` (no period) and latest Run containing `FAIL` rejected; Run 1 FAIL + Run 2 PASS accepted
    ws_not_run = tmp_path / "not_run_no_dot"
    _write_tree(ws_not_run, _make_package_files(status="In-Testing", execution_ref="Not run"))
    res_nr = validate_workspace(ws_not_run)
    assert res_nr["valid"] is False
    assert any("Not run" in e for e in res_nr["errors"])

    ws_fail_latest = tmp_path / "fail_latest"
    _write_tree(
        ws_fail_latest,
        _make_package_files(
            status="In-Testing",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-2 `FAIL`\n"
            ),
        ),
    )
    res_fl = validate_workspace(ws_fail_latest)
    assert res_fl["valid"] is False
    assert any("FAIL" in e for e in res_fl["errors"])

    ws_fail_then_pass = tmp_path / "fail_then_pass"
    _write_tree(
        ws_fail_then_pass,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 2](#run-2--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-2 `FAIL`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `PASS`\n"
            ),
        ),
    )
    assert validate_workspace(ws_fail_then_pass)["valid"] is True


def test_round2_utf8_planned_checks_results_dotpkg_gfm_pipes_and_git_root(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # R2-P1-2: Unreadable UTF-8 INDEX.md and spec.md fail cleanly without raising
    ws_utf_idx = tmp_path / "utf_idx"
    _write_tree(ws_utf_idx, _make_package_files())
    (ws_utf_idx / "docs/specs/INDEX.md").write_bytes(b"\xff\xfe")
    res_ui = validate_workspace(ws_utf_idx)
    assert res_ui["valid"] is False
    assert any("unreadable UTF-8 file" in e for e in res_ui["errors"])

    ws_utf_spec = tmp_path / "utf_spec"
    _write_tree(ws_utf_spec, _make_package_files())
    (ws_utf_spec / pkg / "spec.md").write_bytes(b"\xff\xfe")
    res_us = validate_workspace(ws_utf_spec)
    assert res_us["valid"] is False
    assert any("unreadable UTF-8 file" in e for e in res_us["errors"])

    # R2-P1-3: Missing/empty ## Planned checks fails; stray Execution: Not run outside Planned checks fails
    ws_no_pc = tmp_path / "no_planned_checks"
    files_npc = _make_package_files(
        status="Planning",
        first_entered="Never",
        task_checked=False,
        execution_ref="Not run.",
        execution_evidence="No checks have been executed.",
    )
    files_npc[f"{pkg}/verification.md"] = (
        "# Verification: Sample feature\n\n"
        "Governing specification: [spec.md](./spec.md)\n\n"
        "### AC-001-1 (REQ-001)\n\n- Method: Test.\n\n"
        "### AC-001-2 (REQ-001)\n\n- Method: Test.\n\n"
        "## Execution evidence\n\nNo checks have been executed.\n"
    )
    _write_tree(ws_no_pc, files_npc)
    res_npc = validate_workspace(ws_no_pc / pkg)
    assert res_npc["valid"] is False
    assert any("Planned checks" in e for e in res_npc["errors"]), res_npc["errors"]

    ws_stray_nr = tmp_path / "stray_not_run"
    files_snr = _make_package_files(status="In-Testing")
    files_snr[f"{pkg}/verification.md"] += "\n- Execution: Not run\n"
    _write_tree(ws_stray_nr, files_snr)
    res_snr = validate_workspace(ws_stray_nr)
    assert res_snr["valid"] is False
    assert any("Not run" in e for e in res_snr["errors"])

    # R2-P1-4: Unbackticked FAIL, BLOCKED, and missing Result line in latest Run rejected
    for label, ev_body in (
        ("bare_fail", "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 FAIL\n"),
        ("bare_blocked", "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 PASS, AC-001-2 BLOCKED\n"),
        ("missing_result", "### Run 1 — 2026-11-18\n\n- Command: `pytest`\n"),
    ):
        ws_r = tmp_path / f"res_{label}"
        _write_tree(ws_r, _make_package_files(status="In-Testing", execution_evidence=ev_body))
        res_r = validate_workspace(ws_r)
        assert res_r["valid"] is False, f"{label} should fail"
        assert any("Result" in e for e in res_r["errors"]), res_r["errors"]

    # R2-P2-1: Explicitly targeting dot-prefixed package validates it
    ws_dot = tmp_path / "dot_pkg"
    dot_files = _make_package_files(feature_id=".draft", status="In-Testing", first_entered="Never")
    _write_tree(ws_dot, dot_files)
    res_dot = validate_workspace(ws_dot / "docs/specs/.draft")
    assert res_dot["valid"] is False
    assert res_dot["packages"] == [".draft"]
    assert any("First entered In-Testing" in e for e in res_dot["errors"])

    # R2-P2-2: GFM pipe rows without trailing pipe parse properly
    ws_pipe = tmp_path / "no_trailing_pipe"
    files_pipe = _make_package_files()
    files_pipe[f"{pkg}/decisions.md"] = (
        "# Decisions: Sample feature\n\n"
        "Governing specification: [spec.md](./spec.md)\n\n"
        "## Architectural rationale\n\n- Governs: REQ-001\n\n"
        "## Gate 1: normative review\n\n"
        "| Check | Status\n"
        "| --- | ---\n"
        "| 1 | PASS\n| 2 | PASS\n| 3 | PASS\n| 4 | PASS\n| 5 | PASS\n| 6 | PASS\n"
    )
    _write_tree(ws_pipe, files_pipe)
    assert validate_workspace(ws_pipe)["valid"] is True

    # R2-P2-5: .git ancestor marks workspace_root even for nested packages/api/docs/specs
    ws_git = tmp_path / "monorepo"
    (ws_git / ".git").mkdir(parents=True)
    nested_files = {f"packages/api/{k}": v for k, v in _make_package_files().items()}
    nested_files["README.md"] = "# Monorepo\n"
    nested_files["packages/api/docs/specs/2026-11-18-sample-feature/design.md"] += "\nSee [root](/README.md).\n"
    _write_tree(ws_git, nested_files)
    res_git = validate_workspace(ws_git / "packages/api/docs/specs")
    assert res_git["valid"] is True, res_git["errors"]


def test_round3_workspace_planning_gates_provisional_acs_comments_dups_and_slugs(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # R3-P1-1: Workspace-wide Planning package allows UNCHECKED Gate 1/2/bullets, rejects FAIL
    ws_plan_ok = tmp_path / "ws_plan_ok"
    _write_tree(
        ws_plan_ok,
        _make_package_files(
            status="Planning",
            first_entered="Never",
            gate1_status="UNCHECKED",
            gate2_status="UNCHECKED",
            gate2_extra_status="UNCHECKED",
            task_checked=False,
            execution_ref="Not run.",
            execution_evidence="No checks have been executed.",
        ),
    )
    res_po = validate_workspace(ws_plan_ok)
    assert res_po["valid"] is True, res_po["errors"]

    for fail_target, overrides in (
        ("Gate 1", {"gate1_status": "FAIL"}),
        ("Gate 2", {"gate2_status": "FAIL"}),
        ("Backward scope", {"gate2_extra_status": "FAIL"}),
    ):
        ws_plan_fail = tmp_path / f"ws_plan_fail_{fail_target.replace(' ', '_')}"
        _write_tree(
            ws_plan_fail,
            _make_package_files(
                status="Planning",
                first_entered="Never",
                task_checked=False,
                execution_ref="Not run.",
                execution_evidence="No checks have been executed.",
                **overrides,
            ),
        )
        res_pf = validate_workspace(ws_plan_fail)
        assert res_pf["valid"] is False, f"{fail_target} FAIL should fail even in workspace Planning"
        assert any("FAIL" in e for e in res_pf["errors"]), res_pf["errors"]

    # R3-P1-2: Provisional AC cannot be PASS; settled AC under provisional REQ can be PASS
    ws_prov_pass = tmp_path / "prov_ac_pass"
    _write_tree(
        ws_prov_pass,
        _make_package_files(
            status="In-Progress",
            first_entered="Never",
            provisional=True,
            gate2_status="PASS — invalid on deferred AC",
            task_checked=False,
            execution_ref="Not run.",
            execution_evidence="No checks have been executed.",
        ),
    )
    res_pp = validate_workspace(ws_prov_pass)
    assert res_pp["valid"] is False
    assert any("AC-001-2" in e and "PASS" in e for e in res_pp["errors"]), res_pp["errors"]

    # Settled AC-001-1 PASS + Deferred AC-001-2 BLOCKED under REQ-001 [PROVISIONAL] passes
    ws_prov_split = tmp_path / "prov_split_ok"
    files_ps = _make_package_files(
        status="In-Progress",
        first_entered="Never",
        provisional=True,
        gate2_status="PASS — settled AC",
        task_checked=False,
        execution_ref="Not run.",
        execution_evidence="No checks have been executed.",
    )
    files_ps[f"{pkg}/tasks.md"] = files_ps[f"{pkg}/tasks.md"].replace(
        "| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-001-2](./verification.md#ac-001-2-req-001) | PASS — settled AC |",
        "| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-001-2](./verification.md#ac-001-2-req-001) | BLOCKED — deferred |",
    )
    _write_tree(ws_prov_split, files_ps)
    assert validate_workspace(ws_prov_split)["valid"] is True

    # R3-P2-1: Commented-out broken link ignored
    ws_comment_link = tmp_path / "comment_link"
    files_cl = _make_package_files()
    files_cl[f"{pkg}/design.md"] += "\n<!-- [broken](./does-not-exist.md) -->\n"
    _write_tree(ws_comment_link, files_cl)
    assert validate_workspace(ws_comment_link)["valid"] is True

    # R3-P2-2: Duplicate INDEX.md row rejected
    ws_dup_idx = tmp_path / "dup_idx"
    files_di = _make_package_files()
    idx_lines = files_di["docs/specs/INDEX.md"].strip().splitlines()
    files_di["docs/specs/INDEX.md"] = "\n".join([*idx_lines, idx_lines[-1]]) + "\n"
    _write_tree(ws_dup_idx, files_di)
    res_di = validate_workspace(ws_dup_idx)
    assert res_di["valid"] is False
    assert any("duplicate catalog entry" in e for e in res_di["errors"]), res_di["errors"]

    # R3-P2-3: Specs root containing both INDEX.md and stray spec.md resolves as specs root
    ws_stray = tmp_path / "stray_spec"
    files_st = _make_package_files()
    files_st["docs/specs/spec.md"] = "# Stray\n"
    _write_tree(ws_stray, files_st)
    res_st = validate_workspace(ws_stray / "docs/specs")
    assert res_st["valid"] is True, res_st["errors"]

    # R3-P2-4: heading_slug strips HTML tags and replaces tabs with spaces -> '-'
    assert heading_slug("Title <span>tag</span>\there") == "title-tag-here"

    # R3-P2-5: Intra-package duplicate REQ-001 headings rejected
    ws_dup_req = tmp_path / "dup_req_intra"
    files_dr = _make_package_files()
    files_dr[f"{pkg}/spec.md"] = files_dr[f"{pkg}/spec.md"].replace(
        "## Assumptions and owner-deferred questions",
        "### REQ-001: Duplicate inside same spec\n\n- AC-001-3 — Success: Dup.\n\n## Assumptions and owner-deferred questions",
    )
    _write_tree(ws_dup_req, files_dr)
    res_dr = validate_workspace(ws_dup_req)
    assert res_dr["valid"] is False
    assert any("duplicate REQ-NNN" in e for e in res_dr["errors"]), res_dr["errors"]


def test_round4_per_ac_runs_gate2_phantom_and_verified_approvals(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # R4-P1-1(a): Partial Run 2 (AC-001-1 PASS) leaving AC-001-2 failing in Run 1 is rejected
    ws_partial = tmp_path / "partial_run2"
    _write_tree(
        ws_partial,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 2](#run-2--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `FAIL`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-1 `PASS`\n"
            ),
        ),
    )
    res_part = validate_workspace(ws_partial)
    assert res_part["valid"] is False
    assert any("AC-001-2" in e and "FAIL" in e for e in res_part["errors"]), res_part["errors"]

    # R4-P1-1(b): Run 1 (AC-001-1 PASS, AC-001-2 FAIL) + Run 2 (AC-001-2 PASS) with matching Execution links passes
    ws_split_ok = tmp_path / "split_runs_ok"
    files_so = _make_package_files(
        status="In-Testing",
        execution_ref="[Run 1](#run-1--2026-11-18)",
        execution_evidence=(
            "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `FAIL`\n\n"
            "### Run 2 — 2026-11-18\n\n- Result: AC-001-2 `PASS`\n"
        ),
    )
    files_so[f"{pkg}/verification.md"] = files_so[f"{pkg}/verification.md"].replace(
        "### AC-001-2 (REQ-001)\n\n"
        "- Method: Unit test with `count=-1`.\n"
        "- Expected outcome: Raises `ValueError`.\n"
        "- Execution: [Run 1](#run-1--2026-11-18)",
        "### AC-001-2 (REQ-001)\n\n"
        "- Method: Unit test with `count=-1`.\n"
        "- Expected outcome: Raises `ValueError`.\n"
        "- Execution: [Run 2](#run-2--2026-11-18)",
    )
    _write_tree(ws_split_ok, files_so)
    assert validate_workspace(ws_split_ok)["valid"] is True

    # R4-P1-1(b): Linking AC-001-2 Execution to Run 1 (which recorded FAIL for AC-001-2) is rejected
    ws_stale_link = tmp_path / "stale_exec_link"
    _write_tree(
        ws_stale_link,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 1](#run-1--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `FAIL`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-2 `PASS`\n"
            ),
        ),
    )
    res_sl = validate_workspace(ws_stale_link)
    assert res_sl["valid"] is False
    assert any("AC-001-2" in e and "run-1--2026-11-18" in e for e in res_sl["errors"]), res_sl["errors"]

    # R4-P1-1 fallback: Run-level Result without AC tokens (PASS passes, FAIL fails)
    ws_fb_ok = tmp_path / "fb_ok"
    _write_tree(
        ws_fb_ok,
        _make_package_files(
            status="In-Testing",
            execution_evidence="### Run 1 — 2026-11-18\n\n- Result: All planned checks PASS.\n",
        ),
    )
    assert validate_workspace(ws_fb_ok)["valid"] is True

    ws_fb_fail = tmp_path / "fb_fail"
    _write_tree(
        ws_fb_fail,
        _make_package_files(
            status="In-Testing",
            execution_evidence="### Run 1 — 2026-11-18\n\n- Result: Suite FAIL.\n",
        ),
    )
    assert validate_workspace(ws_fb_fail)["valid"] is False

    # R4-P2-2: Gate 2 phantom AC and mismatched REQ-AC rows rejected
    ws_phantom = tmp_path / "g2_phantom"
    files_ph = _make_package_files()
    files_ph[f"{pkg}/tasks.md"] = files_ph[f"{pkg}/tasks.md"].replace(
        "\n\n- Backward scope check:",
        "\n| REQ-001 | AC-001-9 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-implement-validation) | [AC-001-2](./verification.md#ac-001-2-req-001) | PASS |\n\n- Backward scope check:",
    )
    _write_tree(ws_phantom, files_ph)
    res_ph = validate_workspace(ws_phantom)
    assert res_ph["valid"] is False
    assert any("phantom AC 'AC-001-9'" in e for e in res_ph["errors"]), res_ph["errors"]

    ws_mismatch = tmp_path / "g2_mismatch"
    files_mm = _make_package_files()
    files_mm[f"{pkg}/tasks.md"] = files_mm[f"{pkg}/tasks.md"].replace(
        "| REQ-001 | AC-001-2 |", "| REQ-002 | AC-001-2 |"
    )
    _write_tree(ws_mismatch, files_mm)
    res_mm = validate_workspace(ws_mismatch)
    assert res_mm["valid"] is False
    assert any("REQ-002" in e and "AC-001-2" in e for e in res_mm["errors"]), res_mm["errors"]

    # R4-P2-3: Verified with default or empty Approvals and lifecycle history rejected
    ws_ver_default = tmp_path / "ver_default_hist"
    files_vd = _make_package_files(
        status="Verified",
        real_world_obs="Confirmed in production by Sam.",
    )
    files_vd[f"{pkg}/spec.md"] = files_vd[f"{pkg}/spec.md"].replace(
        "- 2026-11-18 (`Planning -> Verified`): Approved for test.",
        "No approval or lifecycle transition has been recorded yet.",
    )
    _write_tree(ws_ver_default, files_vd)
    res_vd = validate_workspace(ws_ver_default)
    assert res_vd["valid"] is False
    assert any("Approvals and lifecycle history" in e for e in res_vd["errors"]), res_vd["errors"]


def test_round5_fallback_order_qualified_run_links_dup_runs_and_paren_links(tmp_path: Path) -> None:
    pkg = "docs/specs/2026-11-18-sample-feature"

    # R5-P1-1: Run 1 fallback FAIL -> Run 2 per-AC PASS accepted
    ws_fb_recovered = tmp_path / "fb_recovered"
    _write_tree(
        ws_fb_recovered,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 2](#run-2--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: Suite FAIL.\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `PASS`\n"
            ),
        ),
    )
    assert validate_workspace(ws_fb_recovered)["valid"] is True

    # R5-P1-1: Run 1 per-AC PASS -> Run 2 fallback FAIL rejected
    ws_fb_regressed = tmp_path / "fb_regressed"
    _write_tree(
        ws_fb_regressed,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 1](#run-1--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `PASS`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: Regression suite FAIL.\n"
            ),
        ),
    )
    assert validate_workspace(ws_fb_regressed)["valid"] is False

    # R5-P2-1: Path-qualified ./verification.md#run-1--2026-11-18 pointing to failed Run 1 rejected
    ws_qual_link = tmp_path / "qual_run_link"
    _write_tree(
        ws_qual_link,
        _make_package_files(
            status="In-Testing",
            execution_ref="[Run 1](./verification.md#run-1--2026-11-18)",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `FAIL`\n\n"
                "### Run 2 — 2026-11-18\n\n- Result: AC-001-2 `PASS`\n"
            ),
        ),
    )
    res_ql = validate_workspace(ws_qual_link)
    assert res_ql["valid"] is False
    assert any("AC-001-2" in e and "run-1--2026-11-18" in e for e in res_ql["errors"]), res_ql["errors"]

    # R5-P2-1: Duplicate ### Run heading slug rejected
    ws_dup_run = tmp_path / "dup_run_heading"
    _write_tree(
        ws_dup_run,
        _make_package_files(
            status="In-Testing",
            execution_evidence=(
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `PASS`\n\n"
                "### Run 1 — 2026-11-18\n\n- Result: AC-001-1 `PASS`, AC-001-2 `PASS`\n"
            ),
        ),
    )
    res_dr = validate_workspace(ws_dup_run)
    assert res_dr["valid"] is False
    assert any("duplicate execution run heading slug" in e for e in res_dr["errors"]), res_dr["errors"]

    # R5-P2-2: Balanced parentheses in link destination (notes(1).md) accepted, missing(1).md rejected
    ws_paren = tmp_path / "paren_link"
    files_pr = _make_package_files()
    files_pr[f"{pkg}/notes(1).md"] = "# Notes\n\nOk.\n"
    files_pr[f"{pkg}/design.md"] += "\nSee [notes](./notes(1).md).\n"
    _write_tree(ws_paren, files_pr)
    assert validate_workspace(ws_paren)["valid"] is True

    ws_paren_bad = tmp_path / "paren_link_bad"
    files_pb = _make_package_files()
    files_pb[f"{pkg}/design.md"] += "\nSee [missing](./missing(1).md).\n"
    _write_tree(ws_paren_bad, files_pb)
    res_pb = validate_workspace(ws_paren_bad)
    assert res_pb["valid"] is False
    assert any("missing(1).md" in e for e in res_pb["errors"]), res_pb["errors"]







