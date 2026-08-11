"""Vault management: CRUD, the current vault, and per-vault password locking."""

from __future__ import annotations

import hashlib
import hmac
import os
import shutil
from pathlib import Path

from note_vault.models import Vault, sanitize_name
from note_vault.storage import Store


class VaultError(Exception):
    """Raised for vault-related failures."""


def hash_password(password: str, salt: bytes) -> str:
    """Hash a password with scrypt and a random salt."""
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1).hex()


def verify_password(password: str, salt: bytes, expected_hash: str) -> bool:
    """Constant-time comparison of a password against a stored scrypt hash."""
    actual = hash_password(password, salt)
    return hmac.compare_digest(actual, expected_hash)


class Session:
    """Tracks which locked vaults have been unlocked in the current session.

    Unlocking is intentionally in-memory only: restarting the app re-locks
    every password-protected vault.
    """

    def __init__(self) -> None:
        self.unlocked: set[str] = set()

    def unlock(self, vault: Vault, password: str) -> bool:
        if not vault.has_password:
            return True
        assert vault.salt is not None and vault.password_hash is not None
        ok = verify_password(password, bytes.fromhex(vault.salt), vault.password_hash)
        if ok:
            self.unlocked.add(vault.name)
        return ok

    def lock(self, vault: Vault) -> None:
        self.unlocked.discard(vault.name)

    def is_accessible(self, vault: Vault) -> bool:
        return not vault.locked or vault.name in self.unlocked


class VaultService:
    """High-level operations over the vault index."""

    def __init__(self, store: Store | None = None, session: Session | None = None) -> None:
        self.store = store or Store()
        self.session = session or Session()
        self.vaults = self.store.load()

    def save(self) -> None:
        self.store.save(self.vaults)

    # --- current vault ---

    @property
    def current_vault(self) -> Vault | None:
        if not self.store.current_vault:
            return None
        return self.get(self.store.current_vault)

    def set_current(self, name: str) -> bool:
        vault = self.get(name)
        if vault is None:
            return False
        self.store.current_vault = vault.name
        self.save()
        return True

    # --- CRUD ---

    def create(self, name: str, password: str | None = None) -> Vault:
        name = sanitize_name(name)
        if self.get(name) is not None:
            raise VaultError(f"Vault '{name}' already exists")
        rel_path = Path(name)
        try:
            (self.store.vaults_dir / rel_path).mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise VaultError(f"Directory for vault '{name}' already exists") from exc
        salt = os.urandom(16)
        vault = Vault(
            name=name,
            path=rel_path,
            locked=bool(password),
            password_hash=hash_password(password, salt) if password else None,
            salt=salt.hex() if password else None,
        )
        self.vaults.append(vault)
        if self.store.current_vault is None:
            self.store.current_vault = name
        self.save()
        return vault

    def get(self, name: str) -> Vault | None:
        for vault in self.vaults:
            if vault.name.lower() == name.lower():
                return vault
        return None

    def list(self) -> list[Vault]:
        return list(self.vaults)

    def rename(self, old_name: str, new_name: str) -> Vault:
        new_name = sanitize_name(new_name)
        vault = self.get(old_name)
        if vault is None:
            raise VaultError(f"Vault '{old_name}' does not exist")
        if new_name.lower() != vault.name.lower() and self.get(new_name) is not None:
            raise VaultError(f"Vault '{new_name}' already exists")
        old_path = self.store.vaults_dir / vault.path
        new_path = self.store.vaults_dir / new_name
        old_path.rename(new_path)
        for note in vault.notes:
            note.path = Path(new_name) / note.path.name
        vault.name = new_name
        vault.path = Path(new_name)
        if self.store.current_vault == old_name:
            self.store.current_vault = new_name
        self.save()
        return vault

    def delete(self, name: str) -> Vault:
        vault = self.get(name)
        if vault is None:
            raise VaultError(f"Vault '{name}' does not exist")
        path = self.store.vaults_dir / vault.path
        if path.exists():
            shutil.rmtree(path)
        self.vaults = [v for v in self.vaults if v is not vault]
        if self.store.current_vault == vault.name:
            self.store.current_vault = None
        self.save()
        return vault

    # --- locking ---

    def lock(self, name: str, password: str | None = None) -> Vault:
        vault = self.get(name)
        if vault is None:
            raise VaultError(f"Vault '{name}' does not exist")
        if not vault.has_password:
            if not password:
                raise VaultError("Set a password to lock this vault")
            salt = os.urandom(16)
            vault.password_hash = hash_password(password, salt)
            vault.salt = salt.hex()
        vault.locked = True
        self.session.lock(vault)
        self.save()
        return vault

    def unlock(self, name: str, password: str) -> bool:
        vault = self.get(name)
        if vault is None:
            raise VaultError(f"Vault '{name}' does not exist")
        return self.session.unlock(vault, password)

    def accessible(self, vault: Vault) -> bool:
        return self.session.is_accessible(vault)
