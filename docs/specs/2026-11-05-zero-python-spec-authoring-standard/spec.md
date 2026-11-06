# Specification: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- **Feature ID**: `2026-11-05-zero-python-spec-authoring-standard`
- **Status**: `In-Testing`
- **Version**: `1.0.0`
- **Sign-off**: `Human "Proceed" approval granted by User on 2026-11-05 ("The user has approved this document — Proceed"); In-Testing dogfooding initiated by User on 2026-11-06 ("I restarted, can you test this spec one time / or at least review it").`
- **Lineage**:
  - **Extends / Modifies**: `None`
  - **Supersedes**:
    - [`2026-10-18-true-spec-driven-enforcement`](../2026-10-18-true-spec-driven-enforcement/spec.md) (`REQ-001` – `REQ-008`, `ADR-001` – `ADR-006`)
    - [`2026-10-19-simplification-and-deduplication`](../2026-10-19-simplification-and-deduplication/spec.md) (`REQ-009` – `REQ-017`, `ADR-007` – `ADR-012` [`Tier-Aware Auditor Policy`])
    - [`2026-10-19-sdd-lifecycle-and-ears-evolution`](../2026-10-19-sdd-lifecycle-and-ears-evolution/spec.md) (`REQ-018` – `REQ-022`, `ADR-012` [`Normalize Volatile tasks.md Checkboxes`] – `ADR-014`)
    - [`2026-10-20-harness2-artifact-gate-and-auditor-tools`](../2026-10-20-harness2-artifact-gate-and-auditor-tools/spec.md) (`REQ-023` – `REQ-028`, `ADR-015` – `ADR-019`)
    - [`2026-10-30-adversarial-adr-debate-and-spec-gate-hardening`](../2026-10-30-adversarial-adr-debate-and-spec-gate-hardening/spec.md) (`REQ-029` – `REQ-033`, `ADR-020` – `ADR-024`)

## 1. Problem Statement & User Intent

### 1.1 Observed Repository Facts
Prior to this specification (`REQ-001` – `REQ-033`), `spec-driven-plugin` enforced specification compliance via a Python hook and checker pipeline consisting of `hooks.json`, three Python scripts (`scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`), three Python test suites (`tests/test_spec_checker.py`, `tests/test_spec_gate.py`, `tests/test_spec_gate_security.py`), and a subagent manifest (`agents/traceability-auditor.md`).

### 1.2 Authorizing User Intent (Verbatim)
1. **Focus on Specification Authoring Quality Over Python Machinery**:
   - *"I only care about how to write a good spec, right? if a model make a bad spec, then I will not use it"*
   - *"that is right, let have a plan to rewrite this plugin or better, a skill, I think we do not need any python code in this"*
2. **Two-Stage Self-Validation Before Deriving Downstream Files**:
   - *"because there is no python code, before write the deriver files (design, tasks, verification), there must be a self validation again the spec, right?"*
3. **Cross-Spec References, Modifications & Supersession**:
   - *"and a spec could refer to other spec, as this is a change, or modification"*
4. **Post-Coding Testing Lifecycle & Bug Decision Protocol**:
   - *"I also do not think a spec is done if you finish, it still need some using or testing"*
   - *"what is the decision when there is bug?"*

## 2. Non-Goals (Out of Scope)
- **Mechanical `PreToolUse` Tool Interception**: The plugin does not intercept IDE file-writing or shell-execution tool calls via `hooks.json` or Python scripts, nor does it generate `traceability_audit.json` receipt files for new specifications.
- **Unattended Autonomous Approval**: The plugin does not auto-approve specifications; transitioning a specification from `Planning` to `In-Progress` or from `In-Testing` to `Verified` always requires explicit human confirmation in conversation.
- **Application Source-File Line-Count Caps**: The plugin does not impose line-count limits on application source files in consumer repositories.

## 3. Normative Requirements (EARS Syntax)

