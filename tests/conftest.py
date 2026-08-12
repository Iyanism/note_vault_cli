"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from note_vault.storage import Store


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "vaults")


@pytest.fixture
def service(store):
    from note_vault.vaults import VaultService

    return VaultService(store)
