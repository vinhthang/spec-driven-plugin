# Antigravity 2.0 multi-agent orchestration

Use this reference when running `spec-driven` inside Google Antigravity 2.0 alongside `attention-guard`. Standalone Codex installations can ignore this file.

## Pragmatic execution and delegation split

Execute focused specification work, 1–2 file implementations, config updates, git operations, and `rtk`-filtered test checks directly in the Primary Agent. Delegate to isolated workers when work spans 3+ disjoint file slices, parallel workstreams, broad read-only exploration, or noisy multi-step builds—leaving worker `model` unset (`inherit`) by default unless the user requests a specific model or a lightweight read-only `research` sweep fits `flash_lite`.

| Lifecycle step | Execution surface | Model tier | Workspace mode |
| --- | --- | --- | --- |
| Scope disambiguation (`/grill-me`) | Primary Agent (`ask_question`, `(Recommended)` first) | Active model | `inherit` |
| Broad brownfield discovery (pre-Gate 1) | `invoke_subagent(TypeName="research")` | `flash_lite` (optional) or `inherit` | `inherit` (read-only) |
| Authoring 5 spec docs + `validate_specs.py` | Primary Agent (`write_file`, `edit_file`, `run_command`) | Active model | `inherit` |
| 1–2 coupled or sequential tasks (`tasks.md`) | Primary Agent directly (or `invoke_subagent(TypeName="self")` if noisy) | Active model / `inherit` | `inherit` |
| 2 parallel disjoint tasks (`tasks.md`) | Concurrent `invoke_subagent(TypeName="self")` calls in one turn | `inherit` (default) | `share` |
| 3+ disjoint tasks or staged fan-out/fan-in | `run_workflow` (`phase`, `parallel`, `pipeline`, `agent`) | `inherit` (default; omit `model`) | `share` (authors), `inherit` (readers) |
| Multi-module peer collaboration (`/teamwork`) | Native `swarm` (`swarm`, `post_message`, `read_board`, `swarm_wait`) | Omit `model` (inherits coordinator) | `share` (authors), `inherit` (`@verifier`) |

## Partitioning `tasks.md` for parallel workspaces

Give every `## Task N` in `tasks.md` an explicit `- Files:` write-set alongside `- Dependencies:` and `- Covers:`:

- **Safe for parallel `Workspace="share"` / `"branch"`:** `Dependencies: None` (or already completed) **and** strictly disjoint `Files:` sets (including shared test files, `__init__.py`, and lockfiles).
- **Must serialize:** Tasks with overlapping `Files:` or sequential `Dependencies:`.
- **Landing isolated workspaces:** Workers running in `Workspace="share"` or `"branch"` commit on their isolated branch and report concise status (modified files, commit SHA, and test counts—never raw ANSI logs or full tracebacks). Merge or cherry-pick verified commits into the primary working copy before updating `verification.md` or calling `swarm{action:"kill"}` (`kill` deletes the worker's workspace).

### `run_workflow` pattern for 3+ disjoint tasks

Use `run_workflow` when orchestration is code (fan-out over disjoint `tasks.md` slices with structured JSON `finish` schemas, followed by serial integration checks). Omit `model` so workers inherit the active model, and rely on Antigravity's reactive wakeup notification when a backgrounded workflow completes (no polling timers needed):

```python
task_slices = [
    {"id": "Task 1", "files": "src/auth/token.py, tests/test_token.py", "acs": "AC-010-1, AC-010-2"},
    {"id": "Task 2", "files": "src/auth/jwks.py, tests/test_jwks.py", "acs": "AC-011-1, AC-011-2"},
    {"id": "Task 3", "files": "src/auth/middleware.py, tests/test_middleware.py", "acs": "AC-012-1, AC-012-2"},
]

phase("Implement disjoint tasks")
results = await parallel(
    task_slices,
    lambda t: agent(
        f"Execute {t['id']} in docs/specs/2026-11-18-auth/tasks.md. "
        f"Own ONLY {t['files']} covering {t['acs']}. Run rtk test pytest and commit on your share branch.",
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

When Antigravity planning artifacts are active alongside `docs/specs/<feature-id>/`, `docs/specs/` remains the single source of truth:

- **`implementation_plan.md` (`RequestFeedback: true`):** Never copy-paste the five spec documents into `<artifact-dir>/implementation_plan.md`. After Gate 1 and Gate 2 pass (`Execution: Not run.`), write a concise ~20–30 line approval brief linking to `docs/specs/<feature-id>/{spec,decisions,design,tasks,verification}.md`, summarizing Gate 1/2 readiness, any `[PROVISIONAL]` / `BLOCKED` scope, and the selected execution topology (direct Primary Agent, `invoke_subagent`, `run_workflow`, or `swarm`).
- **`/goal` autonomous execution:** When the user authorizes end-to-end execution via `/goal`, advance settled scope through Gate 1 -> Gate 2 -> implementation -> `In-Testing` (appending real `### Run N` command evidence in `verification.md`), then stop at `In-Testing`. Never self-promote to `Verified` without real-world usage observations and explicit human confirmation.
- **`walkthrough.md`:** When creating a completion summary in `<artifact-dir>/walkthrough.md`, link directly to `docs/specs/<feature-id>/verification.md#run-1--<yyyy-mm-dd>` (matching the `### Run 1 — <YYYY-MM-DD>` heading slug) rather than duplicating run logs.
