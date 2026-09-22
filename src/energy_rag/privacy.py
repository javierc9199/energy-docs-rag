"""Guards that keep private documents out of version control.

The vector index stores the full text of every chunk. If you index your own
company documents, the index *is* those documents, so writing it anywhere Git
would pick up is a leak waiting for the next `git add .`.

Before writing an index or reading from a private folder that lives inside a Git
working tree, the pipeline asks Git itself whether the path is ignored
(`git check-ignore`) and refuses if it is not. Outside a Git repository, or with
Git not installed, there is nothing to protect and the check passes.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class UnsafeLocationError(RuntimeError):
    """Raised when private material would be written to a path Git tracks."""


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def repo_root(path: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    probe = path if path.is_dir() else path.parent
    while not probe.exists():
        probe = probe.parent
    result = _git("rev-parse", "--show-toplevel", cwd=probe)
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def is_git_ignored(path: Path) -> bool:
    """True if Git would ignore `path` (checked with a probe file inside it for folders)."""
    root = repo_root(path)
    if root is None:
        return True  # not inside a repository: nothing can be committed
    probe = path / ".probe" if (path.is_dir() or not path.suffix) else path
    result = _git("check-ignore", "-q", str(probe), cwd=root)
    return result.returncode == 0


def assert_safe(path: Path, what: str) -> None:
    path = path.resolve()
    if not is_git_ignored(path):
        raise UnsafeLocationError(
            f"Refusing to use {path} for {what}: it is inside a Git repository and not "
            "ignored, so its contents could be committed. Move it outside the repository, "
            "put it under data/, or add it to .gitignore."
        )
    log.debug("%s at %s is git-ignored or outside a repository", what, path)
