"""Tests for Typer CLI subcommands."""

import json

from typer.testing import CliRunner

from note_vault.cli_commands import app

runner = CliRunner()


def test_vault_commands_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))

    # 1. Create vault
    res = runner.invoke(app, ["vault", "create", "dev"])
    assert res.exit_code == 0
    assert "Vault 'dev' created" in res.stdout

    # 2. List vaults
    res = runner.invoke(app, ["vault", "list"])
    assert res.exit_code == 0
    assert "dev" in res.stdout

    # 3. List vaults JSON
    res = runner.invoke(app, ["vault", "list", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert len(data) == 1
    assert data[0]["name"] == "dev"


def test_note_add_and_cat(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))
    runner.invoke(app, ["vault", "create", "work"])

    # Add inline note
    res = runner.invoke(app, ["note", "add", "api-keys", "-c", "SECRET_KEY=12345"])
    assert res.exit_code == 0
    assert "Note 'api-keys' saved" in res.stdout

    # Cat note content
    res = runner.invoke(app, ["note", "cat", "api-keys"])
    assert res.exit_code == 0
    assert res.stdout.strip() == "SECRET_KEY=12345"


def test_note_add_from_file(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))
    runner.invoke(app, ["vault", "create", "docs"])

    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("Hello from file!", encoding="utf-8")

    res = runner.invoke(app, ["note", "add", "imported", "-f", str(sample_file)])
    assert res.exit_code == 0
    assert "Note 'imported' saved" in res.stdout

    res = runner.invoke(app, ["note", "cat", "imported"])
    assert res.exit_code == 0
    assert res.stdout.strip() == "Hello from file!"


def test_note_list_json(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))
    runner.invoke(app, ["vault", "create", "testvault"])
    runner.invoke(app, ["note", "add", "n1", "-c", "content 1"])
    runner.invoke(app, ["note", "add", "n2", "-c", "content 2"])

    res = runner.invoke(app, ["note", "list", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert len(data) == 2
    names = {n["name"] for n in data}
    assert names == {"n1", "n2"}


def test_search_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))
    runner.invoke(app, ["vault", "create", "searchvault"])
    runner.invoke(app, ["note", "add", "python-tips", "-c", "asyncio queue example"])
    runner.invoke(app, ["note", "add", "rust-tips", "-c", "tokio channel example"])

    res = runner.invoke(app, ["search", "asyncio", "--json"])
    assert res.exit_code == 0
    results = json.loads(res.stdout)
    assert len(results) == 1
    assert results[0]["name"] == "python-tips"


def test_note_delete_force(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTE_VAULT_DIR", str(tmp_path))
    runner.invoke(app, ["vault", "create", "delvault"])
    runner.invoke(app, ["note", "add", "tempnote", "-c", "delete me"])

    res = runner.invoke(app, ["note", "delete", "tempnote", "--force"])
    assert res.exit_code == 0
    assert "deleted" in res.stdout

    res = runner.invoke(app, ["note", "list", "--json"])
    assert json.loads(res.stdout) == []
