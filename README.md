# Note Vault CLI

A secure, terminal-based note manager with structured **vaults**, optional **per-vault password locking**, and full-text **search** — accessible directly from your command line.

---

## Features

- **Vaults:** create, open, rename, delete, and list vaults to organize your notes.
- **Per-vault locking:** optionally protect a vault with a password (salted `scrypt` hash). Locked vaults cannot be opened or read until unlocked.
- **Note management:** create, view, append, replace, rename, and delete notes inside the current vault.
- **Full-text search:** find notes by title or content across the current vault, with context snippets.
- **Persistent indexing:** all vaults and notes are tracked in `vaults/vault_index.json`.
- **Cross-platform:** works on Linux, macOS, and Windows.
- **Interactive UI:** arrow-key menus, colored tables, and inline prompts powered by `rich` and `InquirerPy`.

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

or install it globally with uv and run it anywhere:

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

## Main menu

| Option          | What it does                                       |
| --------------- | -------------------------------------------------- |
| New Note        | Create a note in the current vault                 |
| Open Note       | Pick a note, then view / append / replace / rename / delete it |
| List Notes      | Show every note in the current vault               |
| Search Notes    | Find notes by title or content                     |
| New Vault       | Create a vault, optionally password-protected      |
| Open Vault      | Switch the current vault (unlock when passworded)  |
| List Vaults     | Show all vaults with their lock/current status     |
| Lock Vault      | Lock the current vault (sets a password on first use) |
| Unlock Vault    | Unlock the current vault for this session          |
| Rename Vault    | Rename a vault and its directory on disk           |
| Delete Vault    | Delete a vault and all of its notes                |
| Exit            | Quit                                              |

## Security notes

- Passwords are hashed with **scrypt** using a random 16-byte salt; the plaintext is never written to disk.
- Unlocking is **session-scoped**: restarting the app re-locks every password-protected vault.
- Note files themselves are stored as plain text on disk. File-level encryption is on the roadmap.

## Migrating from the legacy app

Existing data from the original single-file version is read automatically. Legacy `vault_index.json` files that used Windows-style paths and lacked lock metadata are migrated in place on first run.

---

## Project structure

```
note-vault-cli/
├── src/note_vault/        # application source
│   ├── cli.py             # entry point + menu wiring
│   ├── models.py          # Vault / Note models + name sanitization
│   ├── storage.py         # index persistence + legacy migration
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
