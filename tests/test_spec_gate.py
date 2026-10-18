#!/usr/bin/env python3
"""Unit tests for PreToolUse Spec Gate Hook (REQ-002, REQ-004, REQ-005, REQ-008)."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location(
    "spec_gate",
    SCRIPTS_DIR / "spec-gate.py"
)
spec_gate_mod = importlib.util.module_from_spec(spec)
sys.modules["spec_gate"] = spec_gate_mod
spec.loader.exec_module(spec_gate_mod)

evaluate_spec_gate = spec_gate_mod.evaluate_spec_gate
is_exempt_subagent = spec_gate_mod.is_exempt_subagent
is_mutating_subagent = spec_gate_mod.is_mutating_subagent


class TestSpecGate(unittest.TestCase):
    """Test suite for spec-gate.py."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _setup_valid_approved_spec(self):
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "feat-valid"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-valid` | Valid | Approved | `REQ-001` | ADR-001 | `./feat-valid/spec.md` |\n",
            encoding="utf-8",
        )
        (pkg_dir / "spec.md").write_text("# Spec\nREQ-001: Description\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR-001: Rationale\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n", encoding="utf-8")

    def test_exempt_research_subagent(self):
        """Research subagents without mutation keywords are exempt from spec gate."""
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {
                            "TypeName": "research",
                            "Role": "Codebase Researcher",
                            "Prompt": "Search codebase for references to spec gate",
                        }
                    ]
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_word_boundary_codebase_researcher_not_mutating(self):
        """Word boundary keyword matching prevents 'code' in 'codebase researcher' from triggering mutation."""
        sa = {
            "TypeName": "research",
            "Role": "Codebase Researcher",
            "Prompt": "Survey code architecture and patterns",
        }
        self.assertFalse(is_mutating_subagent(sa))
        self.assertTrue(is_exempt_subagent(sa))

    def test_role_spoofing_rejected(self):
        """Subagents with research TypeName but mutating prompts fail closed and require active spec."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-old` | Old | Completed | `REQ-001` | ADR-001 | `./feat-old/spec.md` |\n",
            encoding="utf-8",
        )

        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {
                            "TypeName": "research",
                            "Role": "Codebase Researcher",
                            "Prompt": "Implement feature by patching scripts/helper.py",
                        }
                    ]
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "deny")
        self.assertIn("Spec Gate Rejection", decision.get("reason", ""))

    def test_subagent_denial_no_active_spec(self):
        """Mutating subagents are denied when no active spec exists."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-old` | Old | Completed | `REQ-001` | ADR-001 | `./feat-old/spec.md` |\n",
            encoding="utf-8",
        )

        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {
                            "TypeName": "self",
                            "Role": "Feature Implementer",
                            "Prompt": "Implement feature in scripts/helper.py",
                        }
                    ]
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "deny")
        self.assertIn("No active specification found", decision.get("reason", ""))

    def test_subagent_denial_unapproved_spec(self):
        """Mutating subagents are denied when specification is in planning status."""
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "feat-plan"
        pkg_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-plan` | Plan | Planning | `REQ-001` | ADR-001 | `./feat-plan/spec.md` |\n",
            encoding="utf-8",
        )
        (pkg_dir / "spec.md").write_text("# Spec\nREQ-001: Description\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR-001: Rationale\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n- [ ] Task REQ-001\n", encoding="utf-8")

        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {
                            "TypeName": "self",
                            "Role": "Executor",
                            "Prompt": "Execute implementation",
                        }
                    ]
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "deny")
        self.assertIn("planning/draft status but is not yet approved", decision.get("reason", ""))

    def test_subagent_allowance_with_approved_spec(self):
        """Mutating subagents are allowed when a valid approved specification exists."""
        self._setup_valid_approved_spec()

        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {
                            "TypeName": "self",
                            "Role": "Feature Implementer",
                            "Prompt": "Implement feature per task instructions",
                        }
                    ]
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_direct_mutation_tools_gating(self):
        """Direct file-mutation tools are gated when modifying workspace code without approved spec."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )

        for tool_name in [
            "write_to_file",
            "replace_file_content",
            "multi_replace_file_content",
            "default_api:write_to_file",
            "client:replace_file_content",
        ]:
            payload = {
                "cwd": str(self.workspace),
                "toolCall": {
                    "name": tool_name,
                    "args": {"TargetFile": str(self.workspace / "src" / "app.py")},
                },
            }
            decision = evaluate_spec_gate(payload)
            self.assertEqual(decision.get("decision"), "deny", f"Tool {tool_name} should be denied")

        # Now approve spec -> should allow
        self._setup_valid_approved_spec()
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(self.workspace / "src" / "app.py")},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_direct_mutation_missing_target_file_fails_closed(self):
        """Direct file-mutation tools fail closed when target file path argument is missing."""
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "write_to_file",
                "args": {"CodeContent": "print('hello')"},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "deny")
        self.assertIn("Missing target file path", decision.get("reason", ""))

    def test_direct_mutation_external_brain_artifact_exemption(self):
        """Writing to files outside workspace (e.g. brain runtime artifacts) is allowed unconditionally."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )

        external_path = Path("/Users/thanghoang/.gemini/antigravity/brain/session/artifact.md")
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(external_path)},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_direct_mutation_docs_specs_authoring_exemption(self):
        """Writing to docs/specs/ is allowed unconditionally for specification authoring."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )

        spec_file = self.workspace / "docs" / "specs" / "feat-1" / "spec.md"
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": str(spec_file)},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_non_gated_tool_allowed(self):
        """Tools not in subagent or mutation sets are allowed unconditionally."""
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_cli_execution_via_stdin(self):
        """Test executing spec-gate.py CLI via stdin with valid and invalid payloads."""
        script_path = SCRIPTS_DIR / "spec-gate.py"

        # Allowed request (non-gated tool via stdin)
        payload_allow = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"},
            },
        }
        proc_allow = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(payload_allow),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_allow.returncode, 0)
        self.assertEqual(json.loads(proc_allow.stdout).get("decision"), "allow")

        # Denied request (subagent mutation without active spec)
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "INDEX.md").write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-old` | Old | Completed | `REQ-001` | ADR-001 | `./feat-old/spec.md` |\n",
            encoding="utf-8",
        )
        payload_deny = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {"TypeName": "self", "Role": "Implementer", "Prompt": "Write code"}
                    ]
                },
            },
        }
        proc_deny = subprocess.run(
            [sys.executable, str(script_path)],
            input=json.dumps(payload_deny),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_deny.returncode, 0)
        data_deny = json.loads(proc_deny.stdout)
        self.assertEqual(data_deny.get("decision"), "deny")
        self.assertIn("Spec Gate Rejection", data_deny.get("reason", ""))

    def test_empty_stdin_fails_closed(self):
        """Test that empty or whitespace-only stdin emits deny decision."""
        script_path = SCRIPTS_DIR / "spec-gate.py"

        for empty_input in ["", "   ", "\n\t  \n"]:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                input=empty_input,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data.get("decision"), "deny")
            self.assertEqual(data.get("reason"), "Spec Gate Rejection: Empty payload on stdin")

    def test_unauthorized_external_path_fails_closed(self):
        """Writing to an external path outside workspace and not a recognized runtime artifact path fails closed."""
        self._setup_valid_approved_spec()

        unauthorized_paths = [
            "/etc/hosts",
            "/Users/thanghoang/github/other-project/src/main.py",
            "/var/log/system.log",
        ]

        for path in unauthorized_paths:
            payload = {
                "cwd": str(self.workspace),
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": path},
                },
            }
            decision = evaluate_spec_gate(payload)
            self.assertEqual(decision.get("decision"), "deny", f"Expected deny for {path}")
            self.assertIn("is outside workspace root and not a recognized runtime artifact path", decision.get("reason", ""))

    def test_checker_load_failure_fails_closed(self):
        """When load_spec_checker returns (None, err), evaluate_spec_gate fails closed with deny."""
        self._setup_valid_approved_spec()

        import unittest.mock as mock
        with mock.patch.object(spec_gate_mod, "load_spec_checker", return_value=(None, "Mock import failure")):
            payload = {
                "cwd": str(self.workspace),
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": str(self.workspace / "src" / "app.py")},
                },
            }
            decision = evaluate_spec_gate(payload)
            self.assertEqual(decision.get("decision"), "deny")
            self.assertIn("Failed to load spec_checker verification engine: Mock import failure", decision.get("reason", ""))


    def test_self_approval_in_index_md_denied(self):
        """Self-approval writes to docs/specs/INDEX.md are blocked unless already approved or SPEC_GATE_ALLOW_APPROVAL=1."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n"
            "| `feat-approved` | Feature Approved | Approved | `REQ-002` | ADR-002 | `./feat-approved/spec.md` |\n",
            encoding="utf-8",
        )

        # 1. Attempt to promote feat-1 to Approved via replace_file_content -> DENIED
        payload_promote = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": str(index_file),
                    "TargetContent": "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |",
                    "ReplacementContent": "| `feat-1` | Feature 1 | Approved | `REQ-001` | ADR-001 | `./feat-1/spec.md` |",
                },
            },
        }
        dec_promote = evaluate_spec_gate(payload_promote)
        self.assertEqual(dec_promote.get("decision"), "deny")
        self.assertIn("Autonomous self-approval of feature 'feat-1'", dec_promote.get("reason", ""))

        # 2. Attempt to add new feature with Approved via write_to_file -> DENIED
        new_content = (
            "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "| `feat-new` | New Feature | Approved | `REQ-003` | ADR-003 | `./feat-new/spec.md` |\n"
        )
        payload_new_approved = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": str(index_file),
                    "CodeContent": new_content,
                },
            },
        }
        dec_new = evaluate_spec_gate(payload_new_approved)
        self.assertEqual(dec_new.get("decision"), "deny")
        self.assertIn("Autonomous self-approval of feature 'feat-new'", dec_new.get("reason", ""))

        # 3. Edit already-approved feature (feat-approved) title -> ALLOWED
        payload_edit_approved = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": str(index_file),
                    "TargetContent": "| `feat-approved` | Feature Approved | Approved | `REQ-002` | ADR-002 | `./feat-approved/spec.md` |",
                    "ReplacementContent": "| `feat-approved` | Updated Approved Title | Approved | `REQ-002` | ADR-002 | `./feat-approved/spec.md` |",
                },
            },
        }
        dec_edit_approved = evaluate_spec_gate(payload_edit_approved)
        self.assertEqual(dec_edit_approved.get("decision"), "allow")

        # 4. Add/edit feature with Planning or Draft status -> ALLOWED
        payload_planning = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": str(index_file),
                    "TargetContent": "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |",
                    "ReplacementContent": "| `feat-1` | Feature 1 | Draft | `REQ-001` | ADR-001 | `./feat-1/spec.md` |",
                },
            },
        }
        dec_planning = evaluate_spec_gate(payload_planning)
        self.assertEqual(dec_planning.get("decision"), "allow")

        # 5. With SPEC_GATE_ALLOW_APPROVAL=1 env var set -> ALLOWED
        import unittest.mock as mock
        with mock.patch.dict(os.environ, {"SPEC_GATE_ALLOW_APPROVAL": "1"}):
            dec_override = evaluate_spec_gate(payload_promote)
            self.assertEqual(dec_override.get("decision"), "allow")

    def test_workspace_symlink_escape_denied(self):
        """In-workspace symlinks that resolve outside workspace_root are denied."""
        self._setup_valid_approved_spec()

        # Create an external directory outside workspace
        ext_dir = Path(tempfile.mkdtemp())
        try:
            ext_target = ext_dir / "target.py"
            ext_target.write_text("# external file\n", encoding="utf-8")

            # Create an in-workspace symlink pointing to ext_target
            link_path = self.workspace / "src" / "symlink_escape.py"
            link_path.parent.mkdir(parents=True, exist_ok=True)
            link_path.symlink_to(ext_target)

            payload = {
                "cwd": str(self.workspace),
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": str(link_path)},
                },
            }
            decision = evaluate_spec_gate(payload)
            self.assertEqual(decision.get("decision"), "deny")
            self.assertIn("resolves outside workspace root", decision.get("reason", ""))
        finally:
            shutil.rmtree(ext_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
