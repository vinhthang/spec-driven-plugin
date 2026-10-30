#!/usr/bin/env python3
"""Mechanical Pre-Tool Spec Gate Hook (REQ-031).

Intercepts subagent dispatch and direct file-mutation tools to prevent unauthorized
code modifications when no active, approved specification package exists in docs/specs/.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SUBAGENT_TOOLS = {"invoke_subagent", "default_api:invoke_subagent", "client:invoke_subagent"}

FILE_MUTATION_TOOLS = {
    "write_to_file", "replace_file_content", "multi_replace_file_content",
    "client:write_to_file", "client:replace_file_content", "client:multi_replace_file_content",
    "default_api:write_to_file", "default_api:replace_file_content", "default_api:multi_replace_file_content",
    "write_file", "default_api:write_file", "client:write_file",
    "edit_file", "default_api:edit_file", "client:edit_file",
}

MUTATION_KEYWORDS = {
    "implement", "modify", "compiler", "executor", "builder", "patch", "write_to_file", "replace_file_content",
}

EXEMPT_ROLES = {"research", "codebase researcher", "diagnostician"}


def load_spec_checker() -> Tuple[Optional[Any], Optional[str]]:
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        import spec_checker
        return spec_checker, None
    except Exception as exc:
        return None, str(exc)


def is_allowed_runtime_artifact_path(target_path: Path) -> bool:
    """Check if path has contiguous (.gemini, antigravity, brain|scratch) parts or matches AGY_RUNTIME_ARTIFACT_DIR."""
    resolved = target_path.resolve()
    parts = resolved.parts
    valid_prefixes = {
        (".gemini", "antigravity", "brain"),
        (".gemini", "antigravity", "scratch"),
        (".gemini", "config", "rules"),
        (".gemini", "config", "scripts"),
        (".gemini", "config", "skills"),
    }
    for i in range(len(parts) - 2):
        if parts[i:i + 3] in valid_prefixes:
            return True

    if resolved.name == "hooks.json":
        for i in range(len(parts) - 1):
            if parts[i:i + 2] == (".gemini", "config"):
                return True

    custom_artifact_dir = os.environ.get("AGY_RUNTIME_ARTIFACT_DIR")
    if custom_artifact_dir and custom_artifact_dir.strip():
        try:
            custom_path = Path(custom_artifact_dir).resolve()
            if resolved.is_relative_to(custom_path):
                return True
        except (ValueError, RuntimeError):
            pass

    return False


def get_candidate_workspaces(payload: Dict[str, Any]) -> List[Path]:
    """Resolve candidate workspaces from env, cwd, and workspacePaths."""
    candidates: List[Path] = []
    seen = set()

    def add_path(p_str: Optional[str]):
        if p_str and isinstance(p_str, str) and p_str.strip():
            try:
                resolved = Path(p_str.strip()).resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    candidates.append(resolved)
            except Exception:
                pass

    add_path(os.environ.get("AGY_ACTIVE_WORKSPACE"))
    add_path(payload.get("cwd"))

    ws_paths = payload.get("workspacePaths")
    if isinstance(ws_paths, list):
        for wp in ws_paths:
            add_path(wp)

    if not candidates:
        fallback = Path(os.getcwd()).resolve()
        candidates.append(fallback)

    return candidates


def resolve_target_workspace(resolved_target: Path, candidate_workspaces: List[Path]) -> Optional[Path]:
    """Resolve governing workspace for target file against candidates or filesystem markers."""
    for ws in candidate_workspaces:
        try:
            if resolved_target.is_relative_to(ws):
                return ws
        except (ValueError, RuntimeError):
            pass

    for parent in [resolved_target] + list(resolved_target.parents):
        try:
            if (parent / "docs" / "specs").is_dir() or (parent / ".git").exists():
                return parent
        except Exception:
            pass

    return None


def extract_prompt_workspaces(all_prompts: str, candidate_workspaces: List[Path]) -> List[Path]:
    """Extract mentioned workspaces from prompt text via direct match or file path resolution."""
    mentioned = [ws for ws in candidate_workspaces if str(ws) in all_prompts]
    seen = {ws.resolve() for ws in mentioned}
    for p_str in re.findall(r"(/[A-Za-z0-9_.\-/]+)", all_prompts):
        try:
            p = Path(p_str)
            if p.exists() or p.parent.exists():
                ws = resolve_target_workspace(p.resolve(), candidate_workspaces)
                if ws:
                    ws_res = ws.resolve()
                    if ws_res not in seen and (ws_res / "docs" / "specs" / "INDEX.md").is_file():
                        seen.add(ws_res)
                        mentioned.append(ws)
        except Exception:
            continue
    return mentioned


def _project_file_text(disk_text: str, args: Dict[str, Any], file_label: str = "file") -> Tuple[Optional[str], Optional[str]]:
    """Helper to apply tool args mutation to in-memory file content."""
    target_content = args.get("TargetContent") or args.get("Target")
    replacement_content = args.get("ReplacementContent") if "ReplacementContent" in args else args.get("Replacement")
    if target_content is not None or replacement_content is not None:
        target_content = target_content or ""
        replacement_content = replacement_content or ""
        if not target_content or target_content not in disk_text:
            return None, f"TargetContent for {file_label} replacement was empty or not found on disk."
        return disk_text.replace(target_content, replacement_content, 1), None
    elif "ReplacementChunks" in args and isinstance(args.get("ReplacementChunks"), list):
        projected_text = disk_text
        chunks = args.get("ReplacementChunks", [])
        for chunk in chunks:
            tc = chunk.get("TargetContent") or chunk.get("Target") or ""
            rc = chunk.get("ReplacementContent") or chunk.get("Replacement") or ""
            if not tc or tc not in projected_text:
                return None, f"ReplacementChunk TargetContent was empty or not found in {file_label}."
            projected_text = projected_text.replace(tc, rc, 1)
        return projected_text, None
    elif args.get("Append"):
        content = args.get("CodeContent") or args.get("Content") or ""
        return disk_text + "\n" + content, None
    else:
        content = args.get("CodeContent") or args.get("Content") or args.get("ReplacementContent") or args.get("Replacement") or ""
        return content, None


def has_recent_user_approval(payload: Dict[str, Any]) -> bool:
    """Inspect transcriptPath for explicit user approval (Proceed/Approved) or active /goal session."""
    transcript_path_str = payload.get("transcriptPath", "")
    if not transcript_path_str or not isinstance(transcript_path_str, str):
        return False
    transcript_path = Path(transcript_path_str)
    if not transcript_path.is_file():
        return False

    user_turns: List[str] = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    step = json.loads(line_str)
                    if str(step.get("source", "")).startswith("USER") and step.get("type") == "USER_INPUT":
                        content = step.get("content", "")
                        clean = re.sub(r"<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>", "", str(content))
                        user_turns.append(clean)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return False

    if not user_turns:
        return False

    if "/plan" in user_turns[-1].lower():
        return False

    # Check for scoped /goal in user turns (REQ-032, ADR-023)
    goal_pattern = re.compile(r"(?:^|\s)/goal(?:\b|\s|$)", re.IGNORECASE)
    approval_pattern = re.compile(r"\b(proceed|approve|approved|yes|lgtm|continue)\b", re.IGNORECASE)

    last_goal_idx = None
    for idx, t in enumerate(user_turns):
        if goal_pattern.search(t):
            last_goal_idx = idx

    if last_goal_idx is not None:
        if last_goal_idx == len(user_turns) - 1:
            return True
        subsequent = user_turns[last_goal_idx + 1 :]
        if all(
            approval_pattern.search(turn) or "the user has approved this document" in turn.lower()
            for turn in subsequent
        ):
            return True
        for turn in reversed(subsequent):
            clean_lower = turn.lower()
            if approval_pattern.search(clean_lower) or "the user has approved this document" in clean_lower:
                return True
        return False

    for turn in reversed(user_turns[-5:]):
        clean_lower = turn.lower()
        if approval_pattern.search(clean_lower) or "the user has approved this document" in clean_lower:
            return True

    return False


def is_unauthorized_status_promotion(
    index_path: Path,
    args: Dict[str, Any],
    checker: Any,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """Detect unauthorized promotion or mid-flight scope expansion in docs/specs/INDEX.md (REQ-031, ADR-022)."""
    existing_approved_map: Dict[str, Dict[str, str]] = {}
    disk_text = ""
    if index_path.exists() and index_path.is_file():
        try:
            disk_text = index_path.read_text(encoding="utf-8")
            existing_records = checker.parse_specs_index(index_path)
            existing_approved_map = {
                r["feature_id"]: r
                for r in existing_records
                if checker.normalize_status(r.get("status", "")) in checker.EXECUTION_STATUSES
            }
        except Exception as exc:
            return True, f"Spec Gate Rejection: Failed to parse existing docs/specs/INDEX.md: {exc}"

    # Project new file content
    projected_text, err = _project_file_text(disk_text, args, file_label="docs/specs/INDEX.md")
    if err or projected_text is None:
        return True, f"Spec Gate Rejection: {err}"

    try:
        projected_records = checker.parse_specs_index_text(projected_text)
    except ValueError as exc:
        return (
            True,
            f"Spec Gate Rejection: Projected edit to docs/specs/INDEX.md produces a malformed table: {exc}",
        )
    except Exception as exc:
        return (
            True,
            f"Spec Gate Rejection: Failed to parse projected docs/specs/INDEX.md: {exc}",
        )

    newly_promoted_or_expanded: List[Tuple[Dict[str, str], str]] = []
    for r in projected_records:
        norm_status = checker.normalize_status(r.get("status", ""))
        if norm_status in checker.EXECUTION_STATUSES:
            feat_id = r.get("feature_id", "")
            if feat_id not in existing_approved_map:
                newly_promoted_or_expanded.append((r, "promotion"))
            else:
                old_r = existing_approved_map[feat_id]
                old_req = old_r.get("req_range", "").strip()
                new_req = r.get("req_range", "").strip()
                old_adr = old_r.get("key_decisions", "").strip()
                new_adr = r.get("key_decisions", "").strip()
                if old_req != new_req or old_adr != new_adr:
                    newly_promoted_or_expanded.append((r, "expansion"))

    if newly_promoted_or_expanded:
        if not (
            os.environ.get("SPEC_GATE_ALLOW_APPROVAL") == "1"
            or (payload is not None and has_recent_user_approval(payload))
        ):
            rec, kind = newly_promoted_or_expanded[0]
            feat_id = rec.get("feature_id", "")
            status = rec.get("status", "")
            if kind == "expansion":
                return (
                    True,
                    f"Spec Gate Rejection: Mid-flight scope expansion of feature '{feat_id}' in docs/specs/INDEX.md is forbidden without explicit user approval ('Proceed').",
                )
            else:
                return (
                    True,
                    f"Spec Gate Rejection: Autonomous self-approval of feature '{feat_id}' to status '{status}' in docs/specs/INDEX.md is forbidden. Register as Draft/Planning and ask the user to approve.",
                )

        for record, kind in newly_promoted_or_expanded:
            pkg_dir, _ = checker.resolve_package_dir(record, index_path.parent.parent, index_path.parent)
            if pkg_dir is not None:
                sem_ok, sem_err = checker.validate_semantic_traceability(pkg_dir, verify_evidence=False)
                if not sem_ok:
                    action_word = "expand scope of" if kind == "expansion" else "promote"
                    return (
                        True,
                        f"Spec Gate Rejection: Cannot {action_word} feature '{record.get('feature_id')}' to '{record.get('status')}' without a valid Opus semantic traceability audit: {sem_err}",
                    )

    return False, ""


def extract_adr_decision_bodies(text: str) -> Dict[str, str]:
    """Extract mapping of ADR-xxx -> normalized Decision body text (REQ-033, ADR-024)."""
    adr_blocks = list(re.finditer(r"^#{1,4}\s+.*?\b(ADR-\d+)\b.*$", text, re.MULTILINE))
    bodies: Dict[str, str] = {}
    for i, m in enumerate(adr_blocks):
        adr_id = m.group(1)
        start = m.start()
        end = adr_blocks[i + 1].start() if i + 1 < len(adr_blocks) else len(text)
        block = text[start:end]
        dec_match = re.search(
            r"(?:^|\n)\s*[-*]\s+\*\*Decision\*\*:(.*?)(?=\n\s*[-*]\s+\*\*|\n#{1,4}\s+|$)",
            block,
            re.DOTALL | re.IGNORECASE,
        )
        if dec_match:
            bodies[adr_id] = " ".join(dec_match.group(1).split()).strip()
    return bodies


def is_destructive_decisions_edit(
    decisions_path: Path,
    index_path: Path,
    args: Dict[str, Any],
    checker: Any,
) -> Tuple[bool, str]:
    """Block deletions of existing ADR IDs or in-place rewriting of decision bodies (REQ-033, ADR-024)."""
    if not decisions_path.exists() or not decisions_path.is_file():
        return False, ""

    try:
        disk_text = decisions_path.read_text(encoding="utf-8")
    except Exception as exc:
        return True, f"Spec Gate Rejection: Failed to read decisions.md from disk: {exc}"

    projected_text, err = _project_file_text(disk_text, args)
    if err or projected_text is None:
        return True, f"Spec Gate Rejection: Failed to project decisions.md content: {err}"

    old_adrs = set(re.findall(r"\bADR-\d+\b", disk_text))
    new_adrs = set(re.findall(r"\bADR-\d+\b", projected_text))
    missing_adrs = sorted(list(old_adrs - new_adrs))
    if missing_adrs:
        return (
            True,
            f"Spec Gate Rejection: decisions.md is append-only (RULE[spec-standard]). Existing ADR IDs cannot be removed: {', '.join(missing_adrs)}",
        )

    # Determine if feature is in execution or terminal status
    is_locked = False
    feat_name = decisions_path.parent.name
    if index_path.exists() and index_path.is_file():
        try:
            records = checker.parse_specs_index(index_path)
            locked_statuses = checker.EXECUTION_STATUSES | checker.VERIFIABLE_TERMINAL_STATUSES
            for r in records:
                if r.get("feature_id") == feat_name:
                    if checker.normalize_status(r.get("status", "")) in locked_statuses:
                        is_locked = True
                    break
        except Exception:
            pass

    if is_locked:
        old_bodies = extract_adr_decision_bodies(disk_text)
        new_bodies = extract_adr_decision_bodies(projected_text)
        for adr_id, old_body in old_bodies.items():
            if adr_id in new_bodies:
                new_body = new_bodies[adr_id]
                if old_body != new_body:
                    return (
                        True,
                        f"Spec Gate Rejection: decisions.md is append-only for active/completed specs. Do not rewrite the Decision body of {adr_id} in-place; mark {adr_id} as 'Superseded' and append a new ADR section.",
                    )

    return False, ""



def is_exempt_subagent(sa: Dict[str, Any]) -> bool:
    """Check if subagent qualifies for exemption from spec gate."""
    type_name = str(sa.get("TypeName") or "").strip().lower()
    role = str(sa.get("Role") or "").strip().lower()
    if type_name == "traceability-auditor" or "traceability" in role:
        return True
    return type_name == "research" or role in EXEMPT_ROLES


def is_mutating_subagent(sa: Dict[str, Any]) -> bool:
    """Check if subagent role or prompt indicates code mutation."""
    type_name = str(sa.get("TypeName") or "").strip().lower()
    role = str(sa.get("Role") or "").strip().lower()
    if type_name == "traceability-auditor" or "traceability" in role:
        return False
    if type_name == "self":
        return True
    prompt = str(sa.get("Prompt") or "").strip().lower()
    for kw in MUTATION_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", role, re.IGNORECASE) or re.search(rf"\b{re.escape(kw)}\b", prompt, re.IGNORECASE):
            return True
    return False


def evaluate_spec_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate spec-gate decision for given PreToolUse payload."""
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")

    if tool_name not in SUBAGENT_TOOLS and tool_name not in FILE_MUTATION_TOOLS:
        return {"decision": "allow"}

    candidate_workspaces = get_candidate_workspaces(payload)
    primary_ws = candidate_workspaces[0]

    checker, err = load_spec_checker()
    if not checker:
        return {
            "decision": "deny",
            "reason": f"Spec Gate Rejection: Failed to load spec_checker verification engine: {err}",
        }

    if tool_name in SUBAGENT_TOOLS:
        args = tool_call.get("args", {})
        subagents = args.get("Subagents")
        if not isinstance(subagents, list):
            if isinstance(args, dict) and (args.get("TypeName") or args.get("Prompt") or args.get("Role")):
                subagents = [args]
            else:
                subagents = []
        if not subagents:
            return {"decision": "allow"}

        for sa in subagents:
            type_name = str(sa.get("TypeName") or "").strip().lower()
            role = str(sa.get("Role") or "").strip().lower()
            if type_name == "traceability-auditor" or "traceability" in role:
                sa_model = str(sa.get("Model") or "").strip().lower()
                # Tier-aware auditor policy (ADR-012): reject Flash tiers below
                # High; Opus-class and Gemini Flash High are approved auditors.
                if "flash" in sa_model and "high" not in sa_model:
                    return {
                        "decision": "deny",
                        "reason": "Spec Gate Rejection: Traceability auditor subagent must use a high-reasoning model (Opus-class or Gemini Flash High); Flash tiers below High are not accepted.",
                    }

        requires_gate = False
        for sa in subagents:
            if is_mutating_subagent(sa):
                requires_gate = True
                break
            if is_exempt_subagent(sa):
                continue
            requires_gate = True
            break

        if not requires_gate:
            return {"decision": "allow"}

        all_prompts = " ".join([str(sa.get("Prompt") or "") for sa in subagents])
        mentioned_workspaces = extract_prompt_workspaces(all_prompts, candidate_workspaces)

        if mentioned_workspaces:
            for ws in mentioned_workspaces:
                res = checker.verify_active_specification(str(ws), require_approved=True)
                if not res.get("valid"):
                    reason_detail = res.get("reason", "No active specification found.")
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Spec Gate Rejection: Cannot dispatch execution subagent or mutate code.\n"
                            f"{reason_detail}\n"
                            f"Scaffold docs/specs/<feature-id>/, register in INDEX.md, and secure explicit approval ('Proceed') before code implementation."
                        ),
                    }
            return {"decision": "allow"}
        else:
            last_res = None
            for ws in candidate_workspaces:
                res = checker.verify_active_specification(str(ws), require_approved=True)
                if res.get("valid"):
                    return {"decision": "allow"}
                last_res = res

            reason_detail = (last_res or {}).get("reason", "No active specification found.")
            return {
                "decision": "deny",
                "reason": (
                    f"Spec Gate Rejection: Cannot dispatch execution subagent or mutate code.\n"
                    f"{reason_detail}\n"
                    f"Scaffold docs/specs/<feature-id>/, register in INDEX.md, and secure explicit approval ('Proceed') before code implementation."
                ),
            }

    elif tool_name in FILE_MUTATION_TOOLS:
        args = tool_call.get("args", {})
        raw_path = (
            args.get("Path")
            or args.get("TargetFile")
            or args.get("target_file")
            or args.get("file_path")
            or args.get("path")
        )
        if not raw_path or not str(raw_path).strip():
            return {
                "decision": "deny",
                "reason": "Spec Gate Rejection: Missing target file path in mutation tool call",
            }

        raw_target = Path(raw_path)
        lexical_target = raw_target if raw_target.is_absolute() else (primary_ws / raw_target)
        try:
            lexical_abs = lexical_target.parent.resolve() / lexical_target.name
        except Exception:
            lexical_abs = Path(os.path.abspath(str(lexical_target)))
        resolved_target = lexical_target.resolve()

        # If lexical target is within workspace but resolves outside, block symlink escape
        for ws in candidate_workspaces:
            if lexical_abs.is_relative_to(ws) and not resolved_target.is_relative_to(ws):
                return {
                    "decision": "deny",
                    "reason": f"Spec Gate Rejection: Symlink target '{raw_path}' resolves outside workspace root ('{resolved_target}')",
                }

        # If outside workspace_root (e.g. runtime brain artifacts), only allow recognized artifact paths
        if is_allowed_runtime_artifact_path(resolved_target):
            return {"decision": "allow"}

        target_ws = resolve_target_workspace(resolved_target, candidate_workspaces)
        if target_ws is None:
            return {
                "decision": "deny",
                "reason": f"Spec Gate Rejection: File mutation target '{resolved_target}' is outside workspace root and not a recognized runtime artifact path",
            }

        # If targeting docs/specs/INDEX.md, check for unauthorized self-approval
        if resolved_target == (target_ws / "docs" / "specs" / "INDEX.md"):
            unauth, reason = is_unauthorized_status_promotion(resolved_target, args, checker, payload)
            if unauth:
                return {"decision": "deny", "reason": reason}

        # Check append-only decisions.md enforcement (REQ-033, ADR-024)
        if resolved_target.name == "decisions.md" and resolved_target.is_relative_to(target_ws / "docs" / "specs"):
            is_destr, reason = is_destructive_decisions_edit(
                resolved_target, target_ws / "docs" / "specs" / "INDEX.md", args, checker
            )
            if is_destr:
                return {"decision": "deny", "reason": reason}

        # If inside docs/specs/, allow unconditionally for specification authoring
        if resolved_target.is_relative_to(target_ws / "docs" / "specs"):
            return {"decision": "allow"}

        result = checker.verify_active_specification(str(target_ws), require_approved=True)
        if not result.get("valid"):
            reason_detail = result.get("reason", "No active specification found.")
            return {
                "decision": "deny",
                "reason": (
                    f"Spec Gate Rejection: Cannot dispatch execution subagent or mutate code.\n"
                    f"{reason_detail}\n"
                    f"Scaffold docs/specs/<feature-id>/, register in INDEX.md, and secure explicit approval ('Proceed') before code implementation."
                ),
            }

        return {"decision": "allow"}

    return {"decision": "allow"}


def main(argv=None, stdin=None, stdout=None):
    if argv is None:
        argv = sys.argv
    if stdin is None:
        stdin = sys.stdin
    if stdout is None:
        stdout = sys.stdout

    def emit(data):
        stdout.write(json.dumps(data) + "\n")

    try:
        raw = stdin.read()
        if not raw or not raw.strip():
            emit({"decision": "deny", "reason": "Spec Gate Rejection: Empty payload on stdin"})
            return

        payload = json.loads(raw)
        decision = evaluate_spec_gate(payload)
        emit(decision)
    except Exception as exc:
        emit({"decision": "deny", "reason": f"Spec Gate Exception: {exc}"})


if __name__ == "__main__":
    main()
