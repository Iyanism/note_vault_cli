"""Persistence layer for the vault index file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from note_vault.models import Vault

INDEX_FILENAME = "vault_index.json"


def get_vaults_dir() -> Path:
    """Resolve the vaults directory (env override or project root)."""
    override = os.environ.get("NOTE_VAULT_DIR")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2] / "vaults"


def clean_rel_path(value: str) -> str:
    """Normalize a stored path to a posix path relative to the vaults dir.

    Handles the legacy Windows-style backslashes and the old ``vaults/``
    prefix written by the original single-file implementation.
    """
    value = value.replace("\\", "/")
    if value.startswith("vaults/"):
        value = value[len("vaults/") :]
    return value.strip("/")


class Store:
    """Reads and writes the JSON index tracking vaults and notes."""

    def __init__(self, vaults_dir: str | Path | None = None) -> None:
        self.vaults_dir = Path(vaults_dir or get_vaults_dir()).resolve()
        self.index_path = self.vaults_dir / INDEX_FILENAME
        self.current_vault: str | None = None

    def ensure_dir(self) -> None:
        self.vaults_dir.mkdir(parents=True, exist_ok=True)

    def _read_raw(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"vaults": []}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def load(self) -> list[Vault]:
        """Load vaults from the index, migrating older index formats."""
        self.ensure_dir()
        raw = self._read_raw()
        self.current_vault = raw.get("current_vault") or None
        return [Vault.from_dict(self._migrate_entry(entry)) for entry in raw.get("vaults", [])]

    @staticmethod
    def _migrate_entry(entry: dict[str, Any]) -> dict[str, Any]:
        entry["path"] = clean_rel_path(str(entry.get("path", "")))
        for note in entry.get("notes", []):
            note["path"] = clean_rel_path(str(note.get("path", "")))
        entry.setdefault("locked", False)
        entry.setdefault("password_hash", None)
        entry.setdefault("salt", None)
        entry.setdefault("notes", [])
        return entry

    def save(self, vaults: list[Vault]) -> None:
        """Persist the vault list and the current vault name."""
        self.ensure_dir()
        data = {
            "vaults": [v.to_dict() for v in vaults],
            "current_vault": self.current_vault,
        }
        self.index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
