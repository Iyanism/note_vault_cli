"""Headless integration tests driving app handlers with patched UI prompts."""

from __future__ import annotations

import pytest

from note_vault import cli, ui
from note_vault.notes import NoteError
from note_vault.storage import Store


@pytest.fixture
def app(monkeypatch, tmp_path):
    from note_vault.vaults import VaultService

    store = Store(tmp_path / "vaults")
    monkeypatch.setattr(cli, "VaultService", lambda: VaultService(store))
    return cli.NoteVaultApp()


def test_full_note_lifecycle(app, monkeypatch):
    monkeypatch.setattr(ui, "prompt_confirm", lambda message, default=True: False)
    monkeypatch.setattr(ui, "prompt_secret", lambda message: "irrelevant")

    texts = iter(["Work", "Groceries", "Shopping", "milk eggs"])
    monkeypatch.setattr(ui, "prompt_text", lambda message, default=None: next(texts))
    monkeypatch.setattr(ui, "prompt_content", lambda message: next(texts))

    app._new_vault()
    assert app.current.name == "Work"

    app._new_note()
    assert [n.name for n in app.notes.list()] == ["Groceries"]

    note = app.notes.list()[0]
    app.notes.rename(note, "Shopping")
    assert [n.name for n in app.notes.list()] == ["Shopping"]

    def select_with(action):
        def _select(message, choices):
            if message == "Select a note:":
                return choices[0]["value"]
            return action

        return _select

    monkeypatch.setattr(ui, "prompt_select", select_with("back"))
    app._open_note()
    assert [n.name for n in app.notes.list()] == ["Shopping"]

    monkeypatch.setattr(ui, "prompt_select", select_with("delete"))
    monkeypatch.setattr(ui, "prompt_confirm", lambda message, default=True: True)
    app._open_note()
    assert app.notes.list() == []


def test_new_vault_with_password_locks_it(app, monkeypatch):
    monkeypatch.setattr(ui, "prompt_text", lambda message, default=None: "Secure")
    monkeypatch.setattr(ui, "prompt_confirm", lambda message, default=True: True)
    monkeypatch.setattr(ui, "prompt_secret", lambda message: "hunter2")

    app._new_vault()
    assert app.current.name == "Secure"
    assert app.current.locked is True


def test_open_note_requires_unlock(app, monkeypatch):
    monkeypatch.setattr(ui, "prompt_text", lambda message, default=None: "Secure")
    monkeypatch.setattr(ui, "prompt_confirm", lambda message, default=True: True)
    monkeypatch.setattr(ui, "prompt_secret", lambda message: "hunter2")
    app._new_vault()

    monkeypatch.setattr(ui, "prompt_secret", lambda message: "wrong")
    with pytest.raises(NoteError, match="Incorrect password"):
        app._open_note()

    monkeypatch.setattr(ui, "prompt_secret", lambda message: "hunter2")
    monkeypatch.setattr(ui, "prompt_select", lambda message, choices: "back")
    app._open_note()


def test_new_note_requires_current_vault(app, monkeypatch):
    monkeypatch.setattr(ui, "prompt_text", lambda message, default=None: "Any")
    monkeypatch.setattr(ui, "prompt_content", lambda message: "body")
    with pytest.raises(NoteError, match="No vault is open"):
        app._new_note()
