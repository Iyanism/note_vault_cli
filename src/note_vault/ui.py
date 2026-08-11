"""UI helpers built on rich and InquirerPy."""

from __future__ import annotations

from typing import Any

from InquirerPy import inquirer
from rich.console import Console
from rich.table import Table

from note_vault.models import Note, Vault

console = Console()


def clear() -> None:
    console.clear()


def error(message: str) -> None:
    console.print(f"[bold red]X {message}[/]")


def success(message: str) -> None:
    console.print(f"[bold green]OK {message}[/]")


def info(message: str) -> None:
    console.print(f"[bold cyan]{message}[/]")


def warn(message: str) -> None:
    console.print(f"[bold yellow]! {message}[/]")


# --- prompts ---


def prompt_text(message: str, default: str | None = None) -> str:
    if default is not None:
        return inquirer.text(message=message, default=default).execute()
    return inquirer.text(message=message).execute()


def prompt_secret(message: str) -> str:
    return inquirer.secret(message=message).execute()


def prompt_confirm(message: str, default: bool = True) -> bool:
    return inquirer.confirm(message=message, default=default).execute()


def prompt_content(message: str) -> str:
    return inquirer.text(message=message, multiline=True).execute().strip()


def prompt_select(message: str, choices: list[dict[str, Any]]) -> Any:
    return inquirer.select(message=message, choices=choices).execute()


def pause() -> None:
    inquirer.confirm(message="Press Enter to continue...", default=True).execute()


# --- renderers ---


def vault_choices(vaults: list[Vault], current_name: str | None, unlocked: set[str]) -> list[dict]:
    choices: list[dict] = []
    for vault in vaults:
        flags = []
        if vault.locked and vault.name not in unlocked:
            flags.append("locked")
        if current_name and vault.name == current_name:
            flags.append("current")
        label = vault.name
        if flags:
            label += f" ({', '.join(flags)})"
        choices.append({"name": label, "value": vault})
    return choices


def render_vaults_table(vaults: list[Vault], current_name: str | None, unlocked: set[str]) -> None:
    table = Table(title="Vaults")
    table.add_column("#", style="dim")
    table.add_column("Name")
    table.add_column("Notes", justify="right")
    table.add_column("Status")
    for index, vault in enumerate(vaults, 1):
        status = []
        if vault.locked and vault.name not in unlocked:
            status.append("locked")
        if current_name and vault.name == current_name:
            status.append("current")
        table.add_row(str(index), vault.name, str(len(vault.notes)), ", ".join(status))
    console.print(table)


def note_choices(notes: list[Note]) -> list[dict]:
    return [{"name": note.name, "value": note} for note in notes]


def render_notes_table(notes: list[Note]) -> None:
    table = Table(title="Notes")
    table.add_column("#", style="dim")
    table.add_column("Title")
    for index, note in enumerate(notes, 1):
        table.add_row(str(index), note.name)
    console.print(table)
