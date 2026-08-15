from __future__ import annotations

from click.testing import CliRunner
from gits.cli import cli, main


def test_help():
    runner = CliRunner()
    r = runner.invoke(cli, ["--help"])
    assert r.exit_code == 0
    assert "Usage:" in r.output


def test_get_help():
    runner = CliRunner()
    r = runner.invoke(cli, ["get", "--help"])
    assert r.exit_code == 0
    assert "get" in r.output


def test_zip_help():
    runner = CliRunner()
    r = runner.invoke(cli, ["zip", "--help"])
    assert r.exit_code == 0
    assert "zip" in r.output


def test_push_help():
    runner = CliRunner()
    r = runner.invoke(cli, ["push", "--help"])
    assert r.exit_code == 0
    assert "push" in r.output


def test_pull_help():
    runner = CliRunner()
    r = runner.invoke(cli, ["pull", "--help"])
    assert r.exit_code == 0
    assert "pull" in r.output


def test_version():
    assert main(["--version"]) == 0
    assert main(["-V"]) == 0


def test_zip_invalid_url():
    runner = CliRunner()
    r = runner.invoke(cli, ["zip", "not-a-url"])
    assert r.exit_code == 1
    assert "[-]" in r.output


def test_invalid_url():
    assert main(["not-a-url"]) == 1


def test_empty():
    assert main([]) == 2