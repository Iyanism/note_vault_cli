"""Data models for vaults and notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class InvalidNameError(ValueError):
    """Raised when a vault or note name is invalid."""


def sanitize_name(name: str) -> str:
    """Validate and normalize a vault/note name (blocks path traversal)."""
    cleaned = name.strip().strip("/\\").strip()
    if cleaned in {"", ".", ".."}:
        raise InvalidNameError("Name cannot be empty, '.', or '..'")
    if "/" in cleaned or "\\" in cleaned:
        raise InvalidNameError("Name cannot contain path separators")
    return cleaned


@dataclass
class Note:
    """A single note stored as a text file."""

    name: str
    path: Path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Note:
        return cls(name=data["name"], path=Path(data["path"]))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "path": str(self.path)}


@dataclass
class Vault:
    """A collection of notes, optionally protected by a password."""

    name: str
    path: Path
    notes: list[Note] = field(default_factory=list)
    locked: bool = False
    password_hash: str | None = None
    salt: str | None = None

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None and self.salt is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vault:
        return cls(
            name=data["name"],
            path=Path(data["path"]),
            notes=[Note.from_dict(n) for n in data.get("notes", [])],
            locked=bool(data.get("locked", False)),
            password_hash=data.get("password_hash"),
            salt=data.get("salt"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "notes": [n.to_dict() for n in self.notes],
            "locked": self.locked,
            "password_hash": self.password_hash,
            "salt": self.salt,
        }
