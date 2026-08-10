# Note Vault CLI

A secure, terminal-based note manager with structured **vaults**, optional **per-vault password locking**, and full-text **search** — accessible directly from your command line.

---

## Features

- **Vaults:** create, open, rename, delete, and list vaults to organize your notes.
- **Per-vault locking:** optionally protect a vault with a password (salted `scrypt` hash). Locked vaults cannot be opened or read until unlocked.
- **Note management:** create, view, append, replace, rename, and delete notes inside the current vault.
- **Full-text search:** find notes by title or content across the current vault.
- **Persistent indexing:** all vaults and notes are tracked in `vaults/vault_index.json`.
- **Cross-platform:** works on Linux, macOS, and Windows.
- **Interactive UI:** built with `rich` and `InquirerPy` (arrow-key menus, colored tables).

---

## Getting Started

### Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (project manager — no pip needed)

### Setup

```bash
git clone https://github.com/pradeep-chetri/note-vault-cli.git
cd note-vault-cli
uv sync
```

### Run

```bash
uv run note-vault
```

or from a shell after installation:

```bash
uv tool install .
note-vault
```

### Tests & linting

```bash
uv run pytest          # run the test suite
uv run ruff check .    # lint
uv run ruff format .   # format
```

---

## Project Structure

```
note-vault-cli/
├── src/note_vault/        # application source
│   ├── cli.py             # entry point + menu wiring
│   ├── models.py          # Vault / Note dataclasses
│   ├── storage.py         # index persistence + migration
│   ├── vaults.py          # vault CRUD + password locking
│   ├── notes.py           # note CRUD + search
│   └── ui.py              # rich/inquirer helpers
├── tests/                 # pytest suite
├── vaults/                # user data (gitignored)
└── pyproject.toml
```

The data directory defaults to `./vaults` and can be overridden with the `NOTE_VAULT_DIR` environment variable.

---

## Roadmap

- File-level encryption (encrypt note contents with a key derived from the vault password).
- Text-based user interface (TUI) with a dedicated terminal app.
- Vault backup / export to Markdown or ZIP.
