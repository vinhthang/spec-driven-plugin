---
name: spec-driven
description: Author, self-validate, and maintain high-signal feature specifications using the 5-Document Architecture, EARS syntax, cross-spec delta lineage, In-Testing lifecycle, and the 3-way bug decision protocol.
---

# Specification Authoring & Lifecycle Playbook (`spec-driven`)

A specification is only useful if it makes requirements unambiguous, architectural trade-offs explicit, and downstream implementation verifiable. This skill governs how to author, self-validate, evolve, and test specifications in `docs/specs/<feature-id>/` with **zero Python ceremony**.

---

## 1. Document Precedence & Derivation Flow

$$\underbrace{\text{spec.md} > \text{decisions.md}}_{\text{Normative Source (Author First)}} \xrightarrow{\text{Gate 1 Table}} \underbrace{\text{design.md} > \text{tasks.md}}_{\text{Derived Blueprint (Author Second)}} \xrightarrow{\text{Gate 2 Table}} \text{Human "Proceed"} \longrightarrow \underbrace{\text{verification.md}}_{\text{Empirical Falsifier}}$$

| Document | Role | Authority Level |
| :--- | :--- | :--- |
| `docs/specs/INDEX.md` | Central 6-column catalog of all specifications and their current lifecycle status (`Feature ID \| Title \| Status \| REQ Range \| Key Decisions \| Spec Path`). | Registry |
| `spec.md` | Normative requirements (`REQ-xxx`), acceptance criteria (`AC-xxx`), `Non-Goals`, `Sign-off`, `Type`, `Version`, and cross-spec `Lineage`. | **Highest (Normative)** |
| `decisions.md` | Append-only Architecture Decision Records (`ADR-xxx`), trade-off debates, and **Gate 1 Self-Validation Table**. | **Normative** |
| `design.md` | Concrete file/symbol blast radius, data structures, interfaces, and error-handling flows derived from `spec.md` + `decisions.md`. | Derived Blueprint |
| `tasks.md` | Actionable TDD execution checklist (`- [ ]` / `- [x]`) and **Gate 2 Traceability Matrix** mapped 1-to-1 to `REQ-xxx` and `AC-xxx`. | Derived Checklist |
| `verification.md` | Empirical verification log containing verbatim test commands, exit codes, and real-world `In-Testing` notes. | Empirical Falsifier |

---

## 2. Step 1: Codebase Grounding (Before Writing Anything)

Before creating or editing `spec.md`:
1. **Read `docs/specs/INDEX.md`** and any related prior specifications in `docs/specs/` to identify the next available `REQ-NNN` and `ADR-NNN` IDs and determine whether this feature is a brand-new capability, a living-spec modification (`Extends / Modifies`), or a whole-spec replacement (`Supersedes`).
2. **Inspect the actual codebase** (`codegraph`, `ast-grep`, or file reads) to verify existing module boundaries, function signatures, and data models. Never write a specification from imagination.

---

## 3. Step 2: Author the Normative Source (`spec.md` & `decisions.md`)

### 3.1 `spec.md` Template (With Type, Version, Lineage, Sign-Off & Delta Tags)

Use disjoint lineage modes:
- **In-Place Amendment (`Planning` or `In-Progress` specs)**: Amend the active specification directly under Case 3 and re-run Gate 1 and Gate 2.
- **Whole-Spec Supersession (`Supersedes: <prior-spec-id>`)**: Use when retiring an earlier specification in full. All requirements in the new spec are tagged `[NEW]`. If the superseded spec directory remains in `docs/specs/`, update its `INDEX.md` row, `spec.md` header, and `decisions.md` ADRs to `Status: Superseded`.
- **Living-Spec Modification (`Extends / Modifies: <prior-spec-id>`)**: Use when the earlier `In-Testing` or `Verified` specification remains active and only specific requirements are added (`[NEW]`), changed (`[MODIFIES REQ-xxx in <prior-spec-id>]`), or retired (`[DEPRECATED REQ-xxx in <prior-spec-id>]`).
  - **Frozen Parent Prose Rule**: The parent specification's requirement text and `AC-xxx` bodies are **never edited**. Only a counterpart lineage annotation (`Modified by <new-spec-id>` or `Deprecated by <new-spec-id>`) on the `REQ-xxx` heading in `<prior-spec>/spec.md` and `<prior-spec>`'s row in `INDEX.md` may be appended.

