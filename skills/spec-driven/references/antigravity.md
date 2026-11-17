# Antigravity 2.0 and Gemini 4 orchestration

Use this reference when running `spec-driven` inside Google Antigravity 2.0 (especially under Gemini 4 `Argon` / `Carbon` or Claude `Opus` thinking models, or alongside `attention-guard`). Standalone Codex installations can ignore this file.

## Tiered role and model split

Under a thinking Primary Agent (Gemini 4 `Carbon` / `Argon`), the Primary Agent authors Markdown (`docs/specs/**`, `README.md`, Brain Artifacts) directly and delegates all non-Markdown edits, test suites, and builds.

| Lifecycle step | Execution surface | Model tier | Workspace mode |
| --- | --- | --- | --- |
| Scope disambiguation (`/grill-me`) | Primary Agent (`ask_question`, `(Recommended)` first) | Gemini 4 (`Argon` / `Carbon`) | `inherit` |
| Broad brownfield discovery (pre-Gate 1) | `invoke_subagent(TypeName="research")` | `flash_lite` or `flash` | `inherit` (read-only) |
| Authoring 5 spec docs + read-only `validate_specs.py` | Primary Agent (`write_file`, `edit_file`) | Gemini 4 (`Argon` / `Carbon`) | `inherit` |
| 1–2 coupled or sequential tasks (`tasks.md`) | `invoke_subagent(TypeName="self")` | `flash` | `inherit` (or `share` if parallel) |
| 3+ disjoint tasks or staged fan-out/fan-in | `run_workflow` (`phase`, `parallel`, `pipeline`, `agent`) | `flash` (authors), `pro` (hard verifier) | `share` (authors), `inherit` (readers) |
| Multi-module peer collaboration (`/teamwork`) | Native `swarm` (`swarm`, `post_message`, `read_board`, `swarm_wait`) | Omit `model` (inherits coordinator model) | `share` (authors), `inherit` (`@verifier`) |
| Independent `In-Testing` review or root-cause diagnosis | Distinct `invoke_subagent(TypeName="self")` | `flash` first-line; `pro` for deep algorithmic bugs | `inherit` |

## Partitioning `tasks.md` for parallel workspaces

Give every `## Task N` in `tasks.md` an explicit `- Files:` write-set alongside `- Dependencies:` and `- Covers:`:

- **Safe for parallel `Workspace="share"` / `"branch"`:** `Dependencies: None` (or already completed) **and** strictly disjoint `Files:` sets (including shared test files, `__init__.py`, and lockfiles).
- **Must serialize:** Tasks with overlapping `Files:` or sequential `Dependencies:`.
- **Landing isolated workspaces:** Workers running in `Workspace="share"` or `"branch"` commit on their isolated branch; merge or cherry-pick verified commits into the primary working copy before updating `verification.md` or calling `swarm{action:"kill"}` (`kill` deletes the worker's workspace).

### `run_workflow` pattern for 3+ disjoint tasks

Use `run_workflow` when orchestration is code (fan-out over disjoint `tasks.md` slices with structured JSON `finish` schemas, followed by serial integration checks). Include `[AGY_WORKFLOW_WORKER]` in each `agent()` prompt so Attention Guard recognizes workflow agents even if `model` defaults to `"inherit"`, and arm a 300s `schedule` watchdog if the workflow backgrounds (`WaitMsBeforeAsync=0`):

```python
task_slices = [
    {"id": "Task 1", "files": "src/auth/token.py, tests/test_token.py", "acs": "AC-010-1, AC-010-2"},
    {"id": "Task 2", "files": "src/auth/jwks.py, tests/test_jwks.py", "acs": "AC-011-1, AC-011-2"},
]

phase("Implement disjoint tasks")
results = await parallel(
    task_slices,
    lambda t: agent(
        f"[AGY_WORKFLOW_WORKER] Execute {t['id']} in docs/specs/2026-11-18-auth/tasks.md. "
        f"Own ONLY {t['files']} covering {t['acs']}. Run pytest and commit on your share branch.",
        schema={
            "type": "object",
            "required": ["task_id", "passed", "commit_sha", "test_cmd"],
            "properties": {
                "task_id": {"type": "string"},
                "passed": {"type": "boolean"},
                "commit_sha": {"type": "string"},
                "test_cmd": {"type": "string"},
            },
        },
        role=f"Implement {t['id']}",
        workspace="share",
        model="flash",
    ),
)
for r in results:
    log(r)
```

### Native `swarm` pattern (`/teamwork`)

Reserve `swarm` for large multi-component specs that benefit from live peer coordination and dedicated `@verifier` review loops on a shared message board:

1. Spawn one named author per disjoint `Files:` slice with `workspace:"share"` (leaving `model` unset per the `swarm` contract) and one `@verifier` on `workspace:"inherit"` per 2–4 authors.
2. State exact owned `Files:`, off-limits paths, target `AC-NNN-M` criteria, and required test output in each worker's public `brief`.
3. Reference prior board reports by sequence number (`@verifier check #4 against AC-010-1 and AC-010-2`)—never copy-paste worker outputs across messages.
4. Park the coordinator with `swarm_wait{since: LAST}` (zero-cost board sleep; do **not** arm `schedule` timers to poll the board). Land verified `share` branches into the primary working copy before calling `swarm{action:"kill"}`.

## Zero-duplication Brain Artifact bridge

When Antigravity planning or Attention Guard artifacts are active alongside `docs/specs/<feature-id>/`, `docs/specs/` remains the single source of truth:

- **`implementation_plan.md` (`RequestFeedback: true`):** Never copy-paste the five spec documents into `<artifact-dir>/implementation_plan.md`. After Gate 1 and Gate 2 pass (`Execution: Not run.`), write a concise ~20–30 line approval brief linking to `docs/specs/<feature-id>/{spec,decisions,design,tasks,verification}.md`, summarizing Gate 1/2 readiness, any `[PROVISIONAL]` / `BLOCKED` scope, and the selected execution surface (`invoke_subagent`, `run_workflow`, or `swarm`).
- **`/goal` autonomous execution:** When the user authorizes end-to-end execution via `/goal`, advance settled scope through Gate 1 -> Gate 2 -> implementation -> `In-Testing` (appending real `### Run N` command evidence in `verification.md`), then stop at `In-Testing`. Never self-promote to `Verified` without real-world usage observations and explicit human confirmation.
- **`walkthrough.md`:** Write a brief completion summary in `<artifact-dir>/walkthrough.md` linking directly to `docs/specs/<feature-id>/verification.md#run-1--<yyyy-mm-dd>` (matching the `### Run 1 — <YYYY-MM-DD>` heading slug) to satisfy Attention Guard's Stop-hook Walkthrough Gate without duplicating run logs.
