# Technical Design: Adversarial ADR Debate, Anti-Dogma Auditing & Spec-Gate Lifecycle Hardening

## 1. Requirement-to-Component Traceability Matrix

| Component | Target File(s) | Governing Requirements & ADRs |
|---|---|---|
| Adversarial Architectural Soundness Audit | `agents/traceability-auditor.md`, `scripts/semantic_checker.py` | `Addresses: REQ-029` (`ADR-020`) |
| Structured ADR Debate & Anti-Dogma Checker | `scripts/spec_checker.py`, `skills/spec-standard/SKILL.md`, `rules/spec-standard.md` | `Addresses: REQ-030` (`ADR-021`) |
| Mid-Flight `INDEX.md` Scope Expansion Gate | `scripts/spec-gate.py` | `Addresses: REQ-031` (`ADR-022`) |
| Scoped `/goal` Autonomous Approval | `scripts/spec-gate.py` | `Addresses: REQ-032` (`ADR-023`) |
| Append-Only `decisions.md` Protection Gate | `scripts/spec-gate.py` | `Addresses: REQ-033` (`ADR-024`) |

---

## 2. Detailed Component Design

### 2.1 Adversarial Architectural Soundness in `traceability-auditor.md` & `semantic_checker.py` (`REQ-029`, `ADR-020`)
1. **`agents/traceability-auditor.md`**:
   - Add per-requirement evaluation fields:
     - `architecturally_sound` (`bool`): Evaluates whether `REQ-xxx` and its governing `ADR-xxx` are technically sound, preserve module cohesion and encapsulation (`private` vs `internal`), avoid conflating agent/IDE tool limits (e.g., `ast-gate.py` 500-line read limits) with source code file-size caps, and justify trade-offs.
     - `debate_rationale` (`str`): Summarizes the trade-off and rejected-alternatives verification for `REQ-xxx`.
2. **`scripts/semantic_checker.py`**:
   - In `validate_semantic_traceability()`:
     - For each `req_id` in `spec_reqs`, if `"architecturally_sound"` is present in `entry`:
       - Verify `entry.get("architecturally_sound") is True` and `bool(str(entry.get("debate_rationale") or "").strip())`.
       - If false or missing rationale, return `(False, f"Requirement '{req_id}' failed adversarial architectural soundness check in traceability_audit.json: {entry.get('debate_rationale') or 'missing debate_rationale'}")`.

### 2.2 Structured ADR Debate Validation in `scripts/spec_checker.py` (`REQ-030`, `ADR-021`)
1. **`validate_adr_debate_structure(decisions_text: str, spec_text: str = "") -> Tuple[bool, str]`**:
   - Check 1 (**Hard Line-Count / File-Splitting Dogma Guard**):
     - Detect hard source-file line-count cap patterns in `spec_text` or `decisions_text` (e.g., `r"(?:every|all)\s+[^\n.]{0,60}\bfiles?\b[^\n.]{0,60}(?:under|<\s*)\d+\s+lines"`, `r"sub-\d+-line\s+invariant"`, `r"lineCount\s*<\s*\d+"`).
     - If matched and `decisions_text` does not contain both a trade-offs marker (`trade-off`, `risk`, `cons`) and a rejected-alternatives marker (`rejected alternative`, `alternatives considered`), return `(False, "Specification imposes a hard file line-count cap without debating Trade-offs/Risks and Rejected Alternatives in decisions.md")`.
   - Check 2 (**Structured ADR Section Completeness**):
     - Split `decisions_text` by ADR headings (`^#{1,4}\s+.*?\b(ADR-\d+)\b`, `re.MULTILINE`).
     - For each ADR block that uses structured fields (contains both `context` and `decision` markers such as `- **Context**:` / `### Context` and `- **Decision**:` / `### Decision`):
       - Verify the ADR block contains a trade-offs/risks marker (`trade-off`, `risks`, `cons`) AND a rejected-alternatives marker (`rejected alternative`, `alternatives considered`).
       - If missing, return `(False, f"{adr_id} in decisions.md is missing required 'Trade-offs & Risks' or 'Rejected Alternatives' debate section")`.
   - Invoke `validate_adr_debate_structure(decisions_content, contents["spec.md"])` inside `validate_spec_package()`.

