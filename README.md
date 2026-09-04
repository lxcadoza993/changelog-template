# changelog-template

A [Keep a Changelog](https://keepachangelog.com/) format template plus a Python
script that reads `git log` and produces a changelog draft you can edit.

## What is in here

- **`CHANGELOG-template.md`** — the blank template. Copy it into a new or
  existing project and fill in the sections.
- **`gen.py`** — reads conventional-commit messages from `git log`, groups them
  by type (feat → Added, fix → Fixed, etc.), and prints a formatted draft.

## Why

Writing a changelog from scratch every release is the kind of task that gets
skipped until someone asks "what changed in 2.3?" and nobody remembers. The
script does the first pass — grouping and sorting — so you spend time on the
writing that matters, not on collecting commits.

## How to use

### Template

```bash
cp CHANGELOG-template.md /your/project/CHANGELOG.md
```

Edit the file. Add entries under `## [Unreleased]` as you go.

### Generator

```bash
# All commits since the last tag
python3 gen.py

# Explicit range
python3 gen.py v1.2.0..HEAD

# Since a date
python3 gen.py --since 2026-01-01

# Label the version
python3 gen.py --version 2.0.0
```

The output goes to stdout. Pipe it into your CHANGELOG.md or review it first:

```bash
python3 gen.py --version 2.0.0 >> CHANGELOG.md
```

The generator expects [conventional commit](https://www.conventionalcommits.org/)
messages (`feat:`, `fix:`, `docs:`, etc.). Commits that do not follow the
convention land in the "Changed" section with their raw subject line.

## Requirements

- Python 3.8+
- git on your PATH

No pip dependencies. Standard library only.

## Conventional commit types and where they land

| Prefix | Changelog section |
|--------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `security` | Security |
| `remove` | Removed |
| `deprecate` | Deprecated |
| `docs`, `refactor`, `perf`, `test`, `chore` | Changed |

## License

MIT. See [LICENSE](LICENSE).
