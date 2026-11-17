# Golden calibration example (right-sized 1-requirement package)

This example illustrates appropriate brevity ("one-sitting rule") for a focused, constraint-determined enhancement at `Status: In-Testing` (`docs/specs/2026-11-18-queue-retry-jitter/`). Notice how constrained rationale omits an artificial `ADR` block, Gate 1 and Gate 2 cite concrete facts in single lines, and every cross-file anchor resolves cleanly.

## `docs/specs/INDEX.md`

```markdown
# Feature specifications

| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |
| --- | --- | --- | --- | --- | --- |
| 2026-11-18-queue-retry-jitter | Bounded jitter on worker retry backoff | In-Testing | REQ-001 | None | [spec](./2026-11-18-queue-retry-jitter/spec.md) |
```

## `docs/specs/2026-11-18-queue-retry-jitter/spec.md`

```markdown
# Bounded jitter on worker retry backoff

- Feature ID: 2026-11-18-queue-retry-jitter
- Type: enhancement
- Status: In-Testing
- First entered In-Testing: 2026-11-18
- Related specifications: None

## Problem and source intent

User request: "Add full jitter to `compute_backoff_ms` in `src/worker/retry.py` so synchronized retries stop spiking Redis after a transient outage, and go ahead and implement it."

## Repository grounding

`src/worker/retry.py::compute_backoff_ms(attempt: int, base_ms: int = 200, cap_ms: int = 10_000) -> int` currently returns deterministic `min(cap_ms, base_ms * (2 ** attempt))` and is tested in `tests/test_retry.py`. Callers in `src/worker/runner.py` already accept any non-negative integer delay in milliseconds.

## Non-goals

- Changing `base_ms`, `cap_ms`, maximum retry count, or dead-letter routing in `src/worker/runner.py`.

## Requirements

### REQ-001: Full-jitter retry delay with deterministic RNG injection

- Source intent: User request ("Add full jitter to `compute_backoff_ms`...").
- Statement: WHEN `compute_backoff_ms` calculates a retry delay for `attempt >= 0`, THE retry module SHALL return an integer sampled uniformly from `[0, min(cap_ms, base_ms * (2 ** attempt))]` using an injectable `random.Random` instance (defaulting to module RNG).
- AC-001-1 — Success: For `attempt=3, base_ms=200, cap_ms=10_000`, `compute_backoff_ms` returns values within `[0, 1600]` across seeded samples and reproduces identical delays given the same `rng` seed.
- AC-001-2 — Boundary/failure: IF `attempt < 0` or `base_ms <= 0` or `cap_ms < base_ms`, THEN `compute_backoff_ms` SHALL raise `ValueError` without sleeping or mutating worker state.

## Assumptions and owner-deferred questions

- Reversible assumption: Optional keyword parameter `rng: random.Random | None = None` preserves backward compatibility for existing positional callers in `src/worker/runner.py`.

## Approvals and lifecycle history

- 2026-11-18 (`Planning -> In-Progress`): Authorized in initial user prompt ("go ahead and implement it") covering `REQ-001` after Gate 1 and Gate 2 passed.
- 2026-11-18 (`In-Progress -> In-Testing`): Task 1 and [Run 1](./verification.md#run-1--2026-11-18) passed; awaiting production Redis retry telemetry confirmation for `Verified`.
```

## `docs/specs/2026-11-18-queue-retry-jitter/decisions.md`

```markdown
# Decisions: Bounded jitter on worker retry backoff

Governing specification: [spec.md](./spec.md)

## Architectural rationale

- Governs: REQ-001

Existing `src/worker/runner.py` callers invoke `compute_backoff_ms(attempt)` synchronously with stdlib-only dependencies. Adding an optional `rng: random.Random | None = None` parameter and calling `(rng or _DEFAULT_RNG).randint(0, ceiling)` satisfies full-jitter sampling and deterministic unit testing with zero external dependencies and zero caller signature breaks, so no separate `ADR` block is warranted.

## Gate 1: normative review

| Check | Status | Evidence / required correction |
| --- | --- | --- |
| Codebase grounding | PASS | Verified `src/worker/retry.py::compute_backoff_ms`, `src/worker/runner.py`, and `tests/test_retry.py`. |
| Attributable intent and explicit scope | PASS | `REQ-001` traces directly to user prompt; `runner.py` retry limits excluded in `Non-goals`. |
| Observable requirements and meaningful acceptance criteria | PASS | `AC-001-1` checks bounded seeded range `[0, 1600]`; `AC-001-2` checks invalid-input `ValueError`. |
| Assumptions and owner-deferred questions are explicit | PASS | Optional `rng` keyword compatibility assumption recorded; zero `TODO`/`[PROVISIONAL]` items. |
| Architectural rationale respects requirements | PASS | Constrained rationale governs `REQ-001` without altering `runner.py` callers. |
| IDs, references, and revision route are consistent | PASS | Fresh package `REQ-001` (`AC-001-1`, `AC-001-2`) registered in `docs/specs/INDEX.md`. |
```

