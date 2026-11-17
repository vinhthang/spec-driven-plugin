# Spec-driven

A standalone skill and Google Antigravity plugin for writing, reviewing, and maintaining feature specifications grounded in actual code and user intent.

Each feature uses five proportionate documents in `docs/specs/<feature-id>/`: requirements in `spec.md`, architectural rationale in `decisions.md`, an implementation blueprint in `design.md`, traceable work in `tasks.md`, and planned checks plus actual run evidence in `verification.md`. A shared `docs/specs/INDEX.md` catalog tracks status and repository-wide `REQ-NNN` / `ADR-NNN` allocations.

The workflow validates normative requirements and decisions (**Gate 1**) before deriving implementation plans, then verifies acceptance-criterion traceability (**Gate 2**) before execution. It separates implementation bugs (**Case 1**), architecture/design failures (**Case 2**), and requirement changes (**Case 3**), using `First entered In-Testing` to protect tested requirement history via linked deltas. Passing automated checks leads to `In-Testing`; real usage and explicit human confirmation are required for `Verified`.

## Use

Example requests:

- "Use $spec-driven to specify retry jitter for `src/worker/retry.py`."
- "Use $spec-driven to review `docs/specs/2026-11-10-payment-webhook/` against the live code."
- "Investigate this bug and update the affected spec-driven package."

Implementation follows explicit human authorization; requesting a specification or review does not authorize code changes.

## Layout

- [SKILL.md](skills/spec-driven/SKILL.md): entrypoint covering grounding, authoring, Gates 1 & 2, and read-only package reviews.
- [templates.md](skills/spec-driven/references/templates.md): `INDEX.md` and five-document templates, `[PROVISIONAL]` stubs, delta patterns, and run-evidence format.
- [lifecycle.md](skills/spec-driven/references/lifecycle.md): six-state transitions, `First entered In-Testing` routing, delta chains, three defect cases, `[PROVISIONAL]` descoping, and out-of-band drift.
- [example.md](skills/spec-driven/references/example.md): complete, right-sized 1-requirement calibration example ("one-sitting rule").
- [validate_specs.py](skills/spec-driven/scripts/validate_specs.py): optional zero-dependency Python 3 stdlib CLI linter for verifying `INDEX.md` sync, unique IDs, `#heading-anchors`, and Gate 1/2 completeness (read-only, zero lifecycle hooks).
- [openai.yaml](skills/spec-driven/agents/openai.yaml): OpenAI Codex UI metadata.
- [AGENTS.md](rules/AGENTS.md) & [plugin.json](plugin.json): Google Antigravity plugin rule and manifest.
- [tests/test_validate_specs.py](tests/test_validate_specs.py): repository test suite (not copied into standalone skill installations).

## Install in Google Antigravity

- **Full plugin (compact always-on routing rule + `spec-driven` skill):**
  Clone or symlink this repository into `~/.gemini/config/plugins/spec-driven-plugin`.
- **Standalone on-demand skill only:**
  Copy or symlink `skills/spec-driven` into `~/.gemini/config/skills/spec-driven`.

## Install in Codex

Copy or symlink `skills/spec-driven` into `$CODEX_HOME/skills/spec-driven` (`~/.codex/skills/spec-driven` when `CODEX_HOME` is unset). Review any existing installation before replacing it.

From macOS/Linux (`bash` / `zsh`):

```bash
skill_home="${CODEX_HOME:-$HOME/.codex}"
skill_dest="$skill_home/skills/spec-driven"
[ ! -e "$skill_dest" ] || { echo "Review the existing installation at $skill_dest before replacing it." >&2; exit 1; }
mkdir -p "$(dirname "$skill_dest")"
cp -R ./skills/spec-driven "$skill_dest"
```

From Windows (`PowerShell`):

```powershell
$skillHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillDestination = Join-Path $skillHome 'skills/spec-driven'
if (Test-Path -LiteralPath $skillDestination) { throw 'Review the existing installation before replacing it.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $skillDestination) -Force | Out-Null
Copy-Item -LiteralPath './skills/spec-driven' -Destination $skillDestination -Recurse
```

Standalone skill installation adds no global rules and registers zero lifecycle hooks.
