"""Non-interactive CLI subcommands built with Typer."""

from __future__ import annotations

import getpass
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from note_vault import ui
from note_vault.editor import edit_text
from note_vault.notes import NoteError, NoteService
from note_vault.vaults import Vault, VaultError, VaultService

app = typer.Typer(
    name="note-vault",
    help="A secure terminal-based note manager with vaults and search.",
    add_completion=False,
    no_args_is_help=False,
)

note_app = typer.Typer(help="Manage notes inside a vault.")
vault_app = typer.Typer(help="Manage vaults.")

app.add_typer(note_app, name="note")
app.add_typer(vault_app, name="vault")

console = Console()
err_console = Console(stderr=True)


def get_services() -> tuple[VaultService, NoteService]:
    vaults = VaultService()
    notes = NoteService(vaults)
    return vaults, notes


def get_target_vault(
    vaults: VaultService, vault_name: str | None = None, password: str | None = None
) -> Vault:
    if vault_name:
        v = vaults.get(vault_name)
        if v is None:
            raise VaultError(f"Vault '{vault_name}' does not exist")
    else:
        v = vaults.current_vault
        if v is None:
            raise VaultError("No vault is open; open or create one first")

    if not vaults.accessible(v):
        pwd = password
        if pwd is None and sys.stdin.isatty():
            pwd = getpass.getpass(f"Password for vault '{v.name}': ")
        if pwd is None or not vaults.unlock(v.name, pwd):
            raise NoteError(f"Vault '{v.name}' is locked (incorrect or missing password)")

    return v


# --- Note Subcommands ---


@note_app.command("add")
def note_add(
    title: str = typer.Argument(..., help="Title of the note"),
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="Inline content")] = None,
    file: Annotated[
        Path | None, typer.Option("--file", "-f", help="File path to read from")
    ] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
) -> None:
    """Create a new note in the specified or current vault."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    vaults.set_current(target_vault.name)

    if content is not None:
        text = content
    elif file is not None:
        if not file.exists():
            raise NoteError(f"File '{file}' does not exist")
        text = file.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        text = edit_text(suffix=".txt")

    note = notes.create(title, text)
    ui.success(f"Note '{note.name}' saved in vault '{target_vault.name}'")


@note_app.command("cat")
@note_app.command("show")
def note_cat(
    title: str = typer.Argument(..., help="Title of the note to display"),
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
) -> None:
    """Print raw note content to stdout."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    note = notes.get(target_vault, title)
    if note is None:
        raise NoteError(f"Note '{title}' not found in vault '{target_vault.name}'")
    sys.stdout.write(notes.read(note))
    if not notes.read(note).endswith("\n"):
        sys.stdout.write("\n")


@note_app.command("edit")
def note_edit(
    title: str = typer.Argument(..., help="Title of the note to edit"),
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
) -> None:
    """Open an existing note in external editor."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    note = notes.get(target_vault, title)
    if note is None:
        raise NoteError(f"Note '{title}' not found in vault '{target_vault.name}'")
    current_content = notes.read(note)
    updated_content = edit_text(initial_content=current_content, suffix=".txt")
    notes.replace(note, updated_content)
    ui.success(f"Note '{note.name}' updated")


@note_app.command("list")
def note_list(
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """List notes in the vault."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    all_notes = notes.list(target_vault)
    if json_output:
        data = [n.to_dict() for n in all_notes]
        sys.stdout.write(json.dumps(data, indent=2) + "\n")
    else:
        ui.render_notes_table(all_notes)


@note_app.command("delete")
def note_delete(
    title: str = typer.Argument(..., help="Title of the note to delete"),
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip prompt confirmation")] = False,
) -> None:
    """Delete a note."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    note = notes.get(target_vault, title)
    if note is None:
        raise NoteError(f"Note '{title}' not found in vault '{target_vault.name}'")
    if not force:
        confirm = typer.confirm(f"Delete note '{note.name}' from vault '{target_vault.name}'?")
        if not confirm:
            ui.info("Aborted.")
            return
    notes.delete(note)
    ui.success(f"Note '{title}' deleted")


# --- Vault Subcommands ---


@vault_app.command("list")
def vault_list(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """List all vaults."""
    vaults, _ = get_services()
    all_vaults = vaults.list()
    current = vaults.current_vault.name if vaults.current_vault else None
    if json_output:
        data = [v.to_dict() for v in all_vaults]
        sys.stdout.write(json.dumps(data, indent=2) + "\n")
    else:
        ui.render_vaults_table(all_vaults, current, vaults.session.unlocked)


@vault_app.command("create")
def vault_create(
    name: str = typer.Argument(..., help="Vault name"),
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Set vault password")
    ] = None,
) -> None:
    """Create a new vault."""
    vaults, _ = get_services()
    vault = vaults.create(name, password)
    vaults.set_current(vault.name)
    ui.success(f"Vault '{vault.name}' created and set as current")


@vault_app.command("use")
@vault_app.command("select")
def vault_use(
    name: str = typer.Argument(..., help="Vault name to set active"),
) -> None:
    """Set default active vault."""
    vaults, _ = get_services()
    if not vaults.set_current(name):
        raise VaultError(f"Vault '{name}' does not exist")
    ui.success(f"Active vault set to '{name}'")


@vault_app.command("lock")
def vault_lock(
    name: Annotated[str | None, typer.Argument(help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Set initial password if none exists")
    ] = None,
) -> None:
    """Lock a vault."""
    vaults, _ = get_services()
    target_vault = get_target_vault(vaults, name) if name else vaults.current_vault
    if target_vault is None:
        raise VaultError("No vault specified or current")
    vaults.lock(target_vault.name, password)
    ui.success(f"Vault '{target_vault.name}' locked")


# --- Top-level Search Command ---


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query"),
    vault: Annotated[str | None, typer.Option("--vault", "-v", help="Vault name")] = None,
    password: Annotated[
        str | None, typer.Option("--password", "-p", help="Vault password if locked")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Search notes by title or content."""
    vaults, notes = get_services()
    target_vault = get_target_vault(vaults, vault, password)
    matches = notes.search(query, target_vault)

    if json_output:
        results = [
            {
                "name": n.name,
                "path": str(n.path),
                "snippet": notes.snippet(n, query),
            }
            for n in matches
        ]
        sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        if not matches:
            ui.warn("No matches found")
        else:
            ui.render_notes_table(matches)
