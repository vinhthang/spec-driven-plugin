# Architecture Decisions: Adversarial ADR Debate, Anti-Dogma Auditing & Spec-Gate Lifecycle Hardening

## `ADR-020` — Upgrade `traceability-auditor` and `semantic_checker.py` with Adversarial Architectural Soundness Checks (`Addresses: REQ-029`)
- **Status**: `Accepted`
- **Context**: In `OpenKey` (`5557cc19-259f-4ef8-a1b3-80ea94531d23`), `traceability-auditor` evaluated `REQ-009` (*"every `.swift` file MUST be < 500 lines"*) and returned `verdict: "PASS"` because `design.md` and `tasks.md` matched `spec.md`. Because the auditor only checked cross-document alignment (`design_aligned`, `tasks_actionable`, `decisions_consistent`), it rubber-stamped a flawed requirement born from agent tool-hook bleed-over (`ast-gate.py`).
- **Decision**: Add `architecturally_sound` (`bool`) and `debate_rationale` (`str`) to the evaluation contract in `agents/traceability-auditor.md` and `scripts/semantic_checker.py`. Instruct the auditor to fail any requirement/ADR that conflates agent/IDE tool constraints with software architecture, imposes arbitrary file line-count caps that break module cohesion or `private` encapsulation, or lacks genuine trade-off analysis.
- **Trade-offs & Risks**:
  - *Pros*: Stops bad requirements at Phase 1 before any subagent mutates code; leverages the existing high-reasoning model (`claude-opus-4-6` / `gemini-3.8-flash-high`) already invoked during planning.
  - *Cons / Risks*: Existing `traceability_audit.json` receipts in completed specs do not contain `architecturally_sound`. To prevent breaking historical specs, `semantic_checker.py` validates `architecturally_sound` whenever present in the receipt (and requires it when `architecturally_sound` is emitted by updated auditors), while `spec_checker.py` enforces structural ADR debate on `decisions.md`.
- **Rejected Alternatives**:
  - *Alternative 1: Spawn a separate second subagent for architectural review on every spec edit.* Rejected because spawning two sequential high-reasoning subagents doubles latency when `traceability-auditor` already reads all 4 specification documents in full.
  - *Alternative 2: Rely solely on human review.* Rejected because under `/goal` autonomous mode (or when subtle constraints are buried in long specs), mechanical and auditor checks are the primary line of defense.

---

## `ADR-021` — Enforce Structured ADR Debate (`Trade-offs & Risks` + `Rejected Alternatives`) in `spec_checker.py` (`Addresses: REQ-030`)
- **Status**: `Accepted`
- **Context**: `spec_checker.py` previously accepted any `decisions.md` containing the regex `ADR-\d+`, even if it was a one-sided assertion with zero discussion of downsides or rejected alternatives.
- **Decision**: Implement `validate_adr_debate_structure(decisions_text, spec_text)` in `scripts/spec_checker.py` and call it from `validate_spec_package()`. Whenever `decisions.md` defines structured ADR sections (containing `Context` and `Decision` markers) or whenever `spec.md`/`decisions.md` proposes source-file line-count or file-splitting rules, `decisions.md` must include both a trade-off/risk section (`Trade-offs`, `Risks`, or `Cons`) and a rejected-alternatives section (`Rejected Alternatives` or `Alternatives Considered`).
- **Trade-offs & Risks**:
  - *Pros*: Deterministic, zero-latency check in `spec_checker.py` that forces the Primary Agent to articulate what could go wrong and what alternatives were rejected before a spec is valid.
  - *Cons / Risks*: Could break existing unit tests in `tests/test_spec_checker.py` that use minimal 1-line fixtures (`"ADR-001: Architecture decision"`). We mitigate this by applying the full section check to multi-section structured ADRs (those with explicit `Context` / `Decision` fields) and to any spec mentioning hard file line-count caps.
- **Rejected Alternatives**:
  - *Alternative 1: Require 4 markdown subheadings on every 1-line unit test fixture.* Rejected because it would force rewriting 30+ existing unit tests that test unrelated path-traversal or CLI exit-code logic.

---

