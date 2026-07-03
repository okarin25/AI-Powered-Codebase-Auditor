import logging
import os
import subprocess
from typing import List

from app.core.config import get_settings

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__",
    ".pytest_cache", ".idea", ".vscode", "dist", "build",
    "egg-info", "site-packages",
}

IGNORE_EXTS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif",
    ".ico", ".svg", ".pdf", ".zip", ".tar", ".gz", ".woff",
    ".woff2", ".ttf", ".eot",
}


def get_dir_size_mb(directory: str) -> float:
    """Calculates total directory size in Megabytes."""
    total_size = 0
    for root, _dirs, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)


def clone_repo(repo_url: str, dest_dir: str) -> str:
    """
    Clones a public Git repository into dest_dir with a shallow depth=1 clone.

    Uses subprocess directly (not GitPython's clone_from) because GitPython's
    kill_after_timeout relies on a Unix-only process-killing mechanism and
    raises on Windows. subprocess.run's `timeout` argument works identically
    on every platform.

    Safety measures:
    - GIT_TERMINAL_PROMPT=0 so a private or invalid repo fails fast instead
      of hanging forever waiting for a username/password prompt.
    - `timeout=` hard-kills the git process if cloning takes too long
      (huge repo, slow network, stalled connection).
    - Post-clone size check rejects oversized repos before analysis proceeds.
    """
    settings = get_settings()
    logger.info("Cloning repo %s to %s...", repo_url, dest_dir)

    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--", repo_url, dest_dir],
            env=env,
            timeout=settings.clone_timeout_seconds,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("Clone of %s timed out after %ss", repo_url, settings.clone_timeout_seconds)
        raise ValueError(
            f"Cloning timed out after {settings.clone_timeout_seconds}s. "
            "The repository may be too large or the connection too slow."
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        logger.error("git clone failed for %s: %s", repo_url, stderr)
        raise ValueError(f"Failed to clone repository: {stderr or 'unknown git error'}")

    actual_size = get_dir_size_mb(dest_dir)
    if actual_size > settings.max_repo_size_mb:
        raise ValueError(
            f"Repository size ({actual_size:.1f}MB) exceeds the "
            f"{settings.max_repo_size_mb}MB limit for this service."
        )

    logger.info("Clone complete (%.1fMB).", actual_size)
    return dest_dir


def list_files(directory: str) -> List[str]:
    """Recursively list all files in directory, ignoring common non-source directories."""
    file_list = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTS:
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, directory)
            file_list.append(rel_path.replace("\\", "/"))
    return file_list


def get_repo_structure(directory: str) -> str:
    """Returns a tree-like string structure of the repository."""
    lines: List[str] = []

    def _walk(curr_dir: str, prefix: str = "") -> None:
        try:
            entries = sorted(os.listdir(curr_dir))
        except OSError:
            return
        entries = [e for e in entries if e not in IGNORE_DIRS]
        for i, entry in enumerate(entries):
            entry_path = os.path.join(curr_dir, entry)
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if os.path.isfile(entry_path):
                ext = os.path.splitext(entry)[1].lower()
                if ext in IGNORE_EXTS:
                    continue
                lines.append(f"{prefix}{connector}{entry}")
            else:
                lines.append(f"{prefix}{connector}{entry}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                _walk(entry_path, new_prefix)

    _walk(directory)
    return "\n".join(lines)