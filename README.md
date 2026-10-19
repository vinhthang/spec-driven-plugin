# Spec-Driven Plugin

Mechanical specification governance, 5-Document Architecture enforcement, and Opus-backed semantic traceability verification for Google Antigravity.

---

## Architecture Overview

`spec-driven-plugin` enforces the **5-Document Architecture** across repositories containing `docs/specs/INDEX.md`:

1. **`spec.md`**: Normative requirements (`REQ-\d+`, `FLOW-\d+`, `ALIGN-\d+`) and testable acceptance criteria (`AC-xxx`).
2. **`decisions.md`**: Architecture Decision Records (`ADR-\d+`) capturing explicit design rationale.
3. **`design.md`**: Revisable architectural blueprint mapping every declared requirement ID.
4. **`tasks.md`**: Actionable implementation checklist mapped to requirement IDs.
5. **`verification.md`**: Verbatim test execution and line-count evidence recorded during Phase 2 verification.

### Two-Stage Verification Pipeline

| Stage | Engine | Latency | Responsibility |
| :--- | :--- | :--- | :--- |
| **Stage 1: Structural & Syntax Check** | `scripts/spec_checker.py` (Python) | `~5ms` | Validates 6-column `INDEX.md` table (with escaped pipe `\|` support), path traversal & root containment (`resolve_package_dir`), non-empty 4-document planning baseline, and declared requirement ID citations across documents. |
| **Stage 2: Semantic Traceability Audit** | `agents/traceability-auditor.md` (Opus) / `scripts/semantic_checker.py` | Cached via SHA-256 (`<1ms` hook check) | Evaluates whether `design.md` substantively designs each `REQ-xxx`, `tasks.md` defines actionable work, `decisions.md` is consistent, and `verification.md` proves acceptance criteria. Writes `<package_dir>/traceability_audit.json` keyed by `spec_hash` and `evidence_hash`. |

---

## Components

### 1. Pre-Tool Mechanical Gate (`scripts/spec-gate.py` & `hooks.json`)
Intercepts `invoke_subagent`, `write_to_file`, `replace_file_content`, and `multi_replace_file_content`:
- **Multi-Workspace & `workspacePaths` Resolution**: Resolves the governing workspace root from `payload["workspacePaths"]`, `AGY_ACTIVE_WORKSPACE`, `payload["cwd"]`, or target file ancestors (`.git` / `docs/specs`).
- **Specification Authoring Exemption**: Allows creating and editing files under `docs/specs/` during Phase 1 planning.
- **Anti-Self-Approval & Semantic Promotion Gate**: Blocks promoting a feature to `Approved`, `In-Progress`, or `Active` in `docs/specs/INDEX.md` unless:
  1. Explicit human approval (`"Proceed"` / `"Approved"`) is recorded in the latest `USER_INPUT` step of `transcriptPath` (or `SPEC_GATE_ALLOW_APPROVAL=1`), **and**
  2. `<package_dir>/traceability_audit.json` passes `validate_semantic_traceability()` with an Opus/high-reasoning auditor model (`flash` is mechanically rejected).
- **Subagent Model Guard**: Allows `traceability-auditor` (`TypeName="traceability-auditor"`) to run during Phase 1 planning, but denies dispatch if `Model` is set to `"flash"` or `"flash_lite"`.

### 2. Specification & Semantic Checker (`scripts/spec_checker.py` & `scripts/semantic_checker.py`)
```bash
python3 scripts/spec_checker.py --workspace . [--feature <id>] [--allow-planning] [--verify-evidence] [--semantic] [--json]
```
- `--allow-planning`: Accepts `Draft`, `Planning`, and `Review` statuses during Phase 1.
- `--verify-evidence`: Requires `verification.md` and validates `evidence_hash` in `traceability_audit.json` when present.
- `--semantic`: Enforces `validate_semantic_traceability()` (and invokes the configured CLI agent if `traceability_audit.json` is missing).

### 3. Rules, Skills & Agents
- [`rules/spec-standard.md`](rules/spec-standard.md): Authoritative `spec-standard` governance rule.
- [`skills/spec-standard/SKILL.md`](skills/spec-standard/SKILL.md): Templates and scaling switches for the 5-Document Architecture.
- [`agents/traceability-auditor.md`](agents/traceability-auditor.md): Opus-tier (`model_role: strongest`) subagent that audits specification packages and writes `traceability_audit.json`.

---

## Running Tests

```bash
rtk pytest -v
```
