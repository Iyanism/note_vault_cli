"""Tests for vault CRUD operations."""

from __future__ import annotations

import pytest

from note_vault.models import InvalidNameError
from note_vault.vaults import VaultError


def test_create_vault_makes_directory(service):
    vault = service.create("Work")
    assert (service.store.vaults_dir / vault.path).is_dir()
    assert vault in service.vaults


def test_create_sets_current_when_none_set(service):
    vault = service.create("Work")
    assert service.store.current_vault == vault.name


def test_create_does_not_override_existing_current(service):
    service.create("One")
    service.create("Two")
    assert service.store.current_vault == "One"


def test_create_rejects_duplicate_case_insensitive(service):
    service.create("Work")
    with pytest.raises(VaultError, match="already exists"):
        service.create("work")


def test_create_rejects_invalid_name(service):
    for bad in ["", ".", "..", "../evil", "a/b"]:
        with pytest.raises(InvalidNameError):
            service.create(bad)


def test_get_is_case_insensitive(service):
    service.create("Work")
    assert service.get("WORK") is not None
    assert service.get("missing") is None


def test_list_returns_all(service):
    service.create("One")
    service.create("Two")
    assert [v.name for v in service.list()] == ["One", "Two"]


def test_set_current(service):
    service.create("One")
    service.create("Two")
    assert service.set_current("two") is True
    assert service.current_vault.name == "Two"


def test_set_current_unknown_returns_false(service):
    assert service.set_current("missing") is False


def test_rename_updates_dir_and_current(service):
    service.create("Work")
    service.set_current("Work")
    renamed = service.rename("Work", "Projects")
    assert renamed.name == "Projects"
    assert (service.store.vaults_dir / "Work").exists() is False
    assert (service.store.vaults_dir / "Projects").is_dir()
    assert service.current_vault.name == "Projects"


def test_rename_rejects_collision(service):
    service.create("One")
    service.create("Two")
    with pytest.raises(VaultError, match="already exists"):
        service.rename("One", "two")


def test_rename_missing_raises(service):
    with pytest.raises(VaultError, match="does not exist"):
        service.rename("missing", "renamed")


def test_delete_removes_directory(service):
    vault = service.create("Work")
    service.delete("Work")
    assert (service.store.vaults_dir / vault.path).exists() is False
    assert service.get("Work") is None


def test_delete_clears_current(service):
    service.create("Work")
    service.set_current("Work")
    service.delete("Work")
    assert service.current_vault is None


def test_delete_missing_raises(service):
    with pytest.raises(VaultError, match="does not exist"):
        service.delete("missing")
