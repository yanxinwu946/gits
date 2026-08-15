from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console(stderr=True)
out = Console()


def info(msg: str) -> None:
    console.print(f"[cyan][*][/] {msg}")


def ok(msg: str) -> None:
    out.print(f"[green][+][/] {msg}")


def fail(msg: str) -> None:
    console.print(f"[red][-][/] {msg}")


def spinner(msg: str) -> Progress:
    p = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    )
    p.add_task(msg, total=None)
    p.start()
    return p