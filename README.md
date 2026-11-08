# Spec-driven

A standalone skill and Google Antigravity plugin for writing, reviewing, and maintaining feature specifications grounded in actual code and user intent.

Each feature uses five documents in `docs/specs/<feature-id>/`: requirements in `spec.md`, architectural rationale in `decisions.md`, an implementation blueprint in `design.md`, traceable work in `tasks.md`, and planned checks plus actual evidence in `verification.md`. A shared index catalogs the packages.

The skill reviews requirements and decisions before deriving implementation plans, then checks acceptance-criterion coverage before execution. It distinguishes implementation defects, design flaws, and requirement changes. Passing checks leads to `In-Testing`; real usage and human confirmation are needed for `Verified`.

These are authoring and review practices, not automated enforcement or a guarantee of correctness. Keep documents proportionate to the feature and assess the evidence behind each conclusion.

## Use

Example requests:

- "Use $spec-driven to specify retry behavior for this queue worker."
- "Review this feature specification against the code and identify missing acceptance criteria."
- "Investigate this bug and update the affected spec-driven artifacts."

The skill supports new repositories and existing specifications. It does not require a particular editor, external skill, or multi-agent setup. Implementation follows the user's authorization; merely requesting a specification does not request implementation.

## Layout

- [SKILL.md](skills/spec-driven/SKILL.md): entrypoint, grounding, authoring, and validation workflow.
- [templates.md](skills/spec-driven/references/templates.md): the catalog and five document templates.
- [lifecycle.md](skills/spec-driven/references/lifecycle.md): status transitions, specification changes, and defect handling.
- [AGENTS.md](rules/AGENTS.md): optional always-on governance rule for Google Antigravity plugin installations or repository-root `AGENTS.md`.
- [plugin.json](plugin.json): Google Antigravity plugin manifest.

## Install in Google Antigravity

- **As a full plugin (includes always-on `rules/AGENTS.md` + `spec-driven` skill):**
  Clone or symlink this repository into `~/.gemini/config/plugins/spec-driven-plugin`.
- **As an on-demand standalone skill only:**
  Copy `skills/spec-driven` (including `references/`) into `~/.gemini/config/skills/spec-driven` (or `~/.gemini/skills/spec-driven`).

## Install in Codex

Copy the entire `skills/spec-driven` directory, including `references`, into `$CODEX_HOME/skills/spec-driven`, or `~/.codex/skills/spec-driven` when `CODEX_HOME` is unset. Review an existing installation before replacing it.

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

The installed skill is available on the next turn. The skill consists only of Markdown; standalone skill installation does not add global rules or executable hooks.
