#!/usr/bin/env python3
"""Zero-dependency validator for five-document docs/specs packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote

VALID_STATUSES = {"Planning", "In-Progress", "In-Testing", "Verified", "Superseded", "Abandoned"}
DERIVED_DOCS = ("design.md", "tasks.md", "verification.md")

DECLARED_REQ_RE = re.compile(r"^#{2,6}\s+(REQ-\d+)\b", re.MULTILINE)
DECLARED_ADR_RE = re.compile(r"^#{2,6}\s+(ADR-\d+)\b", re.MULTILINE)
PROVISIONAL_REQ_RE = re.compile(r"^#{2,6}\s+(REQ-\d+)\b[^\n]*\[PROVISIONAL\]", re.MULTILINE)
PROVISIONAL_AC_RE = re.compile(r"^[-*]\s+(AC-\d+-\d+)\b[^\n]*\[PROVISIONAL\]", re.MULTILINE)
AC_DECL_RE = re.compile(r"^[-*]\s+(AC-\d+-\d+)\b", re.MULTILINE)
VERIF_AC_HEADING_RE = re.compile(r"^#{2,6}\s+(AC-\d+-\d+)\b", re.MULTILINE)
REQ_TOKEN_RE = re.compile(r"\bREQ-\d+\b")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(((?:[^()\s]|\([^()\s]*\))+)(?:\s+\"[^\"]*\")?\)")
PLACEHOLDER_RE = re.compile(r"<(?!https?://|mailto:)([^\s<>\n](?:[^<>\n]*[^\s<>\n])?)>")
TODO_RE = re.compile(r"\b(TODO|TBD|FIXME)\b")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_TAG_RE = re.compile(r"^/?([a-zA-Z][a-zA-Z0-9]*)(?:\s+[^<>]*)?/?$")
SAFE_HTML_TAGS = {
    "div", "span", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td",
    "img", "blockquote", "pre", "dl", "dt", "dd", "section", "sup", "sub",
    "br", "hr", "details", "summary", "kbd", "em", "strong", "code", "a", "p",
}


def _read_utf8(path: Path, label: str, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{label}: unreadable UTF-8 file ({exc})")
        return None


def strip_fenced_code_blocks(text: str) -> str:
    """Return text with CommonMark fenced code block contents removed."""
    out: list[str] = []
    fence_char = ""
    fence_len = 0
    for line in text.splitlines():
        if not fence_char:
            m = FENCE_OPEN_RE.match(line)
            if m:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                out.append("")
                continue
            out.append(line)
        else:
            if re.match(rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_len},}}\s*$", line):
                fence_char = ""
                fence_len = 0
            out.append("")
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def strip_inline_code(text: str, replacement: str = "") -> str:
    """Replace CommonMark inline backtick spans with replacement."""
    return re.sub(r"(`+)(?!`)(.*?)(?<!`)\1(?!`)", replacement, text)


def heading_slug(title: str) -> str:
    """Compute GitHub-Flavored Markdown heading slug."""
    cleaned = re.sub(r"<[^>]+>", "", title)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
    cleaned = cleaned.replace("`", "").replace("\t", " ").strip().lower()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    return cleaned.replace(" ", "-")


def extract_heading_slugs(text: str) -> set[str]:
    """Return deduplicated GFM heading slugs for a markdown file."""
    seen: set[str] = set()
    for line in strip_fenced_code_blocks(text).splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = heading_slug(m.group(1))
        slug = base
        idx = 1
        while slug in seen:
            slug = f"{base}-{idx}"
            idx += 1
        seen.add(slug)
    return seen


def _extract_section(text: str, heading_prefix: str) -> str:
    """Return body under `## <heading_prefix>...` up to the next `## ` heading."""
    lines = strip_fenced_code_blocks(text).splitlines()
    capturing = False
    buf: list[str] = []
    prefix_lower = heading_prefix.lower()
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            if line[3:].strip().lower().startswith(prefix_lower):
                capturing = True
            continue
        if capturing:
            buf.append(line)
    return "\n".join(buf).strip()


def _parse_table_rows(section_text: str) -> list[list[str]]:
    """Parse data rows from the first markdown pipe table in section_text."""
    rows: list[list[str]] = []
    header_seen = False
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header_seen:
                break
            continue
        raw = stripped[1:-1] if stripped.endswith("|") and not stripped.endswith(r"\|") else stripped[1:]
        cells = [c.replace(r"\|", "|").strip() for c in re.split(r"(?<!\\)\|", raw)]
        if all(re.match(r"^:?-+:?$", c.strip()) or not c.strip() for c in cells):
            continue
        if not header_seen:
            header_seen = True
            continue
        rows.append(cells)
    return rows


def _expand_id_cell(cell: str, prefix: str) -> set[str]:
    """Expand ID lists or ranges (`REQ-001..REQ-003`) from an INDEX.md cell."""
    cleaned = cell.strip("` ").strip()
    if not cleaned or cleaned.lower() == "none":
        return set()
    ids = set(re.findall(rf"\b{prefix}-\d+\b", cleaned))
    for m in re.finditer(rf"\b{prefix}-(\d+)\s*(?:\.\.|–)\s*{prefix}-(\d+)\b", cleaned):
        start_s, end_s = m.group(1), m.group(2)
        width = max(len(start_s), len(end_s), 3)
        for num in range(int(start_s), int(end_s) + 1):
            ids.add(f"{prefix}-{num:0{width}d}")
    return ids


def _parse_metadata_fields(spec_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in strip_fenced_code_blocks(spec_text).splitlines():
        m = re.match(r"^[-*]\s+([^:]+):\s*(.*)$", line.strip())
        if m:
            fields.setdefault(m.group(1).strip(), m.group(2).strip())
    return fields


def _check_prose_hygiene(label: str, text: str, errors: list[str]) -> None:
    prose = strip_inline_code(HTML_COMMENT_RE.sub("", strip_fenced_code_blocks(text)), "")
    for m in PLACEHOLDER_RE.finditer(prose):
        inner = m.group(1).strip()
        tag_m = HTML_TAG_RE.match(inner)
        if tag_m and tag_m.group(1).lower() in SAFE_HTML_TAGS:
            continue
        errors.append(f"{label}: leftover placeholder '<{inner}>'")
    for m in TODO_RE.finditer(prose):
        errors.append(f"{label}: unowned '{m.group(1)}' marker found")


def _check_links(
    md_path: Path,
    text: str,
    workspace_root: Path,
    slug_cache: dict[Path, set[str]],
    errors: list[str],
    label: str,
) -> None:
    prose = strip_inline_code(HTML_COMMENT_RE.sub("", strip_fenced_code_blocks(text)), "code")
    for m in LINK_RE.finditer(prose):
        target = m.group(2).strip("<>")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        raw_rel, _, raw_anchor = target.partition("#")
        rel_part = unquote(raw_rel)
        anchor = unquote(raw_anchor)
        if rel_part.startswith("/"):
            dest = (workspace_root / rel_part.lstrip("/")).resolve()
        elif rel_part:
            dest = (md_path.parent / rel_part).resolve()
        else:
            dest = md_path.resolve()
        if not dest.is_relative_to(workspace_root):
            errors.append(f"{label}: link target '{target}' escapes workspace root")
            continue
        if not dest.exists():
            errors.append(f"{label}: broken link target '{target}'")
            continue
        if anchor:
            if not dest.is_file():
                errors.append(f"{label}: anchor '#{anchor}' requires a file target in '{target}'")
                continue
            if dest.suffix.lower() == ".md":
                if dest not in slug_cache:
                    target_text = _read_utf8(dest, f"{label} -> {target}", errors)
                    if target_text is None:
                        continue
                    slug_cache[dest] = extract_heading_slugs(target_text)
                if anchor not in slug_cache[dest]:
                    errors.append(f"{label}: broken heading anchor '#{anchor}' in '{target}'")


def _parse_index(text: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    _check_prose_hygiene("INDEX.md", text, errors)
    rows = _parse_table_rows(text)
    records: dict[str, dict[str, Any]] = {}
    for row in rows:
        if len(row) != 6:
            errors.append(f"INDEX.md: malformed row with {len(row)} columns (expected 6)")
            continue
        feat_id = row[0].strip("` ")
        if feat_id in records:
            errors.append(f"INDEX.md: duplicate catalog entry for '{feat_id}'")
            continue
        records[feat_id] = {
            "feature_id": feat_id,
            "status": row[2].strip("` "),
            "reqs": _expand_id_cell(row[3], "REQ"),
            "adrs": _expand_id_cell(row[4], "ADR"),
        }
    return records


def _status_token(cell: str) -> str:
    m = re.match(r"^(PASS|FAIL|BLOCKED|UNCHECKED)\b", cell.strip())
    return m.group(1) if m else cell.strip()


def _validate_gate1(
    decisions_text: str,
    pkg_label: str,
    errors: list[str],
    *,
    allow_unchecked: bool = False,
) -> None:
    g1_rows = _parse_table_rows(_extract_section(decisions_text, "Gate 1"))
    if not g1_rows:
        errors.append(f"{pkg_label}/decisions.md: missing Gate 1 table rows")
        return
    if len(g1_rows) != 6:
        errors.append(f"{pkg_label}/decisions.md: Gate 1 expected 6 normative checks, got {len(g1_rows)}")
    allowed = {"PASS", "UNCHECKED"} if allow_unchecked else {"PASS"}
    for row in g1_rows:
        token = _status_token(row[1]) if len(row) >= 2 else ""
        if token not in allowed:
            check_name = row[0] if row else "unknown"
            errors.append(f"{pkg_label}/decisions.md: Gate 1 check '{check_name}' is '{token or 'missing'}' (expected PASS)")


def _validate_gate2_and_tasks(
    tasks_text: str,
    spec_acs: list[str],
    status: str,
    provisional_reqs: set[str],
    provisional_acs: set[str],
    pkg_label: str,
    errors: list[str],
    *,
    allow_unchecked: bool = False,
) -> None:
    g2_section = _extract_section(tasks_text, "Gate 2")
    g2_rows = _parse_table_rows(g2_section)
    if not g2_rows:
        errors.append(f"{pkg_label}/tasks.md: missing Gate 2 table rows")
        return
    mapped_acs = {row[1].strip("` ") for row in g2_rows if len(row) >= 2}
    for ac in spec_acs:
        if ac not in mapped_acs:
            errors.append(f"{pkg_label}/tasks.md: missing Gate 2 row for {ac}")

    spec_acs_set = set(spec_acs)
    for row in g2_rows:
        req_id = row[0].strip("` ")
        ac_id = row[1].strip("` ") if len(row) > 1 else "?"
        if spec_acs_set:
            if ac_id not in spec_acs_set:
                errors.append(f"{pkg_label}/tasks.md: Gate 2 row references unknown/phantom AC '{ac_id}'")
            else:
                req_m = re.match(r"^REQ-(\d+)$", req_id)
                ac_m = re.match(r"^AC-(\d+)-\d+$", ac_id)
                if not req_m or not ac_m or req_m.group(1) != ac_m.group(1):
                    errors.append(f"{pkg_label}/tasks.md: Gate 2 row '{req_id}' does not match '{ac_id}'")
        if status in {"Planning", "In-Progress"}:
            if ac_id in provisional_acs:
                allowed = {"BLOCKED"}
            elif req_id in provisional_reqs:
                allowed = {"PASS", "BLOCKED"}
            else:
                allowed = {"PASS"}
        else:
            allowed = {"PASS"}
        if allow_unchecked:
            allowed = allowed | {"UNCHECKED"}
        token = _status_token(row[-1])
        if token not in allowed:
            errors.append(f"{pkg_label}/tasks.md: Gate 2 row '{ac_id}' has invalid status '{token}' for {status}")
    allowed_bullets = {"PASS", "UNCHECKED"} if allow_unchecked else {"PASS"}
    for bullet_name in ("Backward scope check", "Reference and catalog consistency"):
        m = re.search(rf"^[-*]\s+{re.escape(bullet_name)}:\s*(.+)$", g2_section, re.MULTILINE)
        if not m:
            errors.append(f"{pkg_label}/tasks.md: missing Gate 2 '{bullet_name}' bullet")
        else:
            token = _status_token(m.group(1))
            if token not in allowed_bullets:
                errors.append(f"{pkg_label}/tasks.md: Gate 2 '{bullet_name}' is '{token}' (expected PASS)")

    if status in {"In-Testing", "Verified"} and re.search(r"^\s*[-*]\s+\[\s\]", strip_fenced_code_blocks(tasks_text), re.MULTILINE):
        errors.append(f"{pkg_label}/tasks.md: unchecked task '- [ ]' remains in {status}")


def _validate_execution_runs(
    verif_text: str,
    planned_sec: str,
    spec_acs: list[str],
    status: str,
    pkg_label: str,
    errors: list[str],
) -> None:
    exec_sec = _extract_section(verif_text, "Execution evidence")
    run_blocks = [
        p for p in re.split(r"(?=^###\s+Run\s+\d+\b)", exec_sec, flags=re.MULTILINE)
        if re.match(r"^###\s+Run\s+\d+\b", p)
    ]
    if "No checks have been executed." in exec_sec or not run_blocks:
        errors.append(f"{pkg_label}/verification.md: Execution evidence missing run record in {status}")
        return

    ac_outcomes: dict[str, str] = {}
    run_by_slug: dict[str, tuple[dict[str, str], str | None]] = {}
    any_result_line = False
    block_fallback: str | None = None

    for block in run_blocks:
        base_slug = heading_slug(block.splitlines()[0].lstrip("#").strip())
        run_slug = base_slug
        if run_slug in run_by_slug:
            errors.append(f"{pkg_label}/verification.md: duplicate execution run heading slug '#{base_slug}'")
            idx = 1
            while run_slug in run_by_slug:
                run_slug = f"{base_slug}-{idx}"
                idx += 1
        result_lines = re.findall(r"^[-*]\s+Result:\s*(.+)$", strip_fenced_code_blocks(block), re.MULTILINE)
        block_acs: dict[str, str] = {}
        block_fallback = None
        for rl in result_lines:
            any_result_line = True
            matches = re.findall(r"(AC-\d+-\d+)\s*:?\s*`?(PASS|FAIL|BLOCKED|UNCHECKED)`?", rl)
            if matches:
                for ac_id, outcome in matches:
                    ac_outcomes[ac_id] = outcome
                    block_acs[ac_id] = outcome
            elif re.search(r"\b(?:FAIL|BLOCKED|UNCHECKED)\b", rl):
                block_fallback = "FAIL"
            elif re.search(r"\bPASS\b", rl):
                block_fallback = "PASS"
        if block_fallback is not None:
            for ac in spec_acs:
                if ac not in block_acs:
                    ac_outcomes[ac] = block_fallback
        run_by_slug[run_slug] = (block_acs, block_fallback)

    if not any_result_line:
        errors.append(f"{pkg_label}/verification.md: execution runs missing Result line in {status}")
    elif not spec_acs:
        if block_fallback != "PASS":
            errors.append(f"{pkg_label}/verification.md: latest execution run Result is '{block_fallback or 'missing'}' (expected PASS) in {status}")
    else:
        for ac in spec_acs:
            outcome = ac_outcomes.get(ac, "missing")
            if outcome != "PASS":
                errors.append(f"{pkg_label}/verification.md: {ac} latest Result is '{outcome}' (expected PASS) in {status}")

    current_ac: str | None = None
    for line in planned_sec.splitlines():
        hm = re.match(r"^#{2,6}\s+(AC-\d+-\d+)\b", line)
        if hm:
            current_ac = hm.group(1)
        elif current_ac and re.match(r"^[-*]\s+Execution:", line):
            for anchor in re.findall(r"\]\([^)]*#(run-[^)\s]+)\)", line):
                if anchor not in run_by_slug:
                    continue
                r_acs, r_fb = run_by_slug[anchor]
                linked_outcome = r_acs.get(current_ac, r_fb)
                if linked_outcome is not None and linked_outcome != "PASS":
                    errors.append(
                        f"{pkg_label}/verification.md: {current_ac} Execution links to '#{anchor}' which recorded '{linked_outcome}'"
                    )


def _validate_verification(
    verif_text: str,
    spec_acs: list[str],
    status: str,
    pkg_label: str,
    errors: list[str],
) -> None:
    verif_clean = strip_fenced_code_blocks(verif_text)
    planned_sec = _extract_section(verif_text, "Planned checks")
    if not planned_sec:
        errors.append(f"{pkg_label}/verification.md: missing or empty '## Planned checks' section")
    planned_headings = set(VERIF_AC_HEADING_RE.findall(verif_clean))
    for ac in spec_acs:
        if ac not in planned_headings:
            errors.append(f"{pkg_label}/verification.md: missing planned check heading for {ac}")

    if status in {"In-Testing", "Verified"}:
        if re.search(r"^[-*]\s+Execution:\s*(?:Not run\b|Blocked pending)", verif_clean, re.MULTILINE):
            errors.append(f"{pkg_label}/verification.md: planned check still marked Not run / Blocked pending in {status}")
        _validate_execution_runs(verif_text, planned_sec, spec_acs, status, pkg_label, errors)

    if status == "Verified":
        obs_sec = _extract_section(verif_text, "Real-world observations")
        if not obs_sec or obs_sec.strip() == "No real-world confirmation has been recorded.":
            errors.append(f"{pkg_label}/verification.md: Real-world observations missing confirmation for Verified")


def _validate_single_package(
    pkg_dir: Path,
    *,
    stage: str,
    single_target: bool,
    workspace_root: Path,
    index_records: dict[str, dict[str, Any]],
    slug_cache: dict[Path, set[str]],
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Validate one spec package directory and return (declared_reqs, declared_adrs)."""
    pkg_id = pkg_dir.name
    spec_path = pkg_dir / "spec.md"
    if not spec_path.is_file():
        errors.append(f"{pkg_id}: missing or empty required file 'spec.md'")
        return [], []
    spec_text = _read_utf8(spec_path, f"{pkg_id}/spec.md", errors)
    if spec_text is None:
        return [], []
    if not spec_text.strip():
        errors.append(f"{pkg_id}: missing or empty required file 'spec.md'")
        return [], []

    spec_clean = strip_fenced_code_blocks(spec_text)
    meta = _parse_metadata_fields(spec_text)
    status = meta.get("Status", "")
    if status not in VALID_STATUSES:
        errors.append(f"{pkg_id}/spec.md: invalid Status '{status}'")
    if meta.get("Feature ID", "") != pkg_id:
        errors.append(f"{pkg_id}/spec.md: Feature ID '{meta.get('Feature ID', '')}' does not match directory '{pkg_id}'")

    is_abandoned = status == "Abandoned"
    is_workspace_planning = not single_target and status == "Planning"
    contents: dict[str, str] = {"spec.md": spec_text}
    _check_prose_hygiene(f"{pkg_id}/spec.md", spec_text, errors)
    _check_links(spec_path, spec_text, workspace_root, slug_cache, errors, f"{pkg_id}/spec.md")

    other_docs = ("decisions.md",) if stage == "gate1" else ("decisions.md",) + DERIVED_DOCS
    for fname in other_docs:
        fpath = pkg_dir / fname
        if not fpath.is_file():
            if not (is_abandoned or is_workspace_planning):
                errors.append(f"{pkg_id}: missing or empty required file '{fname}'")
            continue
        text = _read_utf8(fpath, f"{pkg_id}/{fname}", errors)
        if text is None:
            continue
        if not text.strip():
            if not (is_abandoned or is_workspace_planning):
                errors.append(f"{pkg_id}: missing or empty required file '{fname}'")
            continue
        contents[fname] = text
        _check_prose_hygiene(f"{pkg_id}/{fname}", text, errors)
        _check_links(fpath, text, workspace_root, slug_cache, errors, f"{pkg_id}/{fname}")

    declared_reqs = DECLARED_REQ_RE.findall(spec_clean)
    if not declared_reqs:
        errors.append(f"{pkg_id}/spec.md: no declared REQ-NNN headings found")
    elif len(declared_reqs) != len(set(declared_reqs)):
        errors.append(f"{pkg_id}/spec.md: duplicate REQ-NNN declaration within package")

    decisions_clean = strip_fenced_code_blocks(contents["decisions.md"]) if "decisions.md" in contents else ""
    declared_adrs = DECLARED_ADR_RE.findall(decisions_clean)
    if len(declared_adrs) != len(set(declared_adrs)):
        errors.append(f"{pkg_id}/decisions.md: duplicate ADR-NNN declaration within package")

    if pkg_id not in index_records:
        errors.append(f"INDEX.md: missing catalog entry for '{pkg_id}'")
    else:
        rec = index_records[pkg_id]
        if rec["status"] != status:
            errors.append(f"INDEX.md: status '{rec['status']}' mismatches spec.md '{status}' for '{pkg_id}'")
        if rec["reqs"] != set(declared_reqs):
            errors.append(f"INDEX.md: REQ IDs {sorted(rec['reqs'])} mismatch spec.md {sorted(set(declared_reqs))} for '{pkg_id}'")
        if rec["adrs"] != set(declared_adrs):
            errors.append(f"INDEX.md: ADR IDs {sorted(rec['adrs'])} mismatch decisions.md {sorted(set(declared_adrs))} for '{pkg_id}'")

    unique_reqs = list(dict.fromkeys(declared_reqs))
    unique_adrs = list(dict.fromkeys(declared_adrs))
    if is_abandoned:
        return unique_reqs, unique_adrs

    req_section = _extract_section(spec_text, "Requirements")
    spec_acs = AC_DECL_RE.findall(req_section)
    provisional_reqs = set(PROVISIONAL_REQ_RE.findall(spec_clean))
    provisional_acs = set(PROVISIONAL_AC_RE.findall(spec_clean))

    if not is_workspace_planning:
        if not req_section:
            errors.append(f"{pkg_id}/spec.md: missing or empty '## Requirements' section")
        for req in unique_reqs:
            req_num = req.split("-", 1)[1]
            if not any(ac.startswith(f"AC-{req_num}-") for ac in spec_acs):
                errors.append(f"{pkg_id}/spec.md: {req} has no declared AC-{req_num}-* acceptance criteria")

        first_entered = meta.get("First entered In-Testing", "")
        if status in {"In-Testing", "Verified"}:
            if not DATE_RE.match(first_entered):
                errors.append(f"{pkg_id}/spec.md: First entered In-Testing must be YYYY-MM-DD in {status} (got '{first_entered}')")
            if provisional_reqs or provisional_acs:
                errors.append(f"{pkg_id}/spec.md: [PROVISIONAL] items cannot remain in {status}")
        if status == "Verified":
            hist_sec = _extract_section(spec_text, "Approvals and lifecycle history")
            if not hist_sec or hist_sec.strip() == "No approval or lifecycle transition has been recorded yet.":
                errors.append(f"{pkg_id}/spec.md: Approvals and lifecycle history missing confirmation for Verified")

        for doc_name, doc_text in contents.items():
            if doc_name == "spec.md":
                continue
            tokens = set(REQ_TOKEN_RE.findall(doc_text))
            for req in unique_reqs:
                if req not in tokens:
                    errors.append(f"{pkg_id}/{doc_name}: missing requirement reference {req}")

    if "decisions.md" in contents:
        _validate_gate1(contents["decisions.md"], pkg_id, errors, allow_unchecked=is_workspace_planning)

    if stage == "full":
        if "tasks.md" in contents:
            _validate_gate2_and_tasks(
                contents["tasks.md"],
                spec_acs,
                status,
                provisional_reqs,
                provisional_acs,
                pkg_id,
                errors,
                allow_unchecked=is_workspace_planning,
            )
        if "verification.md" in contents and not is_workspace_planning:
            _validate_verification(contents["verification.md"], spec_acs, status, pkg_id, errors)

    return unique_reqs, unique_adrs


