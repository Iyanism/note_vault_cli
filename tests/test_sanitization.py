"""Tests for name sanitization (path-traversal protection)."""

from __future__ import annotations

import pytest

from note_vault.models import InvalidNameError, sanitize_name


def test_trims_whitespace_and_outer_slashes():
    assert sanitize_name("  Notes  ") == "Notes"
    assert sanitize_name("/Notes/") == "Notes"
    assert sanitize_name("\\Notes\\") == "Notes"


def test_rejects_empty_names():
    for bad in ["", "   ", ".", "..", "./", "../"]:
        with pytest.raises(InvalidNameError):
            sanitize_name(bad)


def test_rejects_path_separators():
    for bad in ["a/b", "a\\b", "folder/../x", "..\\x", "/etc/passwd"]:
        with pytest.raises(InvalidNameError):
            sanitize_name(bad)


def test_allows_normal_names():
    assert sanitize_name("Meeting Notes 2026") == "Meeting Notes 2026"
    assert sanitize_name("a.b.c") == "a.b.c"
