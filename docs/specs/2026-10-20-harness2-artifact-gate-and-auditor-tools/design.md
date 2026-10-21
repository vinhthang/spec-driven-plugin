# Technical Design: Harness² Referenced Artifact Verification Gate & Traceability Auditor Tool Permissions

## 1. Component Changes

### 1.1 `agents/traceability-auditor.md` (`REQ-023`)
Update YAML frontmatter line 5:
```yaml
tools: [read_file, view_file, write_file, write_to_file]
```

### 1.2 `scripts/spec_checker.py` — `check_referenced_artifacts()` & `REQ_ID_PATTERN` (`REQ-024`, `REQ-025`)
- Update `REQ_ID_PATTERN = re.compile(r"\b(?:REQ|FLOW|ALIGN)-(?:[A-Z0-9]+-)*\d+\b")`.
- Add `ARTIFACT_REF_RE = re.compile(r"(?<![/\w.-])((?:scripts|tests)/[A-Za-z0-9_.\-/]+\.py)\b")` and `check_referenced_artifacts(spec_dir: Path, repo_root: Optional[Path] = None) -> List[str]`.
- Wire `check_referenced_artifacts(spec_dir)` into `validate_spec_package()` when `verify_evidence=True`.

### 1.3 `scripts/spec-gate.py` — Global `~/.gemini/config/` Allowance (`REQ-026`)
- Extend `is_allowed_runtime_artifact_path(target_path: Path) -> bool` to recognize contiguous `(".gemini", "config", "rules")`, `(".gemini", "config", "scripts")`, `(".gemini", "config", "skills")`, and `~/.gemini/config/hooks.json`.


### 1.4 `scripts/spec-gate.py` — `/goal` Autonomous Approval & Antigravity 2.0 Tool Schemas (`REQ-027`, `REQ-028`)
- Extend `FILE_MUTATION_TOOLS` with `write_file`, `edit_file`, `default_api:write_file`, `default_api:edit_file`, `client:write_file`, `client:edit_file`.
- Extract `args.get("Path")` alongside `TargetFile` / `target_file` / `file_path` / `path`, and support `Target` / `Replacement` in `is_unauthorized_status_promotion()`.
- Normalize flat `invoke_subagent` `args` (`[args]` when `"Subagents"` is absent and `"Prompt"` or `"TypeName"` is present).
- In `has_recent_user_approval()`, return `True` if `/goal` appears in the user input stream.
- Implement `extract_prompt_workspaces(all_prompts: str, candidate_workspaces: List[Path]) -> List[Path]` (`REQ-028`):
  - Matches both `[ws for ws in candidate_workspaces if str(ws) in all_prompts]` and any absolute path `/[A-Za-z0-9_.\-/]+` in `all_prompts` whose `resolve_target_workspace()` parent contains `docs/specs/INDEX.md`.
