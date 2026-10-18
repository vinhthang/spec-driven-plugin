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

    try:
        tmp_dir = Path(tempfile.gettempdir()).resolve()
        if target_path.is_relative_to(tmp_dir):
            return True
    except (ValueError, RuntimeError):
        pass

    try:
        sys_tmp = Path("/tmp").resolve()
        if target_path.is_relative_to(sys_tmp):
            return True
    except (ValueError, RuntimeError):
        pass

    if target_str.startswith("/tmp") or target_str.startswith("/private/tmp"):
        return True

    return False


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

        workspace_root = payload.get("cwd") or os.environ.get("AGY_ACTIVE_WORKSPACE") or os.getcwd()
        workspace_path = Path(workspace_root).resolve()

        target = Path(raw_path)
        if not target.is_absolute():
            target = workspace_path / target
        resolved_target = target.resolve()

        # If outside workspace_root (e.g. runtime brain artifacts), only allow recognized artifact paths
        if not resolved_target.is_relative_to(workspace_path):
            if is_allowed_runtime_artifact_path(resolved_target):
                return {"decision": "allow"}
            return {
                "decision": "deny",
                "reason": f"Spec Gate Rejection: File mutation target '{resolved_target}' is outside workspace root and not a recognized runtime artifact path",
            }

        # If inside docs/specs/, allow unconditionally for specification authoring
        if resolved_target.is_relative_to(workspace_path / "docs" / "specs"):
            return {"decision": "allow"}

        requires_gate = True
    else:
        return {"decision": "allow"}

    # Evaluate specification status
    workspace_root = payload.get("cwd") or os.environ.get("AGY_ACTIVE_WORKSPACE") or os.getcwd()
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
