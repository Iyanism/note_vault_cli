"""Note management: CRUD, read/write helpers, and full-text search."""

from __future__ import annotations

from pathlib import Path

from note_vault.models import Note, Vault, sanitize_name
from note_vault.vaults import VaultService


class NoteError(Exception):
    """Raised for note-related failures."""


class NoteService:
    """Operations over notes stored inside a vault's directory."""

    def __init__(self, vaults: VaultService) -> None:
        self.vaults = vaults

    # --- helpers ---

    def current_vault(self) -> Vault:
        vault = self.vaults.current_vault
        if vault is None:
            raise NoteError("No vault is open; open or create one first")
        return vault

    def _require_access(self, vault: Vault) -> None:
        if not self.vaults.accessible(vault):
            raise NoteError(f"Vault '{vault.name}' is locked")

    def _vault_of(self, note: Note) -> Vault:
        vault = self.vaults.get(note.path.parent.name)
        if vault is None:
            raise NoteError("Note's vault could not be found")
        return vault

    def _abs_path(self, note: Note) -> Path:
        return self.vaults.store.vaults_dir / note.path

    # --- CRUD ---

    def create(self, title: str, content: str) -> Note:
        title = sanitize_name(title)
        vault = self.current_vault()
        self._require_access(vault)
        if self.get(vault, title) is not None:
            raise NoteError(f"Note '{title}' already exists in vault '{vault.name}'")
        rel_path = vault.path / f"{title}.txt"
        abs_path = self.vaults.store.vaults_dir / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        note = Note(name=title, path=rel_path)
        vault.notes.append(note)
        self.vaults.save()
        return note

    def get(self, vault: Vault, title: str) -> Note | None:
        for note in vault.notes:
            if note.name.lower() == title.lower():
                return note
        return None

    def list(self, vault: Vault | None = None) -> list[Note]:
        vault = vault or self.current_vault()
        self._require_access(vault)
        return list(vault.notes)

    def read(self, note: Note) -> str:
        self._require_access(self._vault_of(note))
        return self._abs_path(note).read_text(encoding="utf-8")

    def append(self, note: Note, content: str) -> None:
        if not content.strip():
            return
        self._require_access(self._vault_of(note))
        with self._abs_path(note).open("a", encoding="utf-8") as handle:
            handle.write("\n" + content)

    def replace(self, note: Note, content: str) -> None:
        self._require_access(self._vault_of(note))
        self._abs_path(note).write_text(content, encoding="utf-8")

    def rename(self, note: Note, new_title: str) -> Note:
        new_title = sanitize_name(new_title)
        vault = self._vault_of(note)
        if new_title.lower() != note.name.lower() and self.get(vault, new_title) is not None:
            raise NoteError(f"Note '{new_title}' already exists in vault '{vault.name}'")
        old_path = self._abs_path(note)
        new_path = old_path.with_name(f"{new_title}.txt")
        old_path.rename(new_path)
        note.name = new_title
        note.path = vault.path / f"{new_title}.txt"
        self.vaults.save()
        return note

    def delete(self, note: Note) -> None:
        vault = self._vault_of(note)
        self._require_access(vault)
        abs_path = self._abs_path(note)
        if abs_path.exists():
            abs_path.unlink()
        vault.notes = [existing for existing in vault.notes if existing is not note]
        self.vaults.save()

    # --- search ---

    def search(self, query: str, vault: Vault | None = None) -> list[Note]:
        query = query.strip().lower()
        if not query:
            return []
        vault = vault or self.current_vault()
        self._require_access(vault)
        matches: list[Note] = []
        for note in vault.notes:
            if query in note.name.lower():
                matches.append(note)
                continue
            try:
                content = self._abs_path(note).read_text(encoding="utf-8").lower()
            except OSError:
                content = ""
            if query in content:
                matches.append(note)
        return matches

    def snippet(self, note: Note, query: str, width: int = 60) -> str:
        """Return a text window around the first query match in a note."""
        content = self._abs_path(note).read_text(encoding="utf-8")
        index = content.lower().find(query.lower())
        if index == -1:
            return content[:width].replace("\n", " ")
        start = max(0, index - width // 2)
        end = min(len(content), index + len(query) + width // 2)
        return content[start:end].replace("\n", " ")
