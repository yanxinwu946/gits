from __future__ import annotations

import io
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import httpx

from gits.git_ops import GitError, clone_repo, sparse_checkout
from gits.ui import info, spinner


class FetchError(Exception):
    ...


@dataclass
class ParsedUrl:
    owner: str
    repo: str
    type: str
    branch: str | None
    path: str | None
    raw_url: str | None = None


GITHUB_COM_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?"
    r"(?:/(?P<type>tree|blob)"
    r"(?:/(?P<branch>[^/]+)"
    r"(?:/(?P<path>.+))?)?)?$"
)

RAW_COM_RE = re.compile(
    r"^(?:https?://)?raw\.githubusercontent\.com/"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)/(?P<branch>[^/]+)/(?P<path>.+)$"
)

ARCHIVE_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)/archive/"
    r"(?P<ref>[^/]+)\.zip$"
)


def parse_github_url(url: str) -> ParsedUrl:
    cleaned = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")

    m = RAW_COM_RE.match(cleaned)
    if m:
        owner = m.group("owner")
        repo = m.group("repo")
        branch = m.group("branch")
        path = unquote(m.group("path"))
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{m.group('path')}"
        return ParsedUrl(owner=owner, repo=repo, type="raw",
                         branch=branch, path=path, raw_url=raw_url)

    m = ARCHIVE_RE.match(cleaned)
    if m:
        return ParsedUrl(owner=m.group("owner"), repo=m.group("repo"),
                         type="archive", branch=m.group("ref"), path=None)

    m = GITHUB_COM_RE.match(cleaned)
    if not m:
        raise FetchError(f"Not a valid GitHub URL: {url}")

    owner = m.group("owner")
    repo = m.group("repo").removesuffix(".git")
    ptype = m.group("type") or "repo"
    branch = m.group("branch") or None
    raw_path = m.group("path") or None
    path = unquote(raw_path) if raw_path else None

    raw_url: str | None = None
    if ptype == "blob" and branch and raw_path:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{raw_path}"

    return ParsedUrl(owner=owner, repo=repo, type=ptype,
                     branch=branch, path=path, raw_url=raw_url)


def _get(url: str) -> bytes:
    try:
        r = httpx.get(url, follow_redirects=True, timeout=30)
        r.raise_for_status()
        return r.content
    except httpx.HTTPStatusError as e:
        raise FetchError(f"HTTP {e.response.status_code}: {e.response.reason_phrase}") from e
    except httpx.RequestError as e:
        raise FetchError(f"Network error: {e}") from e


def fetch_repo(parsed: ParsedUrl, dest: Path) -> None:
    repo_url = f"https://github.com/{parsed.owner}/{parsed.repo}.git"
    info(f"Cloning {parsed.owner}/{parsed.repo}")
    with spinner("Cloning"):
        clone_repo(repo_url, dest)


def fetch_directory(parsed: ParsedUrl, dest: Path) -> Path:
    assert parsed.branch and parsed.path
    repo_url = f"https://github.com/{parsed.owner}/{parsed.repo}.git"
    name = Path(parsed.path).name
    dest_path = dest / name if dest.is_dir() else dest

    info(f"Fetching folder {parsed.path}")
    with tempfile.TemporaryDirectory() as tmp:
        with spinner("Cloning"):
            try:
                clone_repo(repo_url, Path(tmp), branch=parsed.branch)
                sparse_checkout(Path(tmp), parsed.path, parsed.branch)
            except GitError as e:
                raise FetchError(str(e)) from e
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(Path(tmp) / parsed.path, dest_path)
    return dest_path


def fetch_branch_root(parsed: ParsedUrl, dest: Path) -> None:
    assert parsed.branch
    repo_url = f"https://github.com/{parsed.owner}/{parsed.repo}.git"
    info(f"Fetching branch {parsed.branch} of {parsed.owner}/{parsed.repo}")
    with spinner("Cloning"):
        try:
            clone_repo(repo_url, dest, branch=parsed.branch)
        except GitError as e:
            raise FetchError(str(e)) from e


def fetch_file(parsed: ParsedUrl, dest: Path) -> Path:
    assert parsed.raw_url and parsed.path
    name = Path(parsed.path).name
    dest_path = dest / name if dest.is_dir() else dest

    info(f"Fetching file {name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    data = _get(parsed.raw_url)
    dest_path.write_bytes(data)
    return dest_path


def fetch_zip(parsed: ParsedUrl, dest: Path, branch: str | None = None) -> Path:
    b = branch or parsed.branch or "main"
    url = f"https://github.com/{parsed.owner}/{parsed.repo}/archive/{b}.zip"
    zip_name = f"{parsed.repo}-{b}.zip"
    dest_path = dest / zip_name if dest.is_dir() else dest

    info(f"Downloading {parsed.owner}/{parsed.repo} @ {b} → {dest_path.name}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    data = _get(url)
    dest_path.write_bytes(data)
    return dest_path


def fetch_archive(parsed: ParsedUrl, dest: Path) -> Path:
    assert parsed.branch
    url = f"https://github.com/{parsed.owner}/{parsed.repo}/archive/{parsed.branch}.zip"
    name = f"{parsed.repo}-{parsed.branch}"
    dest_path = dest / name if dest.is_dir() else dest

    info(f"Extracting archive {parsed.owner}/{parsed.repo} @ {parsed.branch}")
    dest_path.mkdir(parents=True, exist_ok=True)
    data = _get(url)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for m in zf.namelist():
            parts = m.split("/", 1)
            if len(parts) > 1:
                target = dest_path / parts[1]
                if m.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zf.read(m))
    return dest_path


def download(url: str, target: str = ".") -> Path:
    parsed = parse_github_url(url)
    dest = Path(target)

    if parsed.type == "repo":
        name = f"{parsed.owner}-{parsed.repo}"
        dest_path = dest / name if dest.is_dir() else dest
        fetch_repo(parsed, dest_path)
    elif parsed.type == "tree":
        if parsed.path:
            name = Path(parsed.path).name
            dest_path = dest / name if dest.is_dir() else dest
            fetch_directory(parsed, dest_path)
        elif parsed.branch:
            name = f"{parsed.repo}-{parsed.branch}"
            dest_path = dest / name if dest.is_dir() else dest
            fetch_branch_root(parsed, dest_path)
        else:
            raise FetchError("Missing branch in tree URL")
    elif parsed.type in ("blob", "raw"):
        if not parsed.path:
            raise FetchError("Missing file path in URL")
        name = Path(parsed.path).name
        dest_path = dest / name if dest.is_dir() else dest
        fetch_file(parsed, dest_path)
    elif parsed.type == "archive":
        name = f"{parsed.repo}-{parsed.branch}"
        dest_path = dest / name if dest.is_dir() else dest
        fetch_archive(parsed, dest_path)
    else:
        raise FetchError(f"Unknown URL type: {parsed.type}")

    return dest_path