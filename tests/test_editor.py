"""Tests for external editor helper module."""

import os
from unittest.mock import patch

from note_vault.editor import edit_text, get_default_editor


def test_get_default_editor_env_visual():
    with patch.dict(os.environ, {"VISUAL": "nvim", "EDITOR": "vim"}):
        assert get_default_editor() == "nvim"


def test_get_default_editor_env_editor():
    with patch.dict(os.environ, {"VISUAL": "", "EDITOR": "emacs"}):
        assert get_default_editor() == "emacs"


def test_get_default_editor_fallback(monkeypatch):
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    editor = get_default_editor()
    assert editor in ("nano", "vim", "vi")


def test_edit_text_mocked(monkeypatch):
    # Mock subprocess.run to modify the temp file directly
    def mock_run(cmd, check=False):
        filepath = cmd[-1]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("Edited via mock editor")

        class DummyCompletedProcess:
            returncode = 0

        return DummyCompletedProcess()

    monkeypatch.setattr("subprocess.run", mock_run)
    result = edit_text("Initial text")
    assert result == "Edited via mock editor"
