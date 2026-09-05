"""Helper to open external text editors ($VISUAL, $EDITOR, nano, vim)."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path


class EditorError(Exception):
    """Raised when the editor fails or cannot be executed."""


def get_default_editor() -> str:
    """Resolve default editor from environment or fallback executables."""
    for var in ("VISUAL", "EDITOR"):
        val = os.environ.get(var)
        if val and val.strip():
            return val.strip()

    for binary in ("nano", "vim", "vi"):
        if shutil.which(binary):
            return binary

    return "nano"


def edit_text(initial_content: str = "", suffix: str = ".txt") -> str:
    """Open initial_content in an external editor and return the updated text."""
    editor = get_default_editor()

    with tempfile.NamedTemporaryFile("w+", suffix=suffix, delete=False, encoding="utf-8") as temp:
        temp.write(initial_content)
        temp_path = Path(temp.name)

    try:
        cmd = shlex.split(editor) + [str(temp_path)]
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            raise EditorError(f"Editor command '{editor}' exited with code {res.returncode}")
        return temp_path.read_text(encoding="utf-8")
    finally:
        if temp_path.exists():
            temp_path.unlink()