## `ADR-022` — Gate Mid-Flight `req_range` and `key_decisions` Expansion in `docs/specs/INDEX.md` (`Addresses: REQ-031`)
- **Status**: `Accepted`
- **Context**: In `scripts/spec-gate.py`, `is_unauthorized_status_promotion()` previously ignored any feature whose `feature_id` was already in `existing_approved`. In `OpenKey`, the agent appended `REQ-009` and `ADR-008` to an already `In-Progress` feature by editing its `INDEX.md` row from `REQ-001 to REQ-007` to `REQ-001 to REQ-009`, bypassing both human approval and `validate_semantic_traceability()`.
- **Decision**: Update `is_unauthorized_status_promotion()` in `scripts/spec-gate.py` to track `existing_approved_map` (`feature_id -> record`) and treat any change to `req_range` or `key_decisions` on an execution-authorized row as a scope expansion requiring recent user approval (`has_recent_user_approval`) and a valid `traceability_audit.json` matching the updated `spec_hash`.
- **Trade-offs & Risks**:
  - *Pros*: Closes the exact loophole used in `OpenKey` (`L2418`) where new requirements were injected into an active spec without re-approval or re-auditing.
  - *Cons / Risks*: Cosmetic edits to the `Title` column of an approved row should not be blocked; comparing only `status`, `req_range`, and `key_decisions` preserves title-edit flexibility.
- **Rejected Alternatives**:
  - *Alternative 1: Block all edits to `docs/specs/<feature-id>/spec.md` once a feature is `In-Progress`.* Rejected because legitimate mid-feature refinements require editing `spec.md` first (while in `Planning` or before updating `INDEX.md` and `traceability_audit.json`).

---

## `ADR-023` — Scope `/goal` Autonomous Approval to the Active Turn Sequence (`Addresses: REQ-032`)
- **Status**: `Accepted`
- **Context**: `has_recent_user_approval()` in `scripts/spec-gate.py` used `any(re.search(r"(?:^|\s)/goal(?:\b|\s|$)", t, re.IGNORECASE) for t in user_turns)`, which permanently enabled autonomous self-approval for the entire conversation once `/goal` was used once.
- **Decision**: Update `has_recent_user_approval()` so `/goal` only authorizes execution when `/goal` is in `user_turns[-1]` or when every subsequent user turn after the last `/goal` turn is an explicit continuation confirmation (`proceed`, `approve`, `approved`, `yes`, `lgtm`, `continue`).
- **Trade-offs & Risks**:
  - *Pros*: Prevents a `/goal` command from yesterday's task from silently auto-approving today's specifications in the same long-lived conversation.
  - *Cons / Risks*: If a user sends a mid-`/goal` clarification that is not an approval keyword, the agent must either ask for `"Proceed"` or the user includes `/goal` / `proceed`. This is the desired safety boundary.
- **Rejected Alternatives**:
  - *Alternative 1: Remove `/goal` support from `spec-gate.py` entirely.* Rejected because `RULE[explicit-approval]` explicitly specifies that `/goal` authorizes autonomous execution for the active goal task.

---

## `ADR-024` — Enforce Append-Only `decisions.md` in `spec-gate.py` (`Addresses: REQ-033`)
- **Status**: `Accepted`
- **Context**: `RULE[spec-standard]` mandates that `decisions.md` is append-only (`superseded, never edited`), yet `spec-gate.py` allowed arbitrary edits to `docs/specs/**/decisions.md`. In `OpenKey` (`L2948`), the agent overwrote `ADR-008` in-place to erase the `< 500` line rule from history instead of superseding it with a new ADR.
- **Decision**: Add `is_destructive_decisions_edit()` in `scripts/spec-gate.py` before the blanket `docs/specs/` allow rule. When editing an existing `decisions.md` that already contains `ADR-\d+` entries, block any edit that removes an existing `ADR-\d+` ID, and when the owning feature is in an execution or terminal status (`Approved`, `In-Progress`, `Active`, `Completed`, `Implemented`, `Done`), block in-place modifications to existing ADR `- **Decision**:` sections (allowing status changes to `Superseded` and appending new `ADR-\d+` blocks).
- **Trade-offs & Risks**:
  - *Pros*: Guarantees an immutable audit trail of architectural decisions and why bad decisions were superseded.
  - *Cons / Risks*: While a feature is still in `Draft` or `Planning` (before initial approval), authors may need to refine an ADR's decision wording before locking it; scoping the `- **Decision**:` body immutability to execution/terminal specs while always blocking `ADR-\d+` ID deletion balances drafting ergonomics with historical integrity.
- **Rejected Alternatives**:
  - *Alternative 1: Block all `edit_file` calls on `decisions.md` and only allow `Append=True`.* Rejected because marking an existing ADR's status line as `Status: Superseded by ADR-013` requires an in-place status line edit.
