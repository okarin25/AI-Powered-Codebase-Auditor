import asyncio
import json
import logging
import os
import sys

from app.core.config import get_settings
from app.models.schemas import FileIssue

logger = logging.getLogger(__name__)


async def analyze_security(file_path: str, repo_root: str) -> list[FileIssue]:
    """Runs bandit asynchronously on a single file, with a hard timeout."""
    issues: list[FileIssue] = []
    rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/")

    if not os.path.exists(file_path):
        logger.error("Path does not exist: %s", file_path)
        return issues

    settings = get_settings()
    cmd = ["-m", "bandit", "-f", "json", "-q", file_path]

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
        logger.warning("Bandit timed out on %s after %ss", rel_path, settings.subprocess_timeout_seconds)
        return [
            FileIssue(
                file=rel_path,
                line=None,
                tool="bandit",
                severity="low",
                message=f"Security scan timed out after {settings.subprocess_timeout_seconds}s and was skipped.",
            )
        ]

    stdout = stdout_bytes.decode("utf-8", errors="ignore").strip()
    if not stdout:
        return issues

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        logger.warning("Bandit stdout was not valid JSON for %s.", rel_path)
        return issues

    for item in data.get("results", []):
        bandit_sev = item.get("issue_severity", "LOW").lower()
        severity = bandit_sev if bandit_sev in ("low", "medium", "high") else "low"

        issues.append(
            FileIssue(
                file=os.path.relpath(item.get("filename", file_path), repo_root).replace("\\", "/"),
                line=item.get("line_number"),
                tool="bandit",
                severity=severity,
                message=f"[{item.get('test_id')}] {item.get('issue_text')} (Confidence: {item.get('issue_confidence')})",
            )
        )

    return issues