#### `Source Intent` Attribution Rule
Every `REQ-xxx` must include a `Source Intent` line:
- **Direct User Intent**: Quote the user's prompt or defect observation verbatim.
- **Standard / Architectural Derivation**: When a requirement is derived from an architectural decision or governing standard rather than a direct user quote, state `Derived from ADR-xxx (<reason>)` or `Derived from <standard-name> (<section>)`. **Never fabricate a user quote**; if a requirement has no attributable user intent or ADR derivation, stop and ask the user rather than guessing.

```markdown
# Specification: <Feature Title>

- **Feature ID**: `<YYYY-MM-DD-feature-slug>`
- **Type**: `new feature` <!-- new feature | enhancement | fix | refactor -->
- **Status**: `Planning` <!-- Planning | In-Progress | In-Testing | Verified | Superseded | Abandoned -->
- **Version**: `1.0.0`
- **Sign-off**: `Pending human "Proceed" approval`
- **Lineage**:
  - **Extends / Modifies**: `None` <!-- or [<prior-feature-id>](../<prior-feature-id>/spec.md) -->
  - **Supersedes**: `None` <!-- or [<old-feature-id>](../<old-feature-id>/spec.md) -->

## 1. Problem Statement & User Intent
State the concrete engineering problem, observed repository facts, and quote the exact user request or defect symptom that motivates this specification.

## 2. Non-Goals (Out of Scope)
Explicitly list what this specification will NOT do, change, or solve.

## 3. Normative Requirements (EARS Syntax)

### `REQ-001` [`NEW`]: <Concise Requirement Title>
- **Source Intent**: <Verbatim user prompt, defect observation, or "Derived from ADR-xxx (<reason>)">
- **Statement**: WHEN <trigger condition>, THE <system/module> SHALL <observable behavior>.
- **Acceptance Criteria**:
  - `AC-001-1` (Happy Path): <Deterministic, falsifiable condition that proves success>
  - `AC-001-2` (Error / Boundary Case): IF <invalid input, failure, or boundary condition>, THEN THE <system/module> SHALL <deterministic error handling>.

### `REQ-002` [`MODIFIES REQ-001 in <prior-spec-id>`]: <Modified Requirement Title>
- **Source Intent**: <Why the prior requirement is being changed>
- **Previous Contract**: <Exact summary of what `REQ-001` in `<prior-spec-id>` previously required>
- **Statement**: WHILE <state condition>, THE <system/module> SHALL <updated observable behavior>.
- **Acceptance Criteria**:
  - `AC-002-1` (Happy Path): <Updated falsifiable condition>
  - `AC-002-2` (Error / Boundary Case): <Updated boundary condition>

### `REQ-003` [`DEPRECATED REQ-004 in <prior-spec-id>`]: <Retired Requirement Title>
- **Deprecation & Migration Reason**: <Why `REQ-004` in `<prior-spec-id>` is retired and how existing callers/workflows migrate>
```

### 3.2 `decisions.md` Template (Anti-Strawman Append-Only ADRs + Gate 1 Table)

