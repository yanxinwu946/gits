# gits

> GitHub content fetcher & sync CLI — download any repo, folder, file, or archive from GitHub without cloning the full history.

[![Python](https://img.shields.io/badge/python-%E2%89%A53.9-blue?style=flat-square)](https://python.org)
[![License](https://img.shields.io/github/license/yanxinwu946/gits?style=flat-square)](LICENSE)

## Install

```bash
pip install .
```

## Usage

### Download

```bash
# Full repo (shallow clone)
gits get https://github.com/user/repo

# Subdirectory (sparse checkout)
gits get https://github.com/user/repo/tree/main/src/components

# Single file
gits get https://github.com/user/repo/blob/main/README.md

# Raw file URL
gits get https://raw.githubusercontent.com/user/repo/main/package.json

# Download & extract zip archive
gits get https://github.com/user/repo/archive/main.zip

# Custom save path
gits get https://github.com/user/repo/blob/main/config.yml ./my-config.yml
```

### Zip (download as .zip, no extraction)

```bash
gits zip https://github.com/user/repo
gits zip https://github.com/user/repo -b v1.0.0
gits zip https://github.com/user/repo -o /tmp/
```

### Sync

```bash
gits push "feat: add dark mode"
gits push -f "fix: rebase and squash"
gits pull
```

### URL Reference

| Pattern | Example | Behaviour |
|---------|---------|-----------|
| `:owner/:repo` | `user/repo` | Shallow clone |
| `:owner/:repo/tree/:branch/:path` | `user/repo/tree/main/src` | Sparse checkout |
| `:owner/:repo/blob/:branch/:path` | `user/repo/blob/main/README.md` | Raw file download |
| `raw.githubusercontent.com/...` | `raw.githubusercontent.com/user/repo/main/f.py` | Single file |
| `:owner/:repo/archive/:ref.zip` | `user/repo/archive/main.zip` | Zip download & extract |
| `gits zip` | `gits zip user/repo` | Zip download only |

## Project Structure

```
gits/
├── gits/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py        # click CLI entry point
│   ├── fetcher.py    # URL parsing & download logic
│   ├── git_ops.py    # git operations
│   └── ui.py         # rich terminal output
├── tests/
│   ├── test_cli.py
│   ├── test_fetcher.py
│   └── test_ui.py
├── pyproject.toml
└── README.md
```

## License

MIT