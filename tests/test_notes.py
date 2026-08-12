"""Tests for note CRUD operations."""

from __future__ import annotations

import pytest

from note_vault.models import InvalidNameError
from note_vault.notes import NoteError, NoteService
from note_vault.vaults import VaultService


@pytest.fixture
def notes(store):
    service = VaultService(store)
    service.create("Work")
    service.set_current("Work")
    return NoteService(service)


def _abs(notes, note):
    return notes.vaults.store.vaults_dir / note.path


def test_create_writes_file_and_index(notes):
    note = notes.create("Groceries", "milk eggs")
    assert _abs(notes, note).read_text(encoding="utf-8") == "milk eggs"
    assert [n.name for n in notes.list()] == ["Groceries"]


def test_create_rejects_duplicate_case_insensitive(notes):
    notes.create("Groceries", "x")
    with pytest.raises(NoteError, match="already exists"):
        notes.create("groceries", "y")


def test_create_rejects_invalid_title(notes):
    for bad in ["", "..", "a/b"]:
        with pytest.raises(InvalidNameError):
            notes.create(bad, "x")


def test_create_requires_current_vault(store):
    service = VaultService(store)
    notes = NoteService(service)
    with pytest.raises(NoteError, match="No vault is open"):
        notes.create("Anything", "x")


def test_list_and_get(notes):
    notes.create("Alpha", "one")
    notes.create("Beta", "two")
    assert [n.name for n in notes.list()] == ["Alpha", "Beta"]
    assert notes.get(notes.current_vault(), "alpha") is not None
    assert notes.get(notes.current_vault(), "missing") is None


def test_read_append_replace(notes):
    note = notes.create("Log", "line one")
    notes.append(note, "line two")
    notes.append(note, "")
    assert notes.read(note) == "line one\nline two"
    notes.replace(note, "rewritten")
    assert notes.read(note) == "rewritten"


def test_rename_updates_file_and_index(notes):
    note = notes.create("Groceries", "milk")
    renamed = notes.rename(note, "Shopping")
    assert renamed.name == "Shopping"
    assert _abs(notes, renamed).is_file()
    assert _abs(notes, renamed).read_text(encoding="utf-8") == "milk"
    assert (notes.vaults.store.vaults_dir / "Groceries.txt").exists() is False


def test_rename_rejects_collision(notes):
    notes.create("Alpha", "a")
    note = notes.create("Beta", "b")
    with pytest.raises(NoteError, match="already exists"):
        notes.rename(note, "alpha")


def test_delete_removes_file_and_index_entry(notes):
    note = notes.create("Temp", "temporary")
    notes.delete(note)
    assert _abs(notes, note).exists() is False
    assert notes.list() == []


def test_locked_vault_blocks_operations(store):
    service = VaultService(store)
    service.create("Secure", password="secret")
    service.set_current("Secure")
    notes = NoteService(service)

    with pytest.raises(NoteError, match="locked"):
        notes.create("X", "y")
    with pytest.raises(NoteError, match="locked"):
        notes.list()
