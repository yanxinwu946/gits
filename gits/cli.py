from __future__ import annotations

import sys
from importlib.metadata import version as _version

import click

from gits.fetcher import FetchError, download, fetch_zip, parse_github_url
from gits.git_ops import GitError, stage_all, commit, push, pull
from gits.ui import ok, fail, console

try:
    __version__ = _version("gits")
except Exception:
    __version__ = "0.1.0"


def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://", "github.com/", "www.github.com/"))


@click.group("gits")
def cli() -> None:
    ...


@cli.command()
@click.argument("url")
@click.argument("dest", default=".")
def get(url: str, dest: str) -> None:
    try:
        p = download(url, dest)
    except (FetchError, GitError) as e:
        fail(str(e))
        raise SystemExit(1)
    ok(f"Saved to [bold]{p}[/]")


@cli.command()
@click.argument("message", default="update")
@click.option("--force", "-f", is_flag=True)
def push(message: str, force: bool) -> None:
    try:
        stage_all()
        committed = commit(message)
        if not committed:
            console.print("∅ Nothing to commit")
        push(force=force)
    except GitError as e:
        fail(str(e))
        raise SystemExit(1)
    ok("Pushed")


@cli.command()
def pull() -> None:
    try:
        pull()
    except GitError as e:
        fail(str(e))
        raise SystemExit(1)
    ok("Updated")


@cli.command()
@click.argument("url")
@click.option("--branch", "-b", default="main")
@click.option("--output", "-o", default=".")
def zip(url: str, branch: str, output: str) -> None:
    try:
        parsed = parse_github_url(url)
        p = fetch_zip(parsed, output, branch)
    except FetchError as e:
        fail(str(e))
        raise SystemExit(1)
    ok(f"Saved to [bold]{p}[/]")


def main(argv: list[str] | None = None) -> int:
    raw = argv if argv is not None else sys.argv[1:]

    if raw and raw[0] in ("--version", "-V"):
        click.echo(f"gits {__version__}")
        return 0

    if raw and _is_url(raw[0]):
        url = raw[0]
        dest = raw[1] if len(raw) > 1 else "."
        try:
            p = download(url, dest)
        except (FetchError, GitError) as e:
            fail(str(e))
            return 1
        ok(f"Saved to [bold]{p}[/]")
        return 0

    try:
        cli(raw, standalone_mode=False)
    except SystemExit as e:
        return e.code or 0
    except click.UsageError as e:
        fail(str(e))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())