from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class Colors:
    def __init__(self) -> None:
        if sys.stdout.isatty():
            self.G = "\033[32m"
            self.Y = "\033[33m"
            self.R = "\033[31m"
            self.C = "\033[36m"
            self.B = "\033[1m"
            self.NC = "\033[0m"
            self.OK = f"{self.G}❯{self.NC}"
            self.WAIT = f"{self.C}❯{self.NC}"
            self.ERR = f"{self.R}✘{self.NC}"
        else:
            self.G = self.Y = self.R = self.C = self.B = self.NC = ""
            self.OK = "[OK]"
            self.WAIT = "[*]"
            self.ERR = "[ERR]"


C = Colors()


def log_info(msg: str) -> None:
    print(f"{C.OK} {msg}")


def log_step(msg: str) -> None:
    print(f"{C.WAIT} {msg}")


def log_error(msg: str, code: int = 1) -> int:
    print(f"{C.ERR} {msg}", file=sys.stderr)
    return code


def show_help() -> None:
    print(f"{C.B}GITS{C.NC} - GitHub 内容获取与同步工具")
    print()
    print(f"{C.B}用法:{C.NC}")
    print("  gits <URL> [PATH]    下载仓库、目录或单个文件")
    print("  gits push [MSG] [-f] 快速提交并推送到远程")
    print("  gits pull            拉取远程更新")
    print("  gits help            显示此帮助信息")
    print()
    print(f"{C.B}示例:{C.NC}")
    print("  gits https://github.com/user/repo/tree/main/src ./local-src")
    print('  gits push "feat: add new scripts"')
    print()


def parse_gh_url(url: str) -> str:
    url = url.split("?", 1)[0]
    url = url.split("#", 1)[0]
    return url.rstrip("/")


def run_git(args: list[str], quiet: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    kwargs = {"text": True}
    if quiet:
        kwargs.update({"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL})
    return subprocess.run(["git", *args], check=check, **kwargs)


def resolve_final_path(target: str, item_name: str) -> Path:
    target_path = Path(target)
    if target_path.is_dir():
        return target_path / item_name
    return target_path


def download_file(raw_url: str, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(raw_url) as response:
            destination.write_bytes(response.read())
    except urllib.error.URLError:
        return log_error("Download failed")
    return 0


def do_download(url: str, target: str = ".") -> int:
    clean_url = parse_gh_url(url)
    mode = "repo"
    branch = ""
    subpath_enc = ""
    raw_url = ""

    if "/tree/" in clean_url:
        mode = "folder"
        prefix, rest = clean_url.split("/tree/", 1)
        repo = f"{prefix}.git"
        branch, subpath_enc = rest.split("/", 1)
    elif "/blob/" in clean_url:
        mode = "file"
        _, rest = clean_url.split("/blob/", 1)
        branch, subpath_enc = rest.split("/", 1)
        parts = clean_url.split("/")
        slug = "/".join(parts[3:5])
        raw_url = f"https://raw.githubusercontent.com/{slug}/{branch}/{subpath_enc}"
        repo = ""
    else:
        repo = f"{clean_url.removesuffix('.git')}.git"

    subpath = urllib.parse.unquote(subpath_enc)
    item_name = urllib.parse.unquote(Path(subpath_enc if subpath_enc else clean_url).name)
    final_path = resolve_final_path(target, item_name)

    try:
        if mode == "repo":
            log_step(f"Cloning Repo: {item_name}")
            run_git(["clone", "--depth=1", repo, str(final_path)], quiet=True)
        elif mode == "folder":
            log_step(f"Fetching Folder: {subpath}")
            with tempfile.TemporaryDirectory() as tmp:
                run_git(["clone", "--filter=blob:none", "--no-checkout", "--depth=1", "--branch", branch, repo, tmp], quiet=True)
                run_git(["-C", tmp, "sparse-checkout", "set", subpath], quiet=False)
                run_git(["-C", tmp, "checkout", branch], quiet=True)
                src = Path(tmp) / subpath
                final_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, final_path)
        else:
            log_step(f"Fetching File: {item_name}")
            rc = download_file(raw_url, final_path)
            if rc != 0:
                return rc
    except ValueError:
        return log_error("Invalid GitHub URL format")
    except subprocess.CalledProcessError:
        return log_error("Git command failed")
    except FileNotFoundError as exc:
        return log_error(f"Missing file or command: {exc}")

    log_info(f"Saved to: {C.B}{final_path}{C.NC}")
    return 0


def do_push(args: list[str]) -> int:
    force = "-f" in args
    msg_parts = [part for part in args if part != "-f"]
    msg = " ".join(msg_parts).strip() or "update"

    log_step("Syncing...")
    run_git(["add", "."], quiet=False)
    run_git(["commit", "-m", msg], quiet=True, check=False)
    push_cmd = ["push"]
    if force:
        push_cmd.append("--force-with-lease")
    run_git(push_cmd, quiet=False)
    log_info("Pushed")
    return 0


def do_pull() -> int:
    log_step("Updating...")
    run_git(["pull"], quiet=True)
    log_info("Updated")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"help", "-h", "--help"}:
        show_help()
        return 0

    cmd = argv[0]
    if cmd == "push":
        return do_push(argv[1:])
    if cmd == "pull":
        return do_pull()

    if len(argv) > 2:
        return log_error("Usage: gits <URL> [PATH]")

    url = argv[0]
    target = argv[1] if len(argv) == 2 else "."
    return do_download(url, target)


if __name__ == "__main__":
    raise SystemExit(main())
