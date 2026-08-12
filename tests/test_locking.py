"""Tests for per-vault password locking and session state."""

from __future__ import annotations

import pytest

from note_vault.vaults import VaultError, VaultService, hash_password, verify_password


@pytest.fixture
def secure(store):
    service = VaultService(store)
    service.create("Secure", password="hunter2")
    return service


def test_hash_round_trip():
    salt = b"fixed-salt-bytes"
    digest = hash_password("hunter2", salt)
    assert verify_password("hunter2", salt, digest) is True
    assert verify_password("wrong", salt, digest) is False


def test_hash_is_salted():
    assert hash_password("secret", b"aaaaaaaaaaaaaaaa") != hash_password(
        "secret", b"bbbbbbbbbbbbbbbb"
    )


def test_create_with_password_locks_vault(store):
    service = VaultService(store)
    vault = service.create("Secure", password="hunter2")
    assert vault.locked is True
    assert vault.has_password is True
    assert vault.password_hash is not None
    assert vault.salt is not None


def test_create_without_password_is_unlocked(store):
    service = VaultService(store)
    vault = service.create("Open")
    assert vault.locked is False
    assert vault.has_password is False


def test_unlock_with_wrong_password_fails(secure):
    assert secure.unlock("Secure", "wrong") is False
    assert secure.accessible(secure.get("Secure")) is False


def test_unlock_with_correct_password_succeeds(secure):
    assert secure.unlock("Secure", "hunter2") is True
    assert secure.accessible(secure.get("Secure")) is True


def test_unlock_is_session_scoped(secure):
    vault = secure.get("Secure")
    assert secure.unlock("Secure", "hunter2") is True
    secure.session.lock(vault)
    assert secure.accessible(vault) is False


def test_lock_sets_password_when_missing(store):
    service = VaultService(store)
    service.create("Open")
    service.lock("Open", password="newpass")
    vault = service.get("Open")
    assert vault.locked is True
    assert vault.has_password is True


def test_lock_requires_password_when_missing(store):
    service = VaultService(store)
    service.create("Open")
    with pytest.raises(VaultError, match="password"):
        service.lock("Open")


def test_lock_existing_password_does_not_change_it(secure):
    vault = secure.get("Secure")
    original = vault.password_hash
    secure.lock("Secure")
    assert vault.password_hash == original
    assert secure.unlock("Secure", "hunter2") is True


def test_unlock_unknown_vault_raises(secure):
    with pytest.raises(VaultError, match="does not exist"):
        secure.unlock("missing", "x")


def test_password_never_stored_in_plaintext(secure):
    import json
    from pathlib import Path

    raw = json.loads(Path(secure.store.index_path).read_text(encoding="utf-8"))
    vault_data = next(v for v in raw["vaults"] if v["name"] == "Secure")
    assert "hunter2" not in json.dumps(vault_data)
    assert vault_data["password_hash"]
    assert vault_data["salt"]
