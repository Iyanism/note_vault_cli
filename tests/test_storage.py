"""Tests for index persistence and legacy-format migration."""

from __future__ import annotations

import json

from note_vault.storage import Store, clean_rel_path


def test_load_returns_empty_when_no_index(tmp_path):
    store = Store(tmp_path / "vaults")
    assert store.load() == []
    assert store.current_vault is None


def test_load_creates_vaults_dir(tmp_path):
    store = Store(tmp_path / "vaults")
    store.load()
    assert (tmp_path / "vaults").is_dir()


def test_save_and_load_round_trip(tmp_path, service):
    vault = service.create("Work")
    service.set_current("Work")

    reloaded = Store(tmp_path / "vaults")
    vaults = reloaded.load()
    assert [v.name for v in vaults] == ["Work"]
    assert reloaded.current_vault == "Work"
    assert vaults[0].path == vault.path


def test_migrates_legacy_index_format(tmp_path):
    vaults_dir = tmp_path / "vaults"
    vaults_dir.mkdir()
    legacy = {
        "vaults": [
            {
                "name": "Hello",
                "path": "vaults\\Hello",
                "notes": [{"name": "Hello", "path": "vaults\\Hello\\Hello.txt"}],
            }
        ],
        "current_vault": "Hello",
    }
    (vaults_dir / "vault_index.json").write_text(json.dumps(legacy))

    store = Store(vaults_dir)
    vaults = store.load()

    assert len(vaults) == 1
    vault = vaults[0]
    assert vault.path.as_posix() == "Hello"
    assert vault.notes[0].path.as_posix() == "Hello/Hello.txt"
    assert vault.locked is False
    assert vault.password_hash is None
    assert vault.salt is None
    assert store.current_vault == "Hello"


def test_clean_rel_path_normalizes_windows_separators():
    assert clean_rel_path("Hello\\Notes\\A.txt") == "Hello/Notes/A.txt"
    assert clean_rel_path("vaults\\Hello\\A.txt") == "Hello/A.txt"
    assert clean_rel_path("Hello") == "Hello"


def test_current_vault_persisted(service, tmp_path):
    service.create("One")
    service.create("Two")
    service.set_current("Two")

    raw = json.loads((tmp_path / "vaults" / "vault_index.json").read_text())
    assert raw["current_vault"] == "Two"


def test_index_is_written_with_indent(tmp_path, service):
    service.create("Work")
    raw = (tmp_path / "vaults" / "vault_index.json").read_text()
    assert "\n  " in raw