```markdown
# Architectural Decisions: <Feature Title>

- **Feature ID**: `<YYYY-MM-DD-feature-slug>`
- **Status**: `Planning` <!-- Matches spec.md package status or Accepted once approved -->

## `ADR-001`: <Decision Title>
- **Status**: `Accepted` <!-- Accepted | Superseded by ADR-yyy -->
- **Governs**: `REQ-001`, `REQ-002`
- **Context**: What technical constraint, coupling, or trade-off forces a decision here?
- **Options Considered**:
  1. **Option A (<Name>)**: <Concrete technical summary, affected files, and runtime behavior>
  2. **Option B (<Name>)**: <Second genuinely viable technical approach — never a fake strawman>
- **Decision**: Choose **Option A** because <specific engineering justification grounded in codebase>.
- **Trade-offs & Risks**: What are the concrete downsides, failure modes, or maintenance costs of Option A, and how are they mitigated?
- **Rejected Alternatives**: Why was Option B rejected for this specific context?
- **Blast Radius**: Exact modules/files impacted by this decision.

---

## Gate 1: Normative Source Self-Validation (`spec.md` & `decisions.md`)

| Gate 1 Check | Status | Verification Evidence |
| :--- | :--- | :--- |
| **1. Codebase Grounding** | `PASS` | <Exact existing files/symbols inspected> |
| **2. User Intent & Non-Goals** | `PASS` | <Every REQ cites honest Source Intent (user quote or ADR derivation); explicit Non-Goals listed> |
| **3. EARS & Falsifiable ACs** | `PASS` | <Every REQ uses EARS syntax with both Happy Path and Error/Boundary ACs> |
| **4. Zero Deferral Placeholders** | `PASS` | <Zero unresolved deferral placeholders in spec.md and decisions.md> |
| **5. Anti-Strawman ADR Debate** | `PASS` | <Every ADR compares >= 2 viable options with Trade-offs & Rejected Alternatives> |
| **6. Cross-Spec Lineage & Cascade** | `PASS` | <Type, Version, and Lineage headers present; counterpart INDEX.md / spec.md / decisions.md files updated> |
```

---

## 4. Step 3: Gate 1 — Self-Validation of Normative Source (STOP & CHECK)

**CRITICAL**: Before writing `design.md`, `tasks.md`, or `verification.md`, audit `spec.md` and `decisions.md` and record the completed **Gate 1 Self-Validation Table** at the bottom of `decisions.md`:

- [ ] **1. Codebase Grounding**: Did I read the real codebase files and verify that `spec.md` and `decisions.md` reference real modules and symbols?
- [ ] **2. User Intent & Non-Goals**: Does every `REQ-xxx` cite an honest `Source Intent` (verbatim user quote or explicit ADR/standard derivation, never a fabricated quote), and does `spec.md` include a non-empty `## Non-Goals` section?
- [ ] **3. EARS & Falsifiable ACs**: Is every `REQ-xxx` written in EARS notation with at least one Happy-Path `AC-xxx` and one Error/Boundary `AC-xxx`?
- [ ] **4. Zero Deferral Placeholders**: Are `spec.md` and `decisions.md` 100% free of unresolved deferral markers?
- [ ] **5. Anti-Strawman ADRs**: Does every `ADR-xxx` evaluate at least 2 realistic options and state concrete `Trade-offs & Risks` and `Rejected Alternatives` (preserving old ADR bodies append-only)?
- [ ] **6. Cross-Spec Consistency & Counterpart Cascade**: Does `spec.md` declare `Type`, `Version`, and `Lineage` (`Extends / Modifies` and `Supersedes`) in its header, and if it supersedes or modifies a prior spec, are the delta tags and counterpart files (`INDEX.md`, `<prior-spec>/spec.md` heading annotations with frozen requirement prose, `<prior-spec>/decisions.md`) updated consistently?

*If any check fails, fix `spec.md` or `decisions.md` first. Do NOT proceed to `design.md` or `tasks.md` while Gate 1 has any failing row.*

---

## 5. Step 4: Author the Derived Blueprint (`design.md`, `tasks.md`, `verification.md`)

Once Gate 1 passes all 6 checks:

### 5.1 `design.md` Template
```markdown
# Architecture & Design: <Feature Title>

- **Governing Spec**: [spec.md](./spec.md)
- **Governing Decisions**: [decisions.md](./decisions.md) (`ADR-001`)

## 1. Component & Symbol Map (Blast Radius)
| Requirement | Acceptance Criteria | Repository Path | Section / Symbol | Change Summary |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | `AC-001-1`, `AC-001-2` | `path/to/file` | `function_or_section` | <What changes and why> |

## 2. Data Structures, Interfaces & Control Flow
Specify exact type definitions, function signatures, state transitions, and invariants.

## 3. Error Handling, Edge Cases & Precedence
Map each boundary/error `AC-xxx` from `spec.md` to concrete error handling and recovery behavior.
```

