"""Interactive CLI entry point for Note Vault."""

from __future__ import annotations

from note_vault import ui
from note_vault.models import Note
from note_vault.notes import NoteError, NoteService
from note_vault.vaults import Vault, VaultError, VaultService

MENU: list[dict] = [
    {"name": "New Note", "value": "new_note"},
    {"name": "Open Note", "value": "open_note"},
    {"name": "List Notes", "value": "list_notes"},
    {"name": "Search Notes", "value": "search_notes"},
    {"name": "New Vault", "value": "new_vault"},
    {"name": "Open Vault", "value": "open_vault"},
    {"name": "List Vaults", "value": "list_vaults"},
    {"name": "Lock Vault", "value": "lock_vault"},
    {"name": "Unlock Vault", "value": "unlock_vault"},
    {"name": "Rename Vault", "value": "rename_vault"},
    {"name": "Delete Vault", "value": "delete_vault"},
    {"name": "Exit", "value": "exit"},
]

NOTE_MENU: list[dict] = [
    {"name": "View", "value": "view"},
    {"name": "Append", "value": "append"},
    {"name": "Replace content", "value": "replace"},
    {"name": "Rename", "value": "rename"},
    {"name": "Delete", "value": "delete"},
    {"name": "Back", "value": "back"},
]


class NoteVaultApp:
    """Ties the services and the interactive menu together."""

    def __init__(self) -> None:
        self.vaults = VaultService()
        self.notes = NoteService(self.vaults)

    @property
    def current(self) -> Vault | None:
        return self.vaults.current_vault

    def run(self) -> None:
        while True:
            try:
                choice = self._main_menu()
                if choice == "exit":
                    break
                getattr(self, f"_{choice}")()
            except KeyboardInterrupt:
                ui.info("Exiting.")
                break
            except (VaultError, NoteError) as exc:
                ui.error(str(exc))
            ui.pause()

    # --- shared helpers ---

    def _ensure_unlocked(self) -> None:
        vault = self.current
        if vault is None:
            raise NoteError("No vault is open; open or create one first")
        if self.vaults.accessible(vault):
            return
        password = ui.prompt_secret(f"Vault '{vault.name}' is locked. Password:")
        if not self.vaults.unlock(vault.name, password):
            raise NoteError("Incorrect password")
        ui.success(f"Vault '{vault.name}' unlocked")

    def _vault_picker(self, message: str) -> Vault:
        vaults = self.vaults.list()
        if not vaults:
            raise VaultError("No vaults yet; create one first")
        choices = ui.vault_choices(
            vaults,
            self.current.name if self.current else None,
            self.vaults.session.unlocked,
        )
        return ui.prompt_select(message, choices)

    def _note_actions(self, note: Note) -> None:
        while True:
            action = ui.prompt_select(f"Note: {note.name}", NOTE_MENU)
            if action == "view":
                ui.clear()
                ui.info(note.name)
                ui.console.print("=" * 40)
                ui.console.print(self.notes.read(note))
                ui.console.print("=" * 40)
            elif action == "append":
                content = ui.prompt_content("Content to append:")
                self.notes.append(note, content)
                ui.success(f"Appended to '{note.name}'")
            elif action == "replace":
                content = ui.prompt_content("New content:")
                self.notes.replace(note, content)
                ui.success(f"Replaced content of '{note.name}'")
            elif action == "rename":
                new_title = ui.prompt_text("New title:", default=note.name)
                if new_title != note.name:
                    self.notes.rename(note, new_title)
                    ui.success(f"Renamed to '{note.name}'")
            elif action == "delete":
                if ui.prompt_confirm(
                    f"Delete note '{note.name}'? This cannot be undone.", default=False
                ):
                    self.notes.delete(note)
                    ui.success("Note deleted")
                    return
            else:
                return

    # --- menu handlers ---

    def _new_note(self) -> None:
        self._ensure_unlocked()
        title = ui.prompt_text("Note title:")
        content = ui.prompt_content("Note content (Esc then Enter to finish):")
        note = self.notes.create(title, content)
        ui.success(f"Note '{note.name}' saved")

    def _open_note(self) -> None:
        self._ensure_unlocked()
        notes = self.notes.list()
        if not notes:
            ui.warn("No notes in this vault yet")
            return
        note = ui.prompt_select("Select a note:", ui.note_choices(notes))
        self._note_actions(note)

    def _list_notes(self) -> None:
        self._ensure_unlocked()
        ui.render_notes_table(self.notes.list())

    def _search_notes(self) -> None:
        self._ensure_unlocked()
        query = ui.prompt_text("Search for:")
        matches = self.notes.search(query)
        if not matches:
            ui.warn("No matches found")
            return
        ui.render_notes_table(matches)
        if ui.prompt_confirm("Open one of these?", default=False):
            note = ui.prompt_select("Select a note:", ui.note_choices(matches))
            self._note_actions(note)

    def _new_vault(self) -> None:
        name = ui.prompt_text("Vault name:")
        if ui.prompt_confirm("Protect this vault with a password?", default=False):
            password = ui.prompt_secret("Password:")
            self.vaults.create(name, password)
        else:
            self.vaults.create(name)
        self.vaults.set_current(name)
        ui.success(f"Vault '{name}' created and set as current")

    def _open_vault(self) -> None:
        vault = self._vault_picker("Select a vault to open:")
        if vault.locked and not self.vaults.accessible(vault):
            password = ui.prompt_secret(f"Vault '{vault.name}' is locked. Password:")
            if not self.vaults.unlock(vault.name, password):
                raise NoteError("Incorrect password")
            ui.success(f"Vault '{vault.name}' unlocked")
        self.vaults.set_current(vault.name)
        ui.success(f"Vault '{vault.name}' is now current")

    def _list_vaults(self) -> None:
        ui.render_vaults_table(
            self.vaults.list(),
            self.current.name if self.current else None,
            self.vaults.session.unlocked,
        )

    def _lock_vault(self) -> None:
        vault = self.current
        if vault is None:
            raise VaultError("No vault is open; open or create one first")
        if not vault.has_password:
            password = ui.prompt_secret("This vault has no password yet. Set one:")
            self.vaults.lock(vault.name, password)
        else:
            self.vaults.lock(vault.name)
        ui.success(f"Vault '{vault.name}' locked")

    def _unlock_vault(self) -> None:
        vault = self.current
        if vault is None:
            raise VaultError("No vault is open; open or create one first")
        if not self.vaults.accessible(vault):
            password = ui.prompt_secret(f"Password for vault '{vault.name}':")
            if not self.vaults.unlock(vault.name, password):
                raise NoteError("Incorrect password")
        ui.success(f"Vault '{vault.name}' unlocked")

    def _rename_vault(self) -> None:
        vault = self._vault_picker("Select a vault to rename:")
        new_name = ui.prompt_text("New name:", default=vault.name)
        if new_name != vault.name:
            self.vaults.rename(vault.name, new_name)
            ui.success(f"Vault renamed to '{new_name}'")

    def _delete_vault(self) -> None:
        vault = self._vault_picker("Select a vault to delete:")
        if ui.prompt_confirm(
            f"Delete vault '{vault.name}' and all its notes? This cannot be undone.",
            default=False,
        ):
            self.vaults.delete(vault.name)
            ui.success("Vault deleted")

    # --- main menu ---

    def _main_menu(self) -> str:
        ui.clear()
        ui.console.print("[bold magenta]Note Vault CLI[/] - a secure note manager")
        if self.current is not None:
            ui.info(f"Current vault: {self.current.name}")
        return ui.prompt_select("Main menu", MENU)


def main() -> None:
    NoteVaultApp().run()