### `REQ-034` [`NEW`]: Zero-Python Declarative Markdown Plugin Surface & Legacy CLI Retirement
- **Source Intent**: Verbatim user prompt (`"that is right, let have a plan to rewrite this plugin or better, a skill, I think we do not need any python code in this"`).
- **Statement**: WHEN `spec-driven-plugin` is packaged in this repository, THE repository SHALL deliver its specification governance and authoring guidance solely through declarative plugin metadata (`plugin.json`), Markdown rules (`rules/*.md`), and Markdown skills (`skills/**/SKILL.md`) alongside repository documentation (`README.md`, `docs/specs/**`), SHALL contain zero Python source or bytecode files (`*.py`, `*.pyc`, `__pycache__/`) and zero hook or subagent manifests (`hooks.json`, `agents/*.md`) anywhere in the repository tree, and SHALL document the retirement and migration path for legacy CLI/hook consumers (`scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, `traceability_audit.json`).
- **Acceptance Criteria**:
  - `AC-034-1` (Happy Path — Zero-Python Surface & Legacy Migration Documentation): A full-depth filesystem listing of the repository (`find . -not -path '*/.git*'`) confirms `plugin.json`, `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `README.md`, and `docs/specs/**` exist, `agy plugin validate` passes with `1` skill processed and `0` hooks/agents, and `README.md` plus `docs/specs/INDEX.md` document the migration from retired `v1.x` CLI/hook surfaces (`spec_checker.py --init/--close`, `hooks.json`, `traceability_audit.json`) to the `v2.0` Markdown `Gate 1` and `Gate 2` tables.
  - `AC-034-2` (Error / Boundary Case — Prohibition of Forbidden Executable & Hook Artifacts): IF any `*.py`, `*.pyc`, `__pycache__/`, `hooks.json`, or `agents/*.md` file is present anywhere in the repository tree (or if a `v2.0` specification package under `docs/specs/2026-11-05-*` relies on `traceability_audit.json` instead of inline Gate 1/Gate 2 tables), THEN `AC-034-2` fails and the specification SHALL NOT enter `In-Testing` or `Verified` until the forbidden artifact is removed.

### `REQ-035` [`NEW`]: Two-Stage Self-Validation Gate with Written Verification Tables
- **Source Intent**: Verbatim user prompt (`"because there is no python code, before write the deriver files (design, tasks, verification), there must be a self validation again the spec, right?"`).
- **Statement**: WHEN authoring a new specification or updating the Normative Source / Derived Blueprint of an existing specification in `docs/specs/<feature-id>/`, THE agent SHALL treat `spec.md` and `decisions.md` as the **Normative Source** and `design.md`, `tasks.md`, and `verification.md` as **Derived Files**, SHALL execute **Gate 1 (Normative Source Self-Validation)** and record a completed 6-row `## Gate 1: Normative Source Self-Validation` table in `decisions.md` before authoring or updating `design.md`, `tasks.md`, or `verification.md`, and SHALL execute **Gate 2 (Derived File Self-Validation)** and record a completed per-AC `## Gate 2: Derived File Self-Validation & Traceability Matrix` table in `tasks.md` before requesting human `"Proceed"` approval.
- **Acceptance Criteria**:
  - `AC-035-1` (Happy Path — Written Gate 1 & Per-AC Gate 2 Tables Complete):
    - `decisions.md` contains a completed `## Gate 1: Normative Source Self-Validation` table recording `PASS` and concrete evidence across all 6 checks: (1) Codebase Grounding, (2) User Intent Attribution & `## Non-Goals`, (3) EARS Syntax & Falsifiable `AC-xxx` (every `REQ-xxx` has both a Happy-Path `AC-xxx` and an Error/Boundary `AC-xxx`), (4) Zero Unresolved Deferral Placeholders (zero unfinished deferral markers used in place of normative values), (5) Anti-Strawman ADR Debate ($\ge 2$ viable options, `Trade-offs & Risks`, `Rejected Alternatives`), and (6) Cross-Spec Lineage & Counterpart Cascade.
    - `tasks.md` contains a completed `## Gate 2: Derived File Self-Validation & Traceability Matrix` table with a dedicated 1-to-1 row for every single `AC-xxx` in `spec.md`, mapping it to its `REQ-xxx`, governing `ADR-xxx` in `decisions.md`, section in `design.md`, task in `tasks.md`, and verification section in `verification.md`.
  - `AC-035-2` (Error / Boundary Case — Failed or Omitted Gate Blocks `In-Progress` & Rejects Unmapped Scope): IF any Gate 1 row in `decisions.md` or per-AC Gate 2 row in `tasks.md` is missing, has an empty evidence cell, is marked `FAIL`, or if `design.md` / `tasks.md` contains any unmapped (gold-plated) item not traceable to a declared `REQ-xxx`, THEN THE specification SHALL remain in (for a new specification) or revert to (for an updated specification under Case 2 or Case 3) `Planning`, and code execution SHALL be blocked until all rows pass and human `"Proceed"` is granted.

### `REQ-036` [`NEW`]: Cross-Spec Lineage, Delta Tagging & Counterpart Cascade
- **Source Intent**: Verbatim user prompt (`"and a spec could refer to other spec, as this is a change, or modification"`).
- **Statement**: WHEN a specification supersedes or modifies one or more earlier specifications in `docs/specs/`, THE new `spec.md` SHALL declare `Extends / Modifies` and `Supersedes` links in its header, apply disjoint Whole-Spec Supersession or Living-Spec Modification tags to its requirements, and cascade status or requirement-level annotations to all affected counterpart files in `docs/specs/INDEX.md`, `<prior-spec>/spec.md`, and `<prior-spec>/decisions.md`.
- **Acceptance Criteria**:
  - `AC-036-1` (Happy Path — Disjoint Lineage Modes & Complete Counterpart Cascade):
    - **In-Place Amendment (`Planning` or `In-Progress` specs)**: Active specifications in `Planning` or `In-Progress` are amended directly in-place under Case 3 (`REQ-037`).
    - **Whole-Spec Supersession (`Supersedes: <prior-spec-id>`)**: Retires the prior specification as a whole; all requirements in the new specification are tagged `[NEW]`; and for all 5 superseded specifications (`2026-10-18` through `2026-10-30`, covering `REQ-001` – `REQ-033` and all 25 historical ADR records `ADR-001` – `ADR-024`, including both `2026-10-19` records numbered `ADR-012`), `docs/specs/INDEX.md`, each `<prior-spec>/spec.md` header, and each of the 25 historical ADR blocks in `<prior-spec>/decisions.md` record `Status: Superseded` (citing `2026-11-05-zero-python-spec-authoring-standard` / `ADR-025`) with original decision bodies preserved.
    - **Living-Spec Modification (`Extends / Modifies: <prior-spec-id>`)**: Keeps the prior `In-Testing` or `Verified` specification active, tags individual requirements in the delta specification per-ID (`[NEW]`, `[MODIFIES REQ-xxx in <prior-spec-id>]` with a verbatim `Previous Contract`, or `[DEPRECATED REQ-xxx in <prior-spec-id>]` with a `Deprecation & Migration Reason`), annotates the counterpart `REQ-xxx` heading in `<prior-spec>/spec.md` (`Modified by <new-spec-id>` or `Deprecated by <new-spec-id>`), and updates `<prior-spec>`'s row in `docs/specs/INDEX.md`.
  - `AC-036-2` (Error / Boundary Case — Prohibition of Mixed Lineage Modes, Range Tags & Uncascaded Counterparts): IF a specification simultaneously declares `Supersedes: <spec-id>` and tags a requirement `[MODIFIES REQ-xxx in <spec-id>]` for the same target specification, uses a multi-requirement range tag (`[MODIFIES REQ-001..REQ-005]`), overwrites an existing ADR's `Decision` body in-place instead of marking it `Superseded by ADR-yyy`, or omits cascading status/heading updates to the counterpart `INDEX.md`, `spec.md`, or `decisions.md`, THEN Gate 1 Check 6 SHALL fail.

### `REQ-037` [`NEW`]: Six-State Specification Lifecycle (`In-Testing` vs. `Verified`) & 3-Way Bug Decision Protocol
- **Source Intent**: Verbatim user prompts (`"I also do not think a spec is done if you finish, it still need some using or testing"` and `"what is the decision when there is bug?"`).
- **Statement**: WHEN managing a specification package in `docs/specs/`, THE agent SHALL enforce the 6-state lifecycle state machine (`Planning`, `In-Progress`, `In-Testing`, `Verified`, `Superseded`, `Abandoned`) with self-contained human approval recording in `spec.md`'s `Sign-off` field, and WHEN a bug or discrepancy is discovered at any stage, THE agent SHALL classify and remediate it strictly through the **3-Way Bug Decision Protocol** synchronized across `spec.md`, `rules/spec-standard.md`, and `skills/spec-standard/SKILL.md`.
- **Acceptance Criteria**:
  - `AC-037-1` (Happy Path — 6-State Lifecycle Transitions & Self-Contained Human `Proceed` Sign-Off):
    - `Planning` $\to$ `In-Progress` requires Gate 1 + Gate 2 `PASS` and explicit human `"Proceed"` approval recorded verbatim in `spec.md` (`Sign-off`) and `verification.md`.
    - `In-Progress` $\to$ `In-Testing` requires all tasks in `tasks.md` checked (`- [x]`) and verbatim test/validation output recorded in `verification.md`.
    - `In-Testing` $\to$ `Verified` requires real-world usage/dogfooding and explicit human sign-off recorded in `spec.md` (`Sign-off`).
    - Replacing a specification in full transitions it to `Superseded`; explicit user cancellation transitions it to `Abandoned`.
  - `AC-037-2` (Error / Boundary Case — Defect Regression Transitions & 3-Way Bug Decision Protocol): IF a defect, test failure, or specification discrepancy is discovered during `In-Progress`, `In-Testing`, or `Verified`, THEN THE agent SHALL NEVER self-promote to `Verified`, weaken `spec.md` to pass a broken design, or silently diverge from `spec.md` in code, and SHALL execute the matching branch of the **3-Way Bug Decision Protocol**:
    - **Case 1 (Implementation Bug — `spec.md` & `decisions.md` are right; code/test is wrong)**: Do NOT edit `spec.md` or `decisions.md`. Set status to `In-Progress`, add an unchecked `- [ ]` reproducer task in `tasks.md` citing `REQ-xxx`, reproduce with a failing test, fix the code, check off `- [x]` in `tasks.md`, append the verification run to `verification.md`, and transition status to `In-Testing`.
    - **Case 2 (Design / ADR Flaw — `spec.md` is right; `decisions.md` or `design.md` failed in practice)**: Stop coding and do NOT weaken `spec.md`. Set status to `Planning`, mark the flawed `ADR-xxx` as `Superseded by ADR-yyy` in `decisions.md`, append `ADR-yyy`, re-run Gate 1 (`decisions.md`), update `design.md` and `tasks.md`, re-run Gate 2 (`tasks.md`), and obtain human `"Proceed"` before transitioning to `In-Progress`.
    - **Case 3 (Specification Gap or Flawed Requirement — `spec.md` missed an edge case or had a wrong requirement)**: Stop coding. Set status to `Planning`, amend `spec.md` (or create a `[MODIFIES]` delta spec), update `decisions.md` if needed, re-run Gate 1 (`decisions.md`), cascade updates to `design.md` and `tasks.md`, re-run Gate 2 (`tasks.md`), and obtain human `"Proceed"` before transitioning to `In-Progress`.
