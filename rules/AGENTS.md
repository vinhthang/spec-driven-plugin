# Spec-Driven Development Governance & Invariants

<rule name="spec-driven">
<description>
Governs how to write, review, evolve, and verify code-grounded feature specifications in docs/specs/ using the five-document architecture (spec.md, decisions.md, design.md, tasks.md, verification.md). Pure Markdown guidance — zero Python hooks.
</description>

<constraints>
- **1. Document Responsibilities & Precedence**:
  - **Normative Documents (`spec.md` > `decisions.md`)**: `spec.md` governs intent, scope, observable EARS requirements (`REQ-NNN`), acceptance criteria (`AC-NNN-M`), `First entered In-Testing`, and approval/lifecycle history. `decisions.md` records architectural rationale, viable alternatives (`ADR-NNN`, or explained rationale when constraints leave no choice), and **Gate 1**.
  - **Derived Plans & Evidence (`design.md` > `tasks.md` > `verification.md`)**: Complete **Gate 1** in `decisions.md` (replacing `UNCHECKED` with evidence-backed `PASS`) before writing or updating `design.md`, `tasks.md`, or `verification.md`. Complete **Gate 2** in `tasks.md` before executing implementation work.
  - **Execution Boundary**: Respect the user's scope and explicit authorization. Merely requesting a specification does not authorize implementation; when `attention-guard` thinking-model restrictions are active, the Primary Agent authors `.md` specification files and delegates multi-file implementation and test/build suites to subagents after explicit human authorization (trivial single-file Case 1 fixes or standalone single-agent environments may execute directly).
- **2. Grounding, Intent & Owner-Deferred Decisions**:
  - **Codebase Grounding & Honest Intent**: Inspect actual repository paths, interfaces, tests, and `docs/specs/INDEX.md` before authoring. Every `REQ-NNN` must cite attributable `Source intent` (actual user quote, observed defect, or explained ADR/standard derivation) and observable EARS statements (`WHEN / WHILE / IF ... THEN THE <system> SHALL ...`) with success and boundary/failure criteria. Never invent APIs or user quotes.
  - **Owner-Deferred `[PROVISIONAL]` vs. Unowned Placeholders**: Unowned `TODO`/`TBD` placeholders fail Gate 1. Explicitly owner-deferred questions use `[PROVISIONAL]` on the requirement with `Open question`, `Owner deferral`, and `Blocked scope`, marking dependent Gate 2 rows and tasks `BLOCKED` while allowing independent authorized scope to proceed.
  - **Planned Checks vs. Actual Execution Evidence**: Keep `## Planned checks` (`Execution: Not run.`) distinct from `## Execution evidence` and `## Real-world observations` in `verification.md`. Never claim a check ran in a plan or overwrite prior failed runs.
- **3. Revision Routing & Six-State Lifecycle (`In-Testing` Is Not `Verified`)**:
  - **States**: `Planning` -> `In-Progress` -> `In-Testing` (all tasks complete, zero blocked criteria, checks passed with actual evidence; sets `First entered In-Testing` permanently) -> `Verified` (requires real-world usage evidence and explicit human confirmation; tests alone are insufficient), plus `Superseded` and `Abandoned`.
  - **Revision Route by Testing History**: Inspect `First entered In-Testing` and lifecycle history before editing normative bodies. Packages that **never reached testing** (`First entered In-Testing: Never`) are amended in place; packages that **reached testing at least once** keep existing `REQ`/`AC` bodies frozen and evolve via a linked delta package (`Changes` / `Retires` / `Replaces`) with a 1-hop `Current contract` annotation added outside the parent's frozen body once the delta reaches `In-Testing`.
- **4. Three Defect Cases**:
  - **Case 1 — Implementation Defect** *(Requirements & design remain right; code/tests fail — mints 0 new `REQ` IDs)*: Reopen as `In-Progress`, add an unchecked reproducer/fix task in `tasks.md`, fix and record actual run evidence in `verification.md`, and return to `In-Testing` (preserving `First entered In-Testing`).
  - **Case 2 — Design / Architecture Defect** *(Requirement is right; design/ADR fails — mints 0 new `REQ` IDs)*: Set to `Planning` (retaining testing history), append a replacement ADR or refine a proposed choice in `decisions.md`, re-run Gate 1, update `design.md`/`tasks.md`/`verification.md`, and re-run Gate 2.
  - **Case 3 — Missing or Incorrect Requirement** *(Observable behavior must change — mints/updates `REQ` IDs)*: Pause affected work, inspect `First entered In-Testing` before editing, amend in place (if never tested) or create a linked delta package minting new `REQ-NNN` IDs (if previously tested), and re-run Gate 1 and Gate 2 before authorized execution.
</constraints>

<instructions>
- When authoring, reviewing, updating, or triaging a feature specification in `docs/specs/`, consult skill `spec-driven`.
</instructions>
</rule>
