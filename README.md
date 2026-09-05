# Note Vault CLI

A secure, terminal-based note manager and developer knowledge vault with structured **vaults**, optional **per-vault password locking**, full-text **search**, scriptable **CLI subcommands**, and external **$EDITOR** integration.

---

## Features

- **Dual Mode Interface:** Run interactively with TUI menus (`rich` + `InquirerPy`) or run non-interactively via CLI subcommands (`typer`).
- **External $EDITOR Integration:** Automatically open `$VISUAL`, `$EDITOR`, `nano`, or `vim` for seamless note creation and editing.
- **POSIX Scriptability & Piping:** Read content directly from `stdin` (`cat file.txt | note-vault note add ...`), output raw text to `stdout`, and export structured JSON (`--json`).
- **Vaults:** Create, open, rename, delete, select, and list vaults to organize developer snippets and notes.
- **Per-Vault Password Locking:** Optionally protect vaults with password-derived `scrypt` salted hashes.
- **Note Management:** Create, view, edit, append, replace, rename, and delete notes.
- **Full-Text Search:** Find notes by title or content with context snippets.
- **Cross-Platform:** Runs on Linux, macOS, and Windows.

---

## Getting Started

### Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (project manager)

### Setup

```bash
git clone https://github.com/pradeep-chetri/note-vault-cli.git
cd note-vault-cli
uv sync
```

### Usage

#### Interactive Mode (TUI)
Launch the interactive arrow-key menu by running without arguments:
```bash
uv run note-vault
```

#### Non-Interactive CLI Subcommands
```bash
# Add a note using inline content or $EDITOR
uv run note-vault note add "docker-tips" -c "docker system prune -a"

# Read note content from stdin
cat logs.txt | uv run note-vault note add "trace-log"

# Output raw note text to stdout (suitable for piping or xclip/pbcopy)
uv run note-vault note cat "docker-tips"

# Edit note in $EDITOR
uv run note-vault note edit "docker-tips"

# Search notes and format as JSON
uv run note-vault search "docker" --json

# List vaults or notes in JSON format
uv run note-vault note list --json
uv run note-vault vault list --json
```

### Tests & Linting

```bash
uv run pytest          # run the test suite
uv run ruff check .    # lint
uv run ruff format .   # format
```

---

## CLI Reference

| Command | Description |
| :--- | :--- |
| `note-vault` | Launch interactive menu (when called without arguments) |
| `note-vault note add <title> [-c content \| -f file]` | Create a note (uses stdin / `$EDITOR` if content omitted) |
| `note-vault note cat <title>` | Output raw note content to stdout |
| `note-vault note edit <title>` | Open existing note in `$EDITOR` |
| `note-vault note list [--json]` | List notes in current/target vault |
| `note-vault note delete <title> [-f]` | Delete a note |
| `note-vault vault list [--json]` | List all vaults and lock status |
| `note-vault vault create <name> [-p pass]` | Create a new vault |
| `note-vault vault use <name>` | Select active default vault |
| `note-vault vault lock [name]` | Lock specified or active vault |
| `note-vault search <query> [--json]` | Search notes by title or content |

---

## Security Notes

- Passwords are hashed with **scrypt** using a random 16-byte salt; plaintext passwords are never written to disk.
- Unlocking is **session-scoped**: restarting the application re-locks password-protected vaults.

---

## Project Structure

```
note-vault-cli/
├── src/note_vault/        # application source
│   ├── cli.py             # entry point + menu routing
│   ├── cli_commands.py    # typer non-interactive CLI subcommands
│   ├── editor.py          # external editor ($EDITOR/nano/vim) launcher
│   ├── models.py          # Vault / Note models + name sanitization
│   ├── storage.py         # index persistence + legacy migration
│   ├── vaults.py          # vault CRUD + password locking
│   ├── notes.py           # note CRUD + search
│   └── ui.py              # rich/inquirer UI helpers
├── tests/                 # pytest suite
├── vaults/                # user data (gitignored)
└── pyproject.toml
```

---

## Evolution Roadmap

- [x] **Phase 1: Scriptable CLI & POSIX Support**
  - Non-interactive Typer subcommands, `$EDITOR` support, `stdin`/`stdout` piping, `--json` formatting.
- [ ] **Phase 2: Developer Knowledge Base & Markdown (`.md`) Format**
  - YAML frontmatter (`tags`, `language`, `created_at`), syntax highlighting with `Pygments` / `Rich`, quick code block extraction.
- [ ] **Phase 3: At-Rest Cryptographic Encryption**
  - AES-256-GCM / XChaCha20-Poly1305 per-note encryption derived from vault passphrases + OS Keyring integration.
- [ ] **Phase 4: Advanced Search & Knowledge Graph**
  - Fuzzy search (`fzf` / `rapidfuzz`), tag filtering (`--tag`), and `[[Wiki-links]]` with backlinks graph.
- [ ] **Phase 5: Git Versioning & MCP Server**
  - Automatic micro-commits per vault mutation, export/import tools, and Model Context Protocol (MCP) server (`note-vault mcp serve`) for AI coding assistant integration.
