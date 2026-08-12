"""Tests for full-text search across notes."""

from __future__ import annotations

import pytest

from note_vault.notes import NoteService
from note_vault.vaults import VaultService


@pytest.fixture
def notes(store):
    service = VaultService(store)
    service.create("Work")
    service.set_current("Work")
    return NoteService(service)


def test_search_by_title(notes):
    notes.create("Groceries", "milk")
    assert [n.name for n in notes.search("GROCER")] == ["Groceries"]


def test_search_by_content(notes):
    notes.create("Todo", "Finish the CLI project")
    matches = notes.search("CLI project")
    assert [n.name for n in matches] == ["Todo"]


def test_search_is_case_insensitive(notes):
    notes.create("Log", "Deploy the SERVER today")
    assert len(notes.search("server")) == 1
    assert len(notes.search("SERVER")) == 1


def test_search_empty_query_returns_empty(notes):
    notes.create("Log", "content")
    assert notes.search("   ") == []


def test_search_no_matches(notes):
    notes.create("Log", "content")
    assert notes.search("nonexistent") == []


def test_search_searches_all_notes(notes):
    notes.create("A", "hello world")
    notes.create("B", "goodbye world")
    assert len(notes.search("world")) == 2
    assert len(notes.search("hello")) == 1


def test_snippet_highlights_match_window(notes):
    note = notes.create("Log", "short " + "x" * 100 + " needle at the end")
    snippet = notes.snippet(note, "needle")
    assert "needle" in snippet
    assert len(snippet) <= 65


def test_snippet_without_match_returns_head(notes):
    note = notes.create("Log", "no keywords here")
    snippet = notes.snippet(note, "zzz")
    assert snippet == "no keywords here"