### 5.2 `tasks.md` Template (With Per-AC Gate 2 Traceability Matrix)
```markdown
# Execution Tasks: <Feature Title>

- [ ] **Task 1 (`REQ-001`, `AC-001-1`, `AC-001-2`)**:
  - **Red**: Write failing test or validation check covering `AC-001-1` and `AC-001-2`.
  - **Green**: Implement minimal changes in `path/to/file` to satisfy `REQ-001`.
  - **Refactor**: Clean up duplication while keeping tests green.

---

## Gate 2: Derived File Self-Validation & Traceability Matrix (`design.md`, `tasks.md`, `verification.md`)

| Requirement ID | Acceptance Criteria | Governing ADR | Design Section (`design.md`) | Execution Task (`tasks.md`) | Verification Section (`verification.md`) | Gate 2 Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | `AC-001-1` | `ADR-001` | Section 1, 2 | `Task 1` | Section 1 (`AC-001-1`) | `PASS` |
| `REQ-001` | `AC-001-2` | `ADR-001` | Section 1, 3 | `Task 1` | Section 1 (`AC-001-2`) | `PASS` |

- **Zero Gold-Plating Check**: `PASS`
- **Zero Stale References Check**: `PASS`
```

### 5.3 `verification.md` Template
```markdown
# Verification Evidence: <Feature Title>

- **Governing Spec**: [spec.md](./spec.md)
- **Sign-off Record**:
  - **Transition `Planning` $\to$ `In-Progress`**: <Human "Proceed" approval date and quote>
  - **Transition `In-Progress` $\to$ `In-Testing`**: <Task completion & verification date>
  - **Transition `In-Testing` $\to$ `Verified`**: <Pending or completed human dogfooding sign-off>

## Run 1 — `<YYYY-MM-DD>` (Status: `In-Testing`)
- **Verified Requirements**: `REQ-001` (`AC-001-1`, `AC-001-2`)
- **Command Executed**: `<exact command>`
- **Verbatim Output**:
  ```text
  <exact terminal output>
  ```
```

---

## 6. Step 5: Gate 2 — Self-Validation of Derived Files (Before Asking Human to "Proceed")

Before presenting the specification package to the user for `"Proceed"` approval, complete the **Gate 2 Traceability Matrix** at the bottom of `tasks.md` and verify:
- [ ] **1. 100% Per-AC Forward Traceability**: Every `REQ-xxx` and every `AC-xxx` in `spec.md` has its own row in the Gate 2 table mapped to `decisions.md`, `design.md`, `tasks.md`, and `verification.md`.
- [ ] **2. 100% Backward Traceability (Zero Gold-Plating)**: Every component in `design.md` and every task in `tasks.md` maps back to an explicit `REQ-xxx` in `spec.md`. Remove any unmapped scope creep.
- [ ] **3. Registry Sync**: `docs/specs/INDEX.md` has an up-to-date 6-column row (`Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path`) for `<feature-id>` with status `Planning`.

Then present the summary to the user and wait for explicit **"Proceed"** approval before transitioning `Status` to `In-Progress` (and recording the `"Proceed"` sign-off in `spec.md` and `verification.md`).

> **Primary Agent Execution Boundary**: Once `Status` transitions to `In-Progress`, the Primary Agent coordinates the workstream and updates Markdown specification artifacts (`tasks.md`, `verification.md`), but **never directly modifies non-Markdown source code or the runtime/package/cluster environment** (neither via file tools nor via shell commands in `run_command`). Delegate all code mutations, test suites, builds, and environment changes to execution subagents.

---

## 7. Step 6: The 6-State Specification Lifecycle (`In-Testing` vs. `Verified`)

A specification is **NOT done** when the agent finishes coding and unit tests pass:

```
Planning ──(Gate 1+2 PASS + Human "Proceed")──► In-Progress ──(All Tasks [x] + verification.md)──► In-Testing ──(Real-World Usage + Human Sign-Off)──► Verified
   ▲                                                 ▲                                                 │                                                  │
   └──────────(Case 2 / Case 3 Design or Spec Bug)───┴───────────(Case 1 Implementation Bug)───────────┴──────────────────────────────────────────────────┘
```