### 2.3 Mid-Flight `INDEX.md` Scope Expansion Gate in `scripts/spec-gate.py` (`REQ-031`, `ADR-022`)
1. **`is_unauthorized_status_promotion()` (`scripts/spec-gate.py`)**:
   - Build `existing_approved_map: Dict[str, Dict[str, str]]` mapping `feature_id -> record` for all existing records in `EXECUTION_STATUSES`.
   - Identify `newly_promoted_or_expanded`:
     - Any projected record in `EXECUTION_STATUSES` where `feat_id not in existing_approved_map`, **OR**
     - Any projected record in `EXECUTION_STATUSES` where `feat_id in existing_approved_map` and `(r.get("req_range", "").strip() != existing_approved_map[feat_id].get("req_range", "").strip() or r.get("key_decisions", "").strip() != existing_approved_map[feat_id].get("key_decisions", "").strip())`.
   - Apply the same two-stage gate (require `SPEC_GATE_ALLOW_APPROVAL == "1"` or `has_recent_user_approval(payload)`, AND require `checker.validate_semantic_traceability(pkg_dir, verify_evidence=False)`) to all records in `newly_promoted_or_expanded`.

### 2.4 Scoped `/goal` Autonomous Approval in `scripts/spec-gate.py` (`REQ-032`, `ADR-023`)
1. **`has_recent_user_approval()` (`scripts/spec-gate.py`)**:
   - Locate the last index `last_goal_idx` in `user_turns` matching `r"(?:^|\s)/goal(?:\b|\s|$)"`.
   - If `last_goal_idx is not None`:
     - If `"/plan" in user_turns[-1].lower()`: return `False`.
     - If `last_goal_idx == len(user_turns) - 1`: return `True`.
     - If all subsequent turns `user_turns[last_goal_idx + 1:]` match continuation confirmations (`r"\b(proceed|approve|approved|yes|lgtm|continue)\b"` or `"the user has approved this document"`): return `True`.
     - Otherwise (a new non-`/goal` topic or question turn occurred after `/goal`), do not grant `/goal` approval and fall through to checking the latest turn for explicit approval.

### 2.5 Append-Only `decisions.md` Protection in `scripts/spec-gate.py` (`REQ-033`, `ADR-024`)
1. **`is_destructive_decisions_edit(decisions_path: Path, index_path: Path, args: Dict[str, Any], checker: Any) -> Tuple[bool, str]`**:
   - If `not decisions_path.is_file()`: return `(False, "")` (new file creation is allowed).
   - Read `disk_text = decisions_path.read_text(encoding="utf-8")` and project `projected_text` using the same helper logic as `is_unauthorized_status_promotion()`.
   - Extract existing ADR IDs `old_adrs = set(re.findall(r"\bADR-\d+\b", disk_text))` and `new_adrs = set(re.findall(r"\bADR-\d+\b", projected_text))`.
   - If `old_adrs - new_adrs`:
     - Return `(True, f"Spec Gate Rejection: decisions.md is append-only (RULE[spec-standard]). Existing ADR IDs cannot be removed: {', '.join(sorted(old_adrs - new_adrs))}")`.
   - Determine if the feature owning `decisions_path.parent.name` is in `EXECUTION_STATUSES | VERIFIABLE_TERMINAL_STATUSES` in `index_path`:
     - Extract structured `(adr_id, decision_body)` pairs from `disk_text` and `projected_text` (matching each `## ADR-\d+` block's `- **Decision**:` section up to the next `- **...**:` field or heading).
     - If any existing `adr_id`'s `decision_body` was altered in `projected_text`:
       - Return `(True, f"Spec Gate Rejection: decisions.md is append-only for active/completed specs. Do not rewrite the Decision body of {adr_id} in-place; mark {adr_id} as 'Superseded' and append a new ADR section.")`.