def _find_workspace_root(specs_dir: Path) -> Path:
    for anc in (specs_dir, *specs_dir.parents):
        if (anc / ".git").exists():
            return anc.resolve()
    return (specs_dir.parent.parent if specs_dir.parent.name == "docs" else specs_dir.parent).resolve()


def _resolve_specs_dir(root: Path) -> tuple[Path | None, Path | None]:
    """Resolve (specs_dir, single_pkg_dir) from a workspace root, docs/specs, or package path."""
    resolved = root.resolve()
    if (resolved / "docs" / "specs").is_dir():
        return resolved / "docs" / "specs", None
    if (resolved / "INDEX.md").is_file():
        return resolved, None
    if (resolved / "spec.md").is_file():
        return resolved.parent, resolved
    if resolved.name == "specs":
        return resolved, None
    return None, None


def validate_workspace(root: Path | str, *, stage: str = "full", force_all: bool = False) -> dict[str, Any]:
    """Validate all specs (or one package) under root and return structured report."""
    errors: list[str] = []
    specs_dir, single_pkg = _resolve_specs_dir(Path(root))
    if force_all:
        single_pkg = None
    if specs_dir is None or not specs_dir.is_dir():
        return {"valid": False, "errors": [f"docs/specs directory not found under '{root}'"], "packages": []}

    index_path = specs_dir / "INDEX.md"
    if not index_path.is_file():
        return {"valid": False, "errors": [f"Missing catalog file: {index_path}"], "packages": []}

    index_text = _read_utf8(index_path, "INDEX.md", errors)
    if index_text is None:
        return {"valid": False, "errors": errors, "packages": []}

    workspace_root = _find_workspace_root(specs_dir)
    slug_cache: dict[Path, set[str]] = {}
    _check_links(index_path, index_text, workspace_root, slug_cache, errors, "INDEX.md")
    index_records = _parse_index(index_text, errors)

    all_pkg_dirs = sorted(p.resolve() for p in specs_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    if single_pkg is not None and single_pkg not in all_pkg_dirs:
        all_pkg_dirs = sorted([*all_pkg_dirs, single_pkg])
    target_dirs = [single_pkg] if single_pkg else all_pkg_dirs
    req_owners: dict[str, list[str]] = {}
    adr_owners: dict[str, list[str]] = {}

    for pkg_dir in all_pkg_dirs:
        if pkg_dir in target_dirs:
            reqs, adrs = _validate_single_package(
                pkg_dir,
                stage=stage,
                single_target=single_pkg is not None,
                workspace_root=workspace_root,
                index_records=index_records,
                slug_cache=slug_cache,
                errors=errors,
            )
        else:
            spec_p = pkg_dir / "spec.md"
            dec_p = pkg_dir / "decisions.md"
            spec_txt = _read_utf8(spec_p, f"{pkg_dir.name}/spec.md", errors) if spec_p.is_file() else None
            dec_txt = _read_utf8(dec_p, f"{pkg_dir.name}/decisions.md", errors) if dec_p.is_file() else None
            reqs = DECLARED_REQ_RE.findall(strip_fenced_code_blocks(spec_txt)) if spec_txt else []
            adrs = DECLARED_ADR_RE.findall(strip_fenced_code_blocks(dec_txt)) if dec_txt else []
        for req in dict.fromkeys(reqs):
            req_owners.setdefault(req, []).append(pkg_dir.name)
        for adr in dict.fromkeys(adrs):
            adr_owners.setdefault(adr, []).append(pkg_dir.name)

    if not single_pkg:
        pkg_names = {p.name for p in all_pkg_dirs}
        for feat_id in index_records:
            if feat_id not in pkg_names:
                errors.append(f"INDEX.md: catalog entry '{feat_id}' has no package directory")

    for kind, owners_map in (("REQ", req_owners), ("ADR", adr_owners)):
        for item_id, owners in sorted(owners_map.items()):
            if len(owners) > 1:
                errors.append(f"Duplicate declared {kind} {item_id} across packages: {', '.join(owners)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "packages": [p.name for p in target_dirs],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for validate_specs."""
    parser = argparse.ArgumentParser(description="Validate five-document docs/specs packages.")
    parser.add_argument("target", nargs="?", default=".", help="Workspace root, docs/specs, or package path")
    parser.add_argument("--all", action="store_true", help="Validate all packages under docs/specs")
    parser.add_argument("--stage", choices=("gate1", "full"), default="full", help="Validation stage")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    report = validate_workspace(Path(args.target), stage=args.stage, force_all=args.all)

    if args.json:
        print(json.dumps(report, indent=2))
    elif report["valid"]:
        print(f"OK ({len(report['packages'])} package(s) validated, stage={args.stage})")
    else:
        for err in report["errors"]:
            print(f"ERROR: {err}", file=sys.stderr)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
