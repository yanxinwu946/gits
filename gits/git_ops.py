from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    ...


def _git(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    defaults: dict = {"text": True, "capture_output": True}
    defaults.update(kwargs)
    return subprocess.run(["git", *args], **defaults)


def clone_repo(url: str, dest: Path, branch: str | None = None) -> None:
    cmd = ["clone", "--depth=1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [url, str(dest)]
    r = _git(cmd)
    if r.returncode != 0:
        raise GitError(f"git clone failed: {r.stderr.strip()}")


def sparse_checkout(repo: Path, path: str, branch: str) -> None:
    r1 = _git(["-C", str(repo), "sparse-checkout", "set", path])
    if r1.returncode != 0:
        raise GitError(f"git sparse-checkout failed: {r1.stderr.strip()}")
    r2 = _git(["-C", str(repo), "checkout", branch])
    if r2.returncode != 0:
        raise GitError(f"git checkout '{branch}' failed: {r2.stderr.strip()}")


def stage_all() -> None:
    r = _git(["add", "."])
    if r.returncode != 0:
        raise GitError(f"git add failed: {r.stderr.strip()}")


def commit(message: str) -> bool:
    r = _git(["commit", "-m", message])
    return r.returncode == 0


def push(force: bool = False) -> None:
    cmd = ["push", "--force-with-lease"] if force else ["push"]
    r = _git(cmd)
    if r.returncode != 0:
        raise GitError(f"git push failed: {r.stderr.strip()}")


def pull() -> None:
    r = _git(["pull"])
    if r.returncode != 0:
        raise GitError(f"git pull failed: {r.stderr.strip()}")