from __future__ import annotations

from gits.ui import info, ok, fail


def test_info(capsys):
    info("test")
    captured = capsys.readouterr()
    assert "test" in captured.err


def test_ok(capsys):
    ok("test")
    captured = capsys.readouterr()
    assert "test" in captured.out


def test_fail(capsys):
    fail("test")
    captured = capsys.readouterr()
    assert "test" in captured.err