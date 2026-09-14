import os
import re
import subprocess
from datetime import datetime, timezone

README_PATH = "README.md"
TRACKER_HEADER = "## Problem Tracker"
TABLE_HEADER = "| S.No | Problem Name | Language | Date Solved | Solution |"
TABLE_DIVIDER = "|------|--------------|----------|-------------|----------|"


def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()


def get_changed_problem_dirs():
    before = os.getenv("GITHUB_EVENT_BEFORE", "")
    after = os.getenv("GITHUB_SHA", "")

    if before and after and before != "0000000000000000000000000000000000000000":
        diff_range = f"{before}..{after}"
    else:
        diff_range = "HEAD~1..HEAD"

    try:
        changed_files = run(f"git diff --name-status {diff_range}").splitlines()
    except Exception:
        changed_files = []

    problem_dirs = set()
    for line in changed_files:
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status, path = parts
        if status not in {"A", "M", "R"}:
            continue

        top = path.split("/", 1)[0]
        if re.match(r"^\d{4}-[a-z0-9\-]+$", top):
            problem_dirs.add(top)

    return sorted(problem_dirs)


def prettify_problem_name(slug_dir):
    name_part = slug_dir.split("-", 1)[1] if "-" in slug_dir else slug_dir
    words = name_part.replace("-", " ").split()
    return " ".join(w.capitalize() for w in words)


def read_readme():
    if not os.path.exists(README_PATH):
        return ""
    with open(README_PATH, "r", encoding="utf-8") as f:
        return f.read()


def write_readme(content):
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def ensure_tracker_section(content):
    if TRACKER_HEADER in content and TABLE_HEADER in content:
        return content

    insert_block = (
        f"\n{TRACKER_HEADER}\n\n"
        f"{TABLE_HEADER}\n"
        f"{TABLE_DIVIDER}\n"
    )
    return content + insert_block


def parse_existing_rows(content):
    lines = content.splitlines()
    rows = []
    in_table = False
    for i, line in enumerate(lines):
        if line.strip() == TABLE_HEADER:
            in_table = True
            continue
        if in_table:
            if line.strip() == TABLE_DIVIDER:
                continue
            if not line.strip().startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5:
                rows.append((i, cells))
    return rows, lines


def row_exists_for_dir(rows, slug_dir):
    for _, cells in rows:
        if slug_dir in cells[4]:
            return True
    return False


def append_rows(content, new_dirs):
    rows, lines = parse_existing_rows(content)

    if not new_dirs:
        return content

    header_idx = None
    divider_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == TABLE_HEADER:
            header_idx = idx
        if header_idx is not None and divider_idx is None and line.strip() == TABLE_DIVIDER:
            divider_idx = idx
            break

    if header_idx is None or divider_idx is None:
        return content

    end_idx = divider_idx + 1
    while end_idx < len(lines) and lines[end_idx].strip().startswith("|"):
        end_idx += 1

    existing_count = len(rows)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    to_add = []
    next_serial = existing_count + 1
    for d in new_dirs:
        if row_exists_for_dir(rows, d):
            continue
        pretty_name = prettify_problem_name(d)
        link = f"[{d}](https://github.com/mauryaanant005/Leetcode_Solutions/tree/main/{d})"
        to_add.append(f"| {next_serial} | {pretty_name} | Java | {date_str} | {link} |")
        next_serial += 1

    if not to_add:
        return content

    new_lines = lines[:end_idx] + to_add + lines[end_idx:]
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")


def main():
    changed_dirs = get_changed_problem_dirs()
    content = read_readme()
    if not content:
        content = "# Leetcode Solutions\n"

    content = ensure_tracker_section(content)
    updated = append_rows(content, changed_dirs)

    if updated != content:
        write_readme(updated)


if __name__ == "__main__":
    main()
