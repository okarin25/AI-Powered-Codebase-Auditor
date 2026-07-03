import asyncio
import json
import logging
import os
import sys

from app.core.config import get_settings
from app.models.schemas import FileIssue

logger = logging.getLogger(__name__)


async def analyze_lint(file_path: str, repo_root: str) -> list[FileIssue]:
    """Runs pylint asynchronously on a single file, with a hard timeout."""
    issues: list[FileIssue] = []
    rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/")

    if not os.path.exists(file_path):
        logger.error("Path does not exist: %s", file_path)
        return issues

    settings = get_settings()
    cmd = [
        "-m", "pylint",
        "--output-format=json",
        "--score=no",
        "--reports=no",
        "--disable=import-error,no-name-in-module",  # suppress env-pollution false positives
        file_path,
    ]

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, _ = await asyncio.wait_for(
            process.communicate(), timeout=settings.subprocess_timeout_seconds
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        logger.warning("Pylint timed out on %s after %ss", rel_path, settings.subprocess_timeout_seconds)
        return [
            FileIssue(
                file=rel_path,
                line=None,
                tool="pylint",
                severity="low",
                message=f"Lint check timed out after {settings.subprocess_timeout_seconds}s and was skipped.",
            )
        ]

    stdout = stdout_bytes.decode("utf-8", errors="ignore").strip()
    if not stdout:
        return issues

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        logger.warning("Pylint stdout was not valid JSON for %s. Output parsing skipped.", rel_path)
        return issues

    for item in data:
        pylint_type = item.get("type", "warning").lower()
        if pylint_type in ("fatal", "error"):
            severity = "high"
        elif pylint_type == "warning":
            severity = "medium"
        else:
            severity = "low"

        issues.append(
            FileIssue(
                file=os.path.relpath(item.get("path", file_path), repo_root).replace("\\", "/"),
                line=item.get("line"),
                tool="pylint",
                severity=severity,
                message=f"[{item.get('message-id', '')}:{item.get('symbol', '')}] {item.get('message', '')}",
            )
        )

    return issues