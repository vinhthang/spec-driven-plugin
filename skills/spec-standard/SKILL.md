---
name: spec-standard
description: Author and maintain technical feature specifications following the 5-Document Architecture, requirement ID traceability, and modern docs/specs/ package layout.
---

# 5-Document Architecture Specification Standard

Use this skill when designing new features, authoring architectural specs, or maintaining feature documentation in `docs/specs/`.

---

## 1. Upstream Command Integration Pipeline

Feature specifications and implementation plans connect directly to Antigravity's alignment commands and Dalio human gating:

```
[ User Intent ]
       │
       ▼
 1. /grill-me (or ask_question)   ──▶ Resolves trade-offs & edge cases ──▶ Produces spec.md & decisions.md
       │
       ▼
 2. /plan                         ──▶ CodeGraph impact & architecture  ──▶ Produces design.md & tasks.md
       │
       ▼
 3. Human Approval Gate           ──▶ Awaits explicit "Proceed" sign-off on design & tasks
       │
       ▼
 4. Phase 2 TDD Execution         ──▶ Subagents implement per task     ──▶ Records evidence in verification.md
```

1. **Requirements Gathering (`/grill-me`)**: When requirements are high-level or ambiguous, run `/grill-me` (or invoke `ask_question`). The interactive interview output resolves ambiguities and directly populates `spec.md` (with stable `REQ-XXX` IDs) and `decisions.md`.
2. **Phase 1 Planning (`/plan`)**: Trigger `/plan` to execute read-only CodeGraph impact analysis, formulate `design.md`, and generate `tasks.md` and the ephemeral implementation plan (`implementation_plan.md`).
3. **Approval Gate**: In accordance with `RULE[explicit-approval.md]`, await explicit user confirmation ("Proceed" action or text) before executing any task in `tasks.md`.

---

## 2. The 5-Document Architecture

Every significant feature or architectural workstream maintains a package directory under `docs/specs/<feature-id>/` with up to 5 structured documents:

| Document | Purpose | Mutability | Approval |
| :--- | :--- | :--- | :--- |
| **`spec.md`** | What must be true (requirements, user stories, contracts) | Living, versioned | Human-approved (`/grill-me`) |
| **`decisions.md`** | What has been explicitly decided (ADR rationale) | Append-only (superseded, never edited) | Team-aligned |
| **`design.md`** | How we intend to build it (architecture, components, data flows) | Revisable blueprint | Peer-reviewed (`/plan`) |
| **`tasks.md`** | What remains to be done (execution checkboxes) | Volatile, task tracking | Agent-owned |
| **`verification.md`** | Verbatim evidence that it works (test runs, benchmark outputs) | Append-only per run | Verifiable (TDD) |

### Scaling Switches
- **Minimal Base**: `spec.md` + `design.md` + `tasks.md`.
- **Add `decisions.md`**: When design rationale or trade-offs must outlive the implementation phase.
- **Add `verification.md`**: When correctness must be demonstrated with durable, reproducible tool outputs.

---

## 3. Precedence Order & Conflict Protocol

When documents disagree:
$$\text{spec.md} > \text{decisions.md} > \text{design.md} > \text{tasks.md}$$

- **`verification.md`** can invalidate any document, but may never redefine the specification.
- If a test fails because `design.md` contradicts `spec.md`, the design is wrong. Propose an update to the design; do not weaken `spec.md` just to pass a test.
- When a conflict is discovered, **stop affected work**, name the conflict, and apply precedence. Never silently edit whichever document is easiest.

---

## 4. Requirement IDs (The Traceability Spine)

- Every normative requirement in `spec.md` MUST have a stable, sequential ID (e.g. `REQ-001`, `REQ-002`).
- This ID must be threaded through all 5 documents:
  - In `design.md`: Map architectural components to requirement IDs (`Addresses: REQ-001`).
  - In `tasks.md`: Cite requirement IDs on task items (`- [ ] Implement parser (REQ-001)`).
  - In `verification.md`: Cite the requirement ID next to verbatim test output (`Verified: REQ-001`).
- An ID with no evidence is unverified work; evidence with no ID is unaccounted activity.

---

## 5. Directory Layout & Cataloging

Features are organized under `docs/specs/<feature-id>/`:
```
docs/specs/
├── INDEX.md                  # Central catalog of all specs and status
└── 2026-09-16-modular-review/
    ├── spec.md
    ├── decisions.md
    ├── design.md
    ├── tasks.md
    └── verification.md
```

### Central Catalog (`docs/specs/INDEX.md`)
Maintains a registry of all active, draft, and completed specs, listing:
- Feature ID and title
- Lifecycle status (`draft`, `review`, `approved`, `implemented`)
- Reserved requirement ID ranges (e.g., `REQ-001` to `REQ-025`)
