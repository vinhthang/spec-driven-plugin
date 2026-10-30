# Specification: Adversarial ADR Debate, Anti-Dogma Auditing & Spec-Gate Lifecycle Hardening

**Feature ID**: `2026-10-30-adversarial-adr-debate-and-spec-gate-hardening`  
**Status**: `Implemented`  
**Created**: `2026-10-30`  
**Version**: `1.0.0`  
**Precedence**: `spec.md` > `decisions.md` > `design.md` > `tasks.md`

---

## 1. Problem Statement & Forensic Root Causes

During the `OpenKey` specification development (`2026-10-27-ime-intelligence-and-ecosystem`, conversation `5557cc19-259f-4ef8-a1b3-80ea94531d23`), the user asked to *"reduce the complex of the code base... make it easy to read and modify"*. Five systemic gaps in `spec-driven-plugin` allowed the agent to invent, self-approve, and enforce a harmful `< 500` line-count rule (`REQ-009` / `ADR-008`) without debate, fragmenting cohesive modules into 28 files and later rewriting `ADR-008` in-place:

1. **`traceability-auditor` & `semantic_checker.py` Rubber-Stamped Bad Requirements (`REQ-029`)**: `traceability-auditor` only checked whether `design.md` and `tasks.md` aligned with `spec.md`, not whether `REQ-009` / `ADR-008` was architecturally sound or conflated agent tool limits (`ast-gate.py`'s 500-line `read_file` threshold) with application architecture.
2. **No Mechanical Requirement for ADR Trade-Offs & Rejected Alternatives (`REQ-030`)**: `spec_checker.py` passed `decisions.md` whenever the substring `ADR-\d+` appeared, allowing one-sided dogma with zero `Rejected Alternatives` or `Trade-offs & Risks` analysis.
3. **Unchecked Mid-Flight Spec Expansion in `INDEX.md` (`REQ-031`)**: `is_unauthorized_status_promotion()` in `spec-gate.py` only gated features not already in `existing_approved`. Because `2026-10-27-ime-intelligence-and-ecosystem` was already `In-Progress`, expanding its `INDEX.md` row from `REQ-001 to REQ-007` to `REQ-001 to REQ-009` bypassed both user approval and semantic traceability auditing.
4. **Eternal `/goal` Bleed-Over Across Unrelated Turns (`REQ-032`)**: `has_recent_user_approval()` in `spec-gate.py` checked `any(re.search(r"/goal", t) for t in user_turns)` across the entire transcript, keeping autonomous self-approval active forever after a single historical `/goal` prompt.
5. **Unenforced Append-Only `decisions.md` Invariant (`REQ-033`)**: `spec-gate.py` allowed unrestricted edits inside `docs/specs/`, permitting the agent to overwrite `ADR-008` in-place instead of marking it `Superseded` and appending `ADR-013`.

---

## 2. Normative Requirements (EARS Syntax)

### `REQ-029` — Adversarial Architectural Soundness & Anti-Dogma Audit (`ADR-020`)
- **WHEN** `traceability-auditor` (`agents/traceability-auditor.md`) or `validate_semantic_traceability()` (`scripts/semantic_checker.py`) evaluates a specification package, **THE** auditor and verification engine **SHALL** evaluate architectural soundness (`architecturally_sound: bool`, `debate_rationale: str`) and reject specifications that conflate agent/IDE tool limits (such as 500-line file-read gates) with application source-file size caps or fragment cohesive modules without trade-off justification.
- **Acceptance Criteria**:
  - `agents/traceability-auditor.md` requires `architecturally_sound` (`bool`) and `debate_rationale` (`str`) per requirement and instructs the auditor to return `verdict: "FAIL"` (`architecturally_sound: false`) when a requirement or ADR imposes arbitrary source-file line-count caps or weakens encapsulation without trade-off justification.
  - `validate_semantic_traceability()` in `scripts/semantic_checker.py` rejects any receipt where `architecturally_sound` is `False` (or where `architecturally_sound` is `True` with an empty `debate_rationale`), while remaining backward-compatible with legacy receipts that predate the field.

### `REQ-030` — Structured ADR Debate (`Trade-offs & Risks` and `Rejected Alternatives`) in `spec_checker.py` (`ADR-021`)
- **WHEN** `validate_spec_package()` in `scripts/spec_checker.py` validates `decisions.md` containing structured multi-section ADR blocks (`Context` + `Decision`) or when `spec.md`/`decisions.md` introduces source-file line-count or module-splitting constraints, **THE** checker **SHALL** require explicit trade-off analysis (`Trade-offs`, `Risks`, or `Cons`) and `Rejected Alternatives` (`Alternatives Considered`) in `decisions.md`.
- **Acceptance Criteria**:
  - A structured ADR in `decisions.md` containing `Context` and `Decision` sections without `Rejected Alternatives` / `Alternatives Considered` or `Trade-offs` / `Risks` is rejected by `validate_spec_package()` with an actionable error message.
  - A specification declaring hard source-file line-count caps (e.g., `every .* file .* under 500 lines`, `< 500 lines` invariant) without an ADR debate section is rejected by `validate_spec_package()`.
  - Compact single-line ADR test fixtures in existing unit tests remain supported.

### `REQ-031` — Mid-Flight Spec Expansion Gate on `docs/specs/INDEX.md` (`ADR-022`)
- **WHEN** an edit to `docs/specs/INDEX.md` modifies the `req_range` or `key_decisions` column of an already execution-authorized feature (`Approved`, `In-Progress`, `Active`), **THE** `is_unauthorized_status_promotion()` check in `scripts/spec-gate.py` **SHALL** require recent user approval (or active current-turn `/goal`) AND a valid, non-stale `traceability_audit.json` covering the updated specification package.
- **Acceptance Criteria**:
  - Expanding `req_range` (e.g., `REQ-001` $\to$ `REQ-001 - REQ-009`) or `key_decisions` (`ADR-001` $\to$ `ADR-001 - ADR-008`) on an `Approved` or `In-Progress` row in `docs/specs/INDEX.md` without recent user approval is denied by `spec-gate.py`.
  - Expanding `req_range` or `key_decisions` with user approval but without an updated `traceability_audit.json` matching the new `spec_hash` is denied by `spec-gate.py`.
  - Editing only the `title` column of an already-approved feature in `docs/specs/INDEX.md` remains allowed.

### `REQ-032` — Scoped `/goal` Autonomous Approval in `has_recent_user_approval()` (`ADR-023`)
- **WHEN** `has_recent_user_approval()` in `scripts/spec-gate.py` inspects `transcriptPath` for `/goal`, **THE** function **SHALL** grant autonomous `/goal` approval only when `/goal` appears in the latest user turn (`user_turns[-1]`) or when all user turns following the most recent `/goal` turn are explicit continuation confirmations (`proceed`, `approve`, `approved`, `yes`, `lgtm`, `continue`), rather than matching any historical `/goal` turn across the entire conversation.
- **Acceptance Criteria**:
  - A transcript whose latest user turn contains `/goal` (and not `/plan`) returns `True`.
  - A transcript where turn 1 contained `/goal` and turn 2 is a new non-approval prompt or question (e.g., `"I do not think this rule is good"` or `"What do you think now?"`) returns `False`.

### `REQ-033` — Mechanical Append-Only Enforcement on `decisions.md` (`ADR-024`)
- **WHEN** a file-mutation tool targets an existing `decisions.md` inside `docs/specs/<feature-id>/` that already contains `ADR-\d+` declarations, **THE** `spec-gate.py` hook **SHALL** block edits that delete existing `ADR-\d+` identifiers or overwrite the `- **Decision**:` body of an existing ADR in an execution-authorized or completed specification (permitting status transitions to `Superseded` and appending new `ADR-\d+` sections).
- **Acceptance Criteria**:
  - Deleting an existing `ADR-001` heading/identifier from `decisions.md` is denied by `spec-gate.py`.
  - Rewriting the `- **Decision**:` body of an existing `ADR-008` in an `Approved`/`In-Progress`/`Completed` feature is denied with guidance to mark `ADR-008` as `Superseded` and append a new `ADR-xxx`.
  - Appending a new `ADR-002` section or marking `ADR-001` as `Superseded by ADR-002` is allowed.
