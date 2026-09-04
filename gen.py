#!/usr/bin/env python3
"""Generate a changelog draft from git log.

Reads `git log` output, groups commits by conventional-commit type
(feat, fix, docs, refactor, perf, test, chore, security), and prints a
Keep a Changelog formatted draft to stdout.

Usage:
    python3 gen.py                    # all commits since last tag
    python3 gen.py v1.2.0..HEAD        # explicit range
    python3 gen.py --since 2026-01-01 # since a date

The output is a starting point, not a finished changelog. Edit the wording,
remove entries that do not matter to users, and add context that a commit
message cannot carry. A changelog is for people, not for git.

No dependencies beyond Python 3.8+ and git on your PATH.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

# Map conventional-commit prefixes to Keep a Changelog sections.
TYPE_TO_SECTION: dict[str, str] = {
    "feat": "Added",
    "fix": "Fixed",
    "docs": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "test": "Changed",
    "chore": "Changed",
    "security": "Security",
    "remove": "Removed",
    "deprecate": "Deprecated",
}

# conventional-commit header: type(scope): description
COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|perf|test|chore|security|remove|deprecate)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r":\s*(?P<description>.+)$",
    re.IGNORECASE,
)

# Footer lines like "BREAKING CHANGE: ..." or "Closes #123"
BREAKING_RE = re.compile(r"^BREAKING[ -]CHANGE:\s*(.+)", re.IGNORECASE)


def run_git(args: list[str]) -> str:
    """Run a git command and return stdout as text."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_log(raw: str) -> list[dict]:
    """Parse `git log --format=...` output into structured commits.

    Expected format: `%H%x00%s%x00%b%x00%ad` with `--date=short`.
    That is: hash, subject, body, date, separated by NUL.
    """
    commits = []
    for record in raw.strip().split("\n\0"):
        parts = record.split("\0")
        if len(parts) < 4:
            continue
        sha, subject, body, date = parts[0], parts[1], parts[2], parts[3]
        commits.append(
            {
                "sha": sha[:7],
                "subject": subject.strip(),
                "body": body.strip(),
                "date": date.strip(),
            }
        )
    return commits


def categorize(commits: list[dict]) -> dict[str, list[str]]:
    """Group commit descriptions by changelog section."""
    sections: dict[str, list[str]] = defaultdict(list)
    breaking: list[str] = []

    for c in commits:
        m = COMMIT_RE.match(c["subject"])
        if m:
            section = TYPE_TO_SECTION.get(m.group("type").lower(), "Changed")
            scope = f"**{m.group('scope')}**: " if m.group("scope") else ""
            desc = f"{scope}{m.group('description')}"
        else:
            section = "Changed"
            desc = c["subject"]

        # Check for breaking changes in the body.
        for line in c["body"].split("\n"):
            bm = BREAKING_RE.match(line)
            if bm:
                breaking.append(bm.group(1))

        entry = f"- {desc} ({c['sha']})"
        sections[section].append(entry)

    if breaking:
        sections["Changed"].insert(0, "- **BREAKING**: " + "; ".join(breaking))

    return sections


def format_changelog(sections: dict[str, list[str]], version: str, date_str: str) -> str:
    """Render a Keep a Changelog formatted string."""
    lines = [f"## [{version}] - {date_str}", ""]
    order = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
    for section in order:
        entries = sections.get(section, [])
        if not entries:
            continue
        lines.append(f"### {section}")
        lines.append("")
        lines.extend(entries)
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("range", nargs="?", default="", help="git revision range (e.g. v1.2.0..HEAD)")
    ap.add_argument("--since", default=None, help="date to start from (e.g. 2026-01-01)")
    ap.add_argument("--version", default="Unreleased", help="version label for the section header")
    args = ap.parse_args()

    fmt = "%H%x00%s%x00%b%x00%ad"
    git_args = ["log", f"--format={fmt}", "--date=short", "--no-merges"]
    if args.range:
        git_args.append(args.range)
    elif args.since:
        git_args.append(f"--since={args.since}")
    else:
        # Default: everything since the most recent tag.
        latest_tag = run_git(["describe", "--tags", "--abbrev=0"]).strip()
        if latest_tag:
            git_args.append(f"{latest_tag}..HEAD")

    raw = run_git(git_args)
    if not raw.strip():
        print("No commits found in the specified range.", file=sys.stderr)
        sys.exit(1)

    commits = parse_log(raw)
    sections = categorize(commits)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output = format_changelog(sections, args.version, date_str)
    print(output)


if __name__ == "__main__":
    main()
