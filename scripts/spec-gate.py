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
from typing import Any, Dict, Optional, Tuple

SUBAGENT_TOOLS = {
    "invoke_subagent",
    "default_api:invoke_subagent",
    "client:invoke_subagent",
}

FILE_MUTATION_TOOLS = {
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "client:write_to_file",
    "client:replace_file_content",
    "client:multi_replace_file_content",
    "default_api:write_to_file",
    "default_api:replace_file_content",
    "default_api:multi_replace_file_content",
}

MUTATION_KEYWORDS = {
    "implement",
    "modify",
    "compiler",
    "executor",
    "builder",
    "patch",
    "write_to_file",
    "replace_file_content",
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
    """Check if path matches known runtime artifact paths outside workspace."""
    target_str = str(target_path)
    if ".gemini/antigravity/brain" in target_str or ".gemini/antigravity/scratch" in target_str:
        return True

    custom_artifact_dir = os.environ.get("AGY_RUNTIME_ARTIFACT_DIR")
    if custom_artifact_dir and custom_artifact_dir.strip():
        try:
            custom_path = Path(custom_artifact_dir).resolve()
            if target_path.resolve().is_relative_to(custom_path):
                return True
        except (ValueError, RuntimeError):
            pass

    return False


def is_unauthorized_status_promotion(
    index_path: Path, args: Dict[str, Any], checker: Any
) -> Tuple[bool, str]:
    """Detect unauthorized promotion of features to execution-authorized statuses in docs/specs/INDEX.md."""
    if os.environ.get("SPEC_GATE_ALLOW_APPROVAL") == "1":
        return False, ""

    existing_approved = set()
    disk_text = ""
    if index_path.exists() and index_path.is_file():
        try:
            disk_text = index_path.read_text(encoding="utf-8")
            existing_records = checker.parse_specs_index(index_path)
            existing_approved = {
                r["feature_id"]
                for r in existing_records
                if checker.normalize_status(r.get("status", "")) in checker.EXECUTION_STATUSES
            }
        except Exception:
            pass

    # Project new file content
    if "TargetContent" in args and "ReplacementContent" in args:
        target_c = args.get("TargetContent", "")
        repl_c = args.get("ReplacementContent", "")
        projected_text = disk_text.replace(target_c, repl_c, 1)
    elif "ReplacementChunks" in args and isinstance(args.get("ReplacementChunks"), list):
        projected_text = disk_text
        for chunk in args.get("ReplacementChunks", []):
            target_c = chunk.get("TargetContent", "")
            repl_c = chunk.get("ReplacementContent", "")
            if target_c:
                projected_text = projected_text.replace(target_c, repl_c, 1)
    elif args.get("Append"):
        projected_text = disk_text + "\n" + (args.get("CodeContent") or args.get("Content") or "")
    else:
        projected_text = args.get("CodeContent") or args.get("Content") or args.get("ReplacementContent") or ""

    texts_to_scan = [projected_text]
    if "ReplacementContent" in args and args["ReplacementContent"] not in texts_to_scan:
        texts_to_scan.append(args["ReplacementContent"])

    for text in texts_to_scan:
        for line in text.splitlines():
            trimmed = line.strip()
            if not trimmed.startswith("|") or not trimmed.endswith("|"):
                continue
            raw_parts = re.split(r"(?<!\\)\|", trimmed[1:-1])
            parts = [p.replace(r"\|", "|").strip() for p in raw_parts]
            col0 = parts[0].strip("` ") if parts else ""
            if col0.lower() == "feature id" or re.match(r"^:?-+:?$", col0):
                continue
            if len(parts) >= 3:
                feat_id = col0
                status = parts[2].strip("` ")
                if checker.normalize_status(status) in checker.EXECUTION_STATUSES:
                    if feat_id not in existing_approved:
                        return (
                            True,
                            f"Spec Gate Rejection: Autonomous self-approval of feature '{feat_id}' to status '{status}' in docs/specs/INDEX.md is forbidden. Register as Draft/Planning and ask the user to approve.",
                        )

    return False, ""


def is_exempt_subagent(sa: Dict[str, Any]) -> bool:
    """Check if subagent qualifies for exemption from spec gate."""
    type_name = str(sa.get("TypeName") or "").strip().lower()
    role = str(sa.get("Role") or "").strip().lower()

    if type_name == "research" or role in EXEMPT_ROLES:
        return True

    return False


def is_mutating_subagent(sa: Dict[str, Any]) -> bool:
    """Check if subagent role or prompt indicates code mutation."""
    type_name = str(sa.get("TypeName") or "").strip().lower()
    role = str(sa.get("Role") or "").strip().lower()
    prompt = str(sa.get("Prompt") or "").strip().lower()

    if type_name == "self":
        return True

    for kw in MUTATION_KEYWORDS:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, role, re.IGNORECASE) or re.search(pattern, prompt, re.IGNORECASE):
            return True

    return False