| Status | Meaning & Entry Criteria |
| :--- | :--- |
| `Planning` | Initial authoring or active Case 2 / Case 3 revision of `spec.md`, `decisions.md`, `design.md`, and `tasks.md`. |
| `In-Progress` | Gate 1 + Gate 2 passed and human user gave explicit `"Proceed"` approval (recorded in `spec.md` `Sign-off`), OR a Case 1 implementation bug is actively being fixed via an open `- [ ]` task in `tasks.md`. |
| **`In-Testing`** | All tasks in `tasks.md` are `[x]` and automated test evidence is recorded in `verification.md`. The feature is now being dogfooded/tested in real usage. |
| **`Verified`** | The feature has survived real-world usage in `In-Testing` and the human user explicitly confirmed it works as intended (recorded in `spec.md` `Sign-off`). |
| `Superseded` | Replaced in full by a newer specification (`Supersedes` in the newer `spec.md`). |
| `Abandoned` | Explicitly cancelled by the human user. |

---

## 8. Step 7: The 3-Way Bug Decision Protocol

When a bug, test failure, or real-world edge case is discovered during `In-Progress`, `In-Testing`, or after `Verified`, **stop and classify the root cause into exactly one of three cases**:

### Case 1: Implementation Bug *(Spec & Design are right; Code/Test is wrong — Mints 0 New REQ IDs)*
- **Symptom**: `spec.md`, `decisions.md`, and `design.md` accurately describe the desired behavior, but the code has a logic bug, typo, or missing test assertion.
- **Action**:
  1. **Do NOT edit `spec.md` or `decisions.md` (mint 0 new `REQ` IDs).**
  2. Set `Status` to `In-Progress` (if currently `In-Testing` or `Verified`) and add a reproducer task `- [ ] Fix <bug symptom> (REQ-xxx, AC-xxx)` in `tasks.md` (or in a dedicated `Type: fix` child package citing the parent `REQ-xxx` IDs if isolating a standalone fix workstream).
  3. Reproduce with a failing test (TDD Red), fix the code (Green), check off `- [x]` in `tasks.md`, append the new test run to `verification.md`, and set `Status` to `In-Testing`.

### Case 2: Design / Architecture Flaw *(Spec is right; `design.md` or `ADR-xxx` failed in practice — Mints 0 New REQ IDs)*
- **Symptom**: The requirement in `spec.md` is valid, but the chosen technical approach in `decisions.md` / `design.md` hits an unforeseen constraint, performance bottleneck, or integration failure.
- **Action**:
  1. **Stop coding. Do NOT weaken `spec.md` to match a broken design (mint 0 new `REQ` IDs).**
  2. Set `Status` to `Planning`. In `decisions.md`, mark the broken `ADR-xxx` as `Status: Superseded by ADR-yyy` and append the new `ADR-yyy` explaining why `ADR-xxx` failed in practice.
  3. Re-run **Gate 1** (`decisions.md`), update `design.md` and `tasks.md` to reflect `ADR-yyy`, re-run **Gate 2** (`tasks.md`), and ask the human user to **"Proceed"** before resuming implementation (`In-Progress`).

### Case 3: Specification Gap or Flawed Requirement *(`spec.md` missed an edge case or had a wrong requirement — Mints/Modifies REQ IDs)*
- **Symptom**: Real-world usage reveals a missing requirement, a contradictory edge case, or a requirement in `spec.md` that produces undesirable behavior.
- **Action**:
  1. **Stop coding. Never silently diverge from `spec.md` in code.**
  2. Set `Status` to `Planning`. Either amend `spec.md` directly in-place (updating existing `REQ-xxx` IDs or minting new `[NEW]` `REQ-xxx` IDs when modifying an active `Planning`/`In-Progress` spec) or create a new delta specification (`Extends / Modifies: <prior-spec-id>`) that mints new delta `REQ-xxx` IDs tagged `[MODIFIES REQ-yyy in <prior-spec-id>]` / `[NEW]` with counterpart heading annotations (keeping the parent requirement prose frozen). *(Unlike Case 1 and Case 2 fixes, which mint 0 new `REQ` IDs, Case 3 updates or mints `REQ` IDs.)*
  3. Update `decisions.md` if architectural choices change, re-run **Gate 1** (`decisions.md`), cascade updates into `design.md` and `tasks.md`, re-run **Gate 2** (`tasks.md`), and obtain human **"Proceed"** approval before coding (`In-Progress`).
