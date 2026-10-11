#!/usr/bin/env python3
"""Shared Specification Verification Engine (REQ-032).

Validates that an active feature specification exists in docs/specs/INDEX.md
and complies with the 5-Document Architecture standard.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


ACTIVE_STATUSES = {"draft", "planning", "in-progress", "active", "approved"}
REQ_PATTERN = re.compile(r"\b(REQ-[0-9A-Za-z_-]+|FLOW-\d+|ALIGN-\d+)\b")


def parse_specs_index(index_path: Union[Path, str]) -> List[Dict[str, str]]:
    """Parse markdown table rows in docs/specs/INDEX.md into structured dicts.

    Keys returned: feature_id, title, status, req_range, key_decisions, spec_path.
    """
    path = Path(index_path)
    if not path.exists():
        raise FileNotFoundError(f"Index file not found: {path}")

    content = path.read_text(encoding="utf-8")
    records: List[Dict[str, str]] = []

    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed.startswith("|") or not trimmed.endswith("|"):
            continue

        parts = [p.strip() for p in trimmed[1:-1].split("|")]
        if len(parts) < 6:
            continue

        col0 = parts[0].strip("` ")
        if col0.lower() == "feature id" or re.match(r"^:?-+:?$", col0):
            continue

        feature_id = col0
        title = parts[1].strip()
        status = parts[2].strip("` ")
        req_range = parts[3].strip("` ")
        key_decisions = parts[4].strip()
        raw_spec_path = parts[5].strip()

        # Extract URL or relative path if formatted as [label](path)
        link_match = re.search(r"\[.*?\]\((.*?)\)", raw_spec_path)
        if link_match:
            spec_path = link_match.group(1).strip()
        else:
            spec_path = raw_spec_path.strip("` ")

        records.append({
            "feature_id": feature_id,
            "title": title,
            "status": status,
            "req_range": req_range,
            "key_decisions": key_decisions,
            "spec_path": spec_path,
        })

    return records


def get_active_specifications(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Filter records for active status (case-insensitive in ACTIVE_STATUSES)."""
    return [r for r in records if r.get("status", "").strip().lower() in ACTIVE_STATUSES]


def validate_spec_package(package_dir: Union[Path, str]) -> Tuple[bool, str]:
    """Check that spec.md, decisions.md, and design.md exist and are non-empty.

    Verify that spec.md contains at least one requirement pattern (REQ-xxx, FLOW-xxx, ALIGN-xxx).
    """
    pkg = Path(package_dir)
    if not pkg.exists() or not pkg.is_dir():
        return False, f"Package directory not found: {pkg}"

    required_files = ["spec.md", "decisions.md", "design.md"]
    for req_file in required_files:
        target = pkg / req_file
        if not target.exists() or not target.is_file():
            return False, f"Missing required specification file: {req_file}"
        if target.stat().st_size == 0:
            return False, f"Specification file is empty: {req_file}"

    spec_path = pkg / "spec.md"
    spec_content = spec_path.read_text(encoding="utf-8")
    if not REQ_PATTERN.search(spec_content):
        return False, "spec.md does not contain any requirement pattern (REQ-xxx, FLOW-xxx, ALIGN-xxx)"

    return True, ""


def verify_active_specification(workspace_root: Union[Path, str]) -> Dict[str, Any]:
    """Verify that an active and complete specification package exists in workspace.

    Returns a dict with 'status', 'valid', and additional diagnostic details.
    """
    root = Path(workspace_root).resolve()
    specs_dir = root / "docs" / "specs"

    if not specs_dir.exists() or not specs_dir.is_dir():
        return {
            "status": "no_spec_framework",
            "valid": True,
            "reason": "No docs/specs directory in workspace",
        }

    index_path = specs_dir / "INDEX.md"
    if not index_path.exists() or not index_path.is_file():
        return {
            "status": "invalid",
            "valid": False,
            "reason": "Missing docs/specs/INDEX.md",
        }

    try:
        records = parse_specs_index(index_path)
    except Exception as exc:
        return {
            "status": "corrupt_index",
            "valid": False,
            "reason": f"Failed to parse docs/specs/INDEX.md: {exc}",
        }

    active_specs = get_active_specifications(records)
    if not active_specs:
        return {
            "status": "no_active_spec",
            "valid": False,
            "reason": "No active specification found in docs/specs/INDEX.md",
        }

    for spec in active_specs:
        feat_id = spec.get("feature_id", "")
        spec_path_str = spec.get("spec_path", "")

        candidates: List[Path] = []
        if feat_id:
            candidates.append(specs_dir / feat_id)
        if spec_path_str:
            p1 = (specs_dir / spec_path_str).resolve()
            if p1.is_file():
                candidates.append(p1.parent)
            elif p1.is_dir():
                candidates.append(p1)

            p2 = (root / spec_path_str).resolve()
            if p2.is_file():
                candidates.append(p2.parent)
            elif p2.is_dir():
                candidates.append(p2)

        pkg_dir: Optional[Path] = None
        for cand in candidates:
            if cand.exists() and cand.is_dir():
                pkg_dir = cand
                break

        if not pkg_dir:
            return {
                "status": "incomplete_package",
                "valid": False,
                "feature_id": feat_id,
                "reason": f"Package directory for feature '{feat_id}' not found",
            }

        is_valid, err = validate_spec_package(pkg_dir)
        if not is_valid:
            return {
                "status": "incomplete_package",
                "valid": False,
                "feature_id": feat_id,
                "reason": err,
            }

    active_ids = [s.get("feature_id", "") for s in active_specs]
    return {
        "status": "valid",
        "valid": True,
        "active_features": active_ids,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint for spec verification engine."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Shared Specification Verification Engine (REQ-032)"
    )
    parser.add_argument(
        "--workspace",
        default=os.getcwd(),
        help="Workspace root directory to verify (default: current working directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured verification report as JSON",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress textual diagnostic messages",
    )
    args = parser.parse_args(argv)

    try:
        result = verify_active_specification(Path(args.workspace))
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "valid": False, "reason": str(exc)}))
        elif not args.quiet:
            print(f"Error during specification verification: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result))
    elif not args.quiet:
        if result.get("valid"):
            print(f"Specification verification passed: status={result.get('status')}")
            if "active_features" in result:
                print(f"Active features: {', '.join(result['active_features'])}")
        else:
            print(f"Specification verification failed: {result.get('reason')}", file=sys.stderr)

    if result.get("valid"):
        return 0
    elif result.get("status") in ("corrupt_index", "error"):
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