## `docs/specs/2026-11-18-queue-retry-jitter/design.md`

```markdown
# Design: Bounded jitter on worker retry backoff

Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)

## Components

| Requirement / AC | Path and symbol | Responsibility / change |
| --- | --- | --- |
| REQ-001 / AC-001-1, AC-001-2 | `src/worker/retry.py::compute_backoff_ms`, `tests/test_retry.py` | Validate inputs, compute `ceiling = min(cap_ms, base_ms * (2 ** attempt))`, return `(rng or _DEFAULT_RNG).randint(0, ceiling)`. |

## Interfaces and flow

- Signature: `compute_backoff_ms(attempt: int, base_ms: int = 200, cap_ms: int = 10_000, *, rng: random.Random | None = None) -> int` using module-level `_DEFAULT_RNG = random.Random()`.

## Boundaries and recovery

- Raise `ValueError("invalid backoff parameters")` before exponentiation whenever `attempt < 0`, `base_ms <= 0`, or `cap_ms < base_ms`.

## Dependencies and unresolved design work

None.
```

## `docs/specs/2026-11-18-queue-retry-jitter/tasks.md`

```markdown
# Tasks: Bounded jitter on worker retry backoff

Sources: [spec.md](./spec.md), [design.md](./design.md)

## Task 1: Add seeded full-jitter sampling and input guards to `compute_backoff_ms`

- [x] Complete the work and its applicable checks.
- Covers: REQ-001 / AC-001-1, AC-001-2
- Dependencies: None
- Blocked by: None
- Work: Write failing unit tests in `tests/test_retry.py` for seeded jitter bounds and `ValueError` boundaries, then implement `rng` sampling and guards in `src/worker/retry.py`.
- Completion evidence: `pytest -q tests/test_retry.py` passed (`4 passed`), recorded in [Run 1](./verification.md#run-1--2026-11-18).

## Gate 2: traceability and readiness

| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | AC-001-1 | [Rationale](./decisions.md#architectural-rationale) | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-add-seeded-full-jitter-sampling-and-input-guards-to-compute_backoff_ms) | [AC-001-1](./verification.md#ac-001-1-req-001) | PASS — seeded range check mapped |
| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-add-seeded-full-jitter-sampling-and-input-guards-to-compute_backoff_ms) | [AC-001-2](./verification.md#ac-001-2-req-001) | PASS — boundary error check mapped |

- Backward scope check: PASS — only `retry.py` and `test_retry.py` touched, serving `REQ-001`.
- Reference and catalog consistency: PASS — all anchors and `INDEX.md` verified.
```

## `docs/specs/2026-11-18-queue-retry-jitter/verification.md`

````markdown
# Verification: Bounded jitter on worker retry backoff

Governing specification: [spec.md](./spec.md)

## Planned checks

### AC-001-1 (REQ-001)

- Method: Unit test `test_compute_backoff_seeded_full_jitter` in `tests/test_retry.py` sampling 200 calls with `random.Random(42)` at `attempt=3, base_ms=200, cap_ms=10_000`.
- Expected outcome: Every sample is in `0 <= delay <= 1600`, distinct values occur, and re-seeding `Random(42)` reproduces the exact sequence.
- Execution: [Run 1](#run-1--2026-11-18)

### AC-001-2 (REQ-001)

- Method: Parametrized unit test `test_compute_backoff_rejects_invalid_bounds` in `tests/test_retry.py` passing `attempt=-1`, `base_ms=0`, and `cap_ms=100 < base_ms=200`.
- Expected outcome: Each call raises `ValueError`.
- Execution: [Run 1](#run-1--2026-11-18)

## Execution evidence

### Run 1 — 2026-11-18

- Checked: REQ-001 / AC-001-1, AC-001-2 (`local pytest, Python 3.12`)
- Command: `pytest -q tests/test_retry.py` (exit code: `0`)
- Output excerpt:
  ```text
  ....                                                                     [100%]
  4 passed in 0.03s
  ```
- Result: AC-001-1 `PASS`, AC-001-2 `PASS` — seeded full-jitter bounds, determinism, and `ValueError` guards verified.

## Real-world observations

No real-world confirmation has been recorded.
````