def evaluate_spec_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate spec-gate decision for given PreToolUse payload."""
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")

    requires_gate = False

    if tool_name in SUBAGENT_TOOLS:
        args = tool_call.get("args", {})
        subagents = args.get("Subagents", [])
        if not subagents or not isinstance(subagents, list):
            return {"decision": "allow"}

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

    elif tool_name in FILE_MUTATION_TOOLS:
        args = tool_call.get("args", {})
        raw_path = (
            args.get("TargetFile")
            or args.get("target_file")
            or args.get("file_path")
            or args.get("path")
        )
        if not raw_path or not str(raw_path).strip():
            return {
                "decision": "deny",
                "reason": "Spec Gate Rejection: Missing target file path in mutation tool call",
            }

        workspace_root = os.environ.get("AGY_ACTIVE_WORKSPACE") or payload.get("cwd") or os.getcwd()
        workspace_path = Path(workspace_root).resolve()

        raw_target = Path(raw_path)
        lexical_target = raw_target if raw_target.is_absolute() else (workspace_path / raw_target)
        try:
            lexical_abs = lexical_target.parent.resolve() / lexical_target.name
        except Exception:
            lexical_abs = Path(os.path.abspath(str(lexical_target)))
        resolved_target = lexical_target.resolve()

        # If lexical target is within workspace but resolves outside, block symlink escape
        if lexical_abs.is_relative_to(workspace_path) and not resolved_target.is_relative_to(workspace_path):
            return {
                "decision": "deny",
                "reason": f"Spec Gate Rejection: Symlink target '{raw_path}' resolves outside workspace root ('{resolved_target}')",
            }

        # If outside workspace_root (e.g. runtime brain artifacts), only allow recognized artifact paths
        if not resolved_target.is_relative_to(workspace_path):
            if is_allowed_runtime_artifact_path(resolved_target):
                return {"decision": "allow"}
            return {
                "decision": "deny",
                "reason": f"Spec Gate Rejection: File mutation target '{resolved_target}' is outside workspace root and not a recognized runtime artifact path",
            }

        # If targeting docs/specs/INDEX.md, check for unauthorized self-approval
        if resolved_target == (workspace_path / "docs" / "specs" / "INDEX.md"):
            checker, err = load_spec_checker()
            if checker:
                unauth, reason = is_unauthorized_status_promotion(resolved_target, args, checker)
                if unauth:
                    return {"decision": "deny", "reason": reason}

        # If inside docs/specs/, allow unconditionally for specification authoring
        if resolved_target.is_relative_to(workspace_path / "docs" / "specs"):
            return {"decision": "allow"}

        requires_gate = True
    else:
        return {"decision": "allow"}

    # Evaluate specification status
    workspace_root = os.environ.get("AGY_ACTIVE_WORKSPACE") or payload.get("cwd") or os.getcwd()
    checker, err = load_spec_checker()
    if not checker:
        return {
            "decision": "deny",
            "reason": f"Spec Gate Rejection: Failed to load spec_checker verification engine: {err}",
        }

    result = checker.verify_active_specification(workspace_root, require_approved=True)

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
