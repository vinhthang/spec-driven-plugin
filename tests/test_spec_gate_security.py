#!/usr/bin/env python3
"""Security, spoofing, multi-workspace, and approval tests for spec-gate.py (REQ-010, REQ-011, REQ-014, REQ-015)."""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("spec_gate", SCRIPTS_DIR / "spec-gate.py")
spec_gate_mod = importlib.util.module_from_spec(spec)
sys.modules["spec_gate"] = spec_gate_mod
spec.loader.exec_module(spec_gate_mod)

evaluate_spec_gate = spec_gate_mod.evaluate_spec_gate
get_candidate_workspaces = spec_gate_mod.get_candidate_workspaces
resolve_target_workspace = spec_gate_mod.resolve_target_workspace
has_recent_user_approval = spec_gate_mod.has_recent_user_approval
is_allowed_runtime_artifact_path = spec_gate_mod.is_allowed_runtime_artifact_path
is_unauthorized_status_promotion = spec_gate_mod.is_unauthorized_status_promotion

INDEX_HEADER = (
    "| Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path |\n"
    "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
)


class TestSpecGateSecurity(unittest.TestCase):
    """Security, edge-case, and multi-workspace tests for spec-gate.py."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _setup_valid_approved_spec(self, feature_id="feat-approved"):
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / feature_id
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "spec.md").write_text("# Spec\n- REQ-001: Requirement 1\n", encoding="utf-8")
        (pkg_dir / "decisions.md").write_text("# Decisions\nADR-001: Key decision\n", encoding="utf-8")
        (pkg_dir / "design.md").write_text("# Design\nAddresses REQ-001\n", encoding="utf-8")
        (pkg_dir / "tasks.md").write_text("# Tasks\n- [ ] Task for REQ-001\n", encoding="utf-8")
        (specs_dir / "INDEX.md").write_text(
            INDEX_HEADER + f"| `{feature_id}` | Title | Approved | `REQ-001` | ADR-001 | `./{feature_id}/spec.md` |\n",
            encoding="utf-8",
        )

    def test_self_approval_in_index_md_denied(self):
        """Self-approval writes to docs/specs/INDEX.md are blocked unless already approved or SPEC_GATE_ALLOW_APPROVAL=1."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n"
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
            INDEX_HEADER + "| `feat-new` | New Feature | Approved | `REQ-003` | ADR-003 | `./feat-new/spec.md` |\n"
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

    def test_is_allowed_runtime_artifact_path_spoofing(self):
        """is_allowed_runtime_artifact_path rejects spoofed substring paths and allows valid runtime paths."""
        # Valid brain path
        valid_brain = Path("/Users/thanghoang/.gemini/antigravity/brain/conv-123/plan.md")
        self.assertTrue(is_allowed_runtime_artifact_path(valid_brain))

        # Valid scratch path
        valid_scratch = Path("/Users/thanghoang/.gemini/antigravity/scratch/test.py")
        self.assertTrue(is_allowed_runtime_artifact_path(valid_scratch))

        # Spoofed path where .gemini is not an exact path component
        spoofed_user = Path("/Users/evil/fake.gemini/antigravity/brain_spoof/file.py")
        self.assertFalse(is_allowed_runtime_artifact_path(spoofed_user))

        spoofed_tmp = Path("/tmp/not.gemini/antigravity/brain/file.py")
        self.assertFalse(is_allowed_runtime_artifact_path(spoofed_tmp))

        spoofed_suffix = Path("/tmp/.gemini/antigravity/brain_spoof/file.py")
        self.assertFalse(is_allowed_runtime_artifact_path(spoofed_suffix))

        # Custom artifact dir support
        custom_dir = Path(self.test_dir) / "custom_artifacts"
        custom_dir.mkdir(parents=True, exist_ok=True)
        custom_file = custom_dir / "artifact.md"
        import unittest.mock as mock
        with mock.patch.dict(os.environ, {"AGY_RUNTIME_ARTIFACT_DIR": str(custom_dir)}):
            self.assertTrue(is_allowed_runtime_artifact_path(custom_file))

    def test_is_unauthorized_status_promotion_unmatched_target_content(self):
        """is_unauthorized_status_promotion fails closed when TargetContent is empty or not found on disk."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )
        checker, _ = spec_gate_mod.load_spec_checker()

        # 1. Empty TargetContent
        unauth, reason = is_unauthorized_status_promotion(index_file, {"TargetContent": "", "ReplacementContent": "| Approved |"}, checker)
        self.assertTrue(unauth)
        self.assertIn("TargetContent for docs/specs/INDEX.md replacement was empty or not found on disk", reason)

        # 2. TargetContent not on disk
        unauth2, reason2 = is_unauthorized_status_promotion(index_file, {"TargetContent": "NonExistentString", "ReplacementContent": "SomethingElse"}, checker)
        self.assertTrue(unauth2)
        self.assertIn("TargetContent for docs/specs/INDEX.md replacement was empty or not found on disk", reason2)

        # 3. ReplacementChunks with empty or missing TargetContent
        unauth3, reason3 = is_unauthorized_status_promotion(
            index_file,
            {"ReplacementChunks": [{"TargetContent": "NonExistent", "ReplacementContent": "New"}]},
            checker,
        )
        self.assertTrue(unauth3)
        self.assertIn("ReplacementChunk TargetContent was empty or not found", reason3)

    def test_is_unauthorized_status_promotion_malformed_table(self):
        """is_unauthorized_status_promotion fails closed when projected INDEX.md produces a malformed table."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        valid_row = "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |"
        index_file.write_text(
            INDEX_HEADER + f"{valid_row}\n",
            encoding="utf-8",
        )
        checker, _ = spec_gate_mod.load_spec_checker()

        # Replace with a row having only 5 columns (missing 1 column)
        malformed_row = "| `feat-1` | Feature 1 | Planning | `REQ-001` | `./feat-1/spec.md` |"
        unauth, reason = is_unauthorized_status_promotion(
            index_file,
            {"TargetContent": valid_row, "ReplacementContent": malformed_row},
            checker,
        )
        self.assertTrue(unauth)
        self.assertIn("produces a malformed table", reason)

    def test_partial_cell_replacement_promotion_denied(self):
        """Partial cell replacement changing Planning to Approved is detected and denied."""
        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )
        payload = {
            "cwd": str(self.workspace),
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": str(index_file),
                    "TargetContent": "| Planning |",
                    "ReplacementContent": "| Approved |",
                },
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "deny")
        self.assertIn("Autonomous self-approval of feature 'feat-1'", decision.get("reason", ""))




    def test_hooks_json_schema_validation(self):
        """hooks.json conforms to Antigravity inner hooks schema (REQ-014)."""
        hooks_path = Path(__file__).resolve().parent.parent / "hooks.json"
        self.assertTrue(hooks_path.is_file(), "hooks.json must exist in repo root")
        with open(hooks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("spec-gate-plugin", data)
        pre_tool = data["spec-gate-plugin"].get("PreToolUse", [])
        self.assertTrue(len(pre_tool) > 0)
        matcher_item = pre_tool[0]
        self.assertIn("matcher", matcher_item)
        self.assertIn("hooks", matcher_item)
        hook_cmd = matcher_item["hooks"][0]
        self.assertEqual(hook_cmd.get("type"), "command")
        self.assertEqual(hook_cmd.get("timeout"), 5)
        self.assertIn("./scripts/spec-gate.py", hook_cmd.get("command", ""))

    def test_workspace_paths_resolution_when_cwd_absent(self):
        """get_candidate_workspaces resolves workspacePaths when cwd is absent or plugin dir (REQ-014)."""
        ws1 = self.workspace / "ws1"
        ws1.mkdir()
        candidates = get_candidate_workspaces({"workspacePaths": [str(ws1)]})
        self.assertIn(ws1.resolve(), candidates)

        self._setup_valid_approved_spec()
        plugin_dir = self.workspace / "fake-plugin"
        plugin_dir.mkdir()
        payload = {
            "cwd": str(plugin_dir),
            "workspacePaths": [str(self.workspace)],
            "toolCall": {
                "name": "invoke_subagent",
                "args": {"Subagents": [{"TypeName": "self", "Role": "Implementer", "Prompt": "Write code"}]},
            },
        }
        decision = evaluate_spec_gate(payload)
        self.assertEqual(decision.get("decision"), "allow")

    def test_secondary_workspace_resolution(self):
        """resolve_target_workspace discovers secondary workspace via .git or docs/specs ancestor (REQ-014)."""
        sec_ws = self.workspace / "secondary_repo"
        (sec_ws / "docs" / "specs").mkdir(parents=True)
        target_file = sec_ws / "src" / "pkg" / "module.py"
        target_file.parent.mkdir(parents=True)
        target_file.touch()

        primary_ws = self.workspace / "primary_repo"
        primary_ws.mkdir()
        resolved_ws = resolve_target_workspace(target_file.resolve(), [primary_ws.resolve()])
        self.assertEqual(resolved_ws, sec_ws.resolve())

        git_ws = self.workspace / "git_repo"
        (git_ws / ".git").mkdir(parents=True)
        git_target = git_ws / "lib" / "code.py"
        git_target.parent.mkdir(parents=True)
        git_target.touch()
        self.assertEqual(resolve_target_workspace(git_target.resolve(), [primary_ws.resolve()]), git_ws.resolve())

    def test_has_recent_user_approval_and_promotion(self):
        """has_recent_user_approval detects user approval in transcript and permits INDEX.md promotion (REQ-014)."""
        transcript_file = self.workspace / "transcript.jsonl"
        transcript_file.write_text(
            json.dumps({"source": "USER", "type": "USER_INPUT", "content": "Please proceed with implementation."}) + "\n",
            encoding="utf-8",
        )
        self.assertTrue(has_recent_user_approval({"transcriptPath": str(transcript_file)}))

        specs_dir = self.workspace / "docs" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        index_file = specs_dir / "INDEX.md"
        index_file.write_text(
            INDEX_HEADER + "| `feat-1` | Feature 1 | Planning | `REQ-001` | ADR-001 | `./feat-1/spec.md` |\n",
            encoding="utf-8",
        )
        tool_call_promote = {
            "name": "replace_file_content",
            "args": {
                "TargetFile": str(index_file),
                "TargetContent": "| Planning |",
                "ReplacementContent": "| Approved |",
            },
        }
        payload_promote = {
            "cwd": str(self.workspace),
            "transcriptPath": str(transcript_file),
            "toolCall": tool_call_promote,
        }
        dec_allow = evaluate_spec_gate(payload_promote)
        self.assertEqual(dec_allow.get("decision"), "allow")

        transcript_file.write_text(
            json.dumps({"source": "USER", "type": "USER_INPUT", "content": "Can you explain how this works?"}) + "\n",
            encoding="utf-8",
        )
        self.assertFalse(has_recent_user_approval(payload_promote))
        dec_deny = evaluate_spec_gate(payload_promote)
        self.assertEqual(dec_deny.get("decision"), "deny")
        self.assertIn("Autonomous self-approval", dec_deny.get("reason", ""))

        transcript_file.write_text(
            json.dumps({"source": "USER", "type": "USER_INPUT", "content": "/plan proceed with design"}) + "\n",
            encoding="utf-8",
        )
        self.assertFalse(has_recent_user_approval(payload_promote))

    def test_unauthorized_external_path_fails_closed(self):
        """Writing to an external path outside workspace and not a recognized runtime artifact path fails closed."""
        self._setup_valid_approved_spec()
        for path in ["/etc/hosts", "/Users/thanghoang/github/other-project/src/main.py", "/var/log/system.log"]:
            payload = {"cwd": str(self.workspace), "toolCall": {"name": "write_to_file", "args": {"TargetFile": path}}}
            decision = evaluate_spec_gate(payload)
            self.assertEqual(decision.get("decision"), "deny")
            self.assertIn("is outside workspace root and not a recognized runtime artifact path", decision.get("reason", ""))

    def test_traceability_auditor_model_enforcement(self):
        """Traceability auditor subagent is denied with sub-High Flash tiers but allowed with pro/inherit and Flash High (ADR-012)."""
        self._setup_valid_approved_spec()
        call_args = lambda m: {"Subagents": [{"TypeName": "traceability-auditor", "Model": m, "Role": "Auditor", "Prompt": "Audit"}]}
        res_flash = evaluate_spec_gate({"cwd": str(self.workspace), "toolCall": {"name": "invoke_subagent", "args": call_args("flash")}})
        self.assertEqual(res_flash.get("decision"), "deny")
        self.assertIn("must use a high-reasoning model", res_flash.get("reason", ""))

        res_medium = evaluate_spec_gate({"cwd": str(self.workspace), "toolCall": {"name": "invoke_subagent", "args": call_args("gemini-3.8-flash-medium")}})
        self.assertEqual(res_medium.get("decision"), "deny")

        res_pro = evaluate_spec_gate({"cwd": str(self.workspace), "toolCall": {"name": "invoke_subagent", "args": call_args("pro")}})
        self.assertEqual(res_pro.get("decision"), "allow")

        res_flash_high = evaluate_spec_gate({"cwd": str(self.workspace), "toolCall": {"name": "invoke_subagent", "args": call_args("gemini-3.8-flash-high")}})
        self.assertEqual(res_flash_high.get("decision"), "allow")

    def test_index_promotion_requires_semantic_traceability_receipt(self):
        """Promoting to Approved when pkg_dir exists requires valid Opus traceability_audit.json receipt."""
        specs_dir = self.workspace / "docs" / "specs"
        pkg_dir = specs_dir / "feat-sem"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        for fname, txt in [("spec.md", "# Spec\n- REQ-001: R\n"), ("decisions.md", "ADR-001: D\n"), ("design.md", "REQ-001\n"), ("tasks.md", "- [ ] REQ-001\n")]:
            (pkg_dir / fname).write_text(txt, encoding="utf-8")

        index_file = specs_dir / "INDEX.md"
        index_file.write_text(INDEX_HEADER + "| `feat-sem` | Feat | Planning | `REQ-001` | ADR-001 | `./feat-sem/spec.md` |\n", encoding="utf-8")
        transcript_file = self.workspace / "transcript.jsonl"
        transcript_file.write_text(json.dumps({"source": "USER", "type": "USER_INPUT", "content": "proceed"}) + "\n", encoding="utf-8")

        payload = {
            "cwd": str(self.workspace), "transcriptPath": str(transcript_file),
            "toolCall": {"name": "replace_file_content", "args": {"TargetFile": str(index_file), "TargetContent": "| Planning |", "ReplacementContent": "| Approved |"}},
        }

        res_missing = evaluate_spec_gate(payload)
        self.assertEqual(res_missing.get("decision"), "deny")
        self.assertIn("without a valid Opus semantic traceability audit", res_missing.get("reason", ""))

        spec_checker = spec_gate_mod.load_spec_checker()[0]
        spec_hash = spec_checker.compute_spec_package_hash(pkg_dir, include_verification=False)
        audit_data = {
            "spec_hash": spec_hash, "auditor_model": "claude-opus-4-6", "verdict": "PASS",
            "requirements_evaluated": {"REQ-001": {"design_aligned": True, "design_rationale": "ok", "tasks_actionable": True, "tasks_rationale": "ok", "decisions_consistent": True}}
        }
        (pkg_dir / "traceability_audit.json").write_text(json.dumps(audit_data), encoding="utf-8")
        self.assertEqual(evaluate_spec_gate(payload).get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()

