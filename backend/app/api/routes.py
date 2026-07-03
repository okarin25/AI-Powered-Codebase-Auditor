import asyncio
import io
import logging
import os
import tempfile
import threading
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.agent.agent import run_audit_agent
from app.analysis.complexity import analyze_complexity
from app.analysis.lint import analyze_lint
from app.analysis.security import analyze_security
from app.core.config import get_settings
from app.core.security import verify_api_key
from app.ingestion.repo_loader import clone_repo, list_files
from app.models.schemas import AuditReport, AuditRequest, AuditResponse, StatusResponse

logger = logging.getLogger(__name__)
settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

# Every route in this router requires a valid X-API-Key header (unless
# API_KEY is unset in the environment, e.g. for local dev).
router = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])

# In-memory job store. Fine for a single-instance portfolio deployment;
# would need Redis/a DB to scale beyond one process.
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()


def _purge_expired_jobs() -> None:
    """Lazily sweep out jobs older than JOB_TTL_HOURS to bound memory growth."""
    ttl_seconds = settings.job_ttl_hours * 3600
    now = time.time()
    with jobs_lock:
        expired = [jid for jid, job in jobs.items() if now - job.get("created_at", now) > ttl_seconds]
        for jid in expired:
            del jobs[jid]
    if expired:
        logger.info("Purged %d expired job(s).", len(expired))


def _count_active_jobs() -> int:
    with jobs_lock:
        return sum(1 for job in jobs.values() if job["status"] in ("pending", "running"))


async def async_audit_pipeline(job_id: str, repo_url: str) -> None:
    """Core async pipeline: clone -> static analysis -> agent -> report."""
    logger.info("Starting audit pipeline for job %s on %s", job_id, repo_url)

    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = "Cloning repository..."

    temp_dir_obj = tempfile.TemporaryDirectory(prefix=f"audit_{job_id}_")
    temp_dir = temp_dir_obj.name

    try:
        await asyncio.to_thread(clone_repo, repo_url, temp_dir)

        with jobs_lock:
            jobs[job_id]["progress"] = "Scanning repository structure..."
        all_files = await asyncio.to_thread(list_files, temp_dir)

        python_files = [f for f in all_files if f.endswith(".py")]
        files_to_analyze = python_files[: settings.max_files_to_analyze]

        precompiled_issues: Dict[str, Any] = {}

        for i, file_rel in enumerate(files_to_analyze):
            abs_path = os.path.join(temp_dir, file_rel)

            with jobs_lock:
                jobs[job_id]["progress"] = (
                    f"Analyzing {file_rel} ({i + 1}/{len(files_to_analyze)})..."
                )

            radon_task = asyncio.to_thread(analyze_complexity, abs_path, temp_dir)
            bandit_task = analyze_security(abs_path, temp_dir)
            pylint_task = analyze_lint(abs_path, temp_dir)

            results = await asyncio.gather(radon_task, bandit_task, pylint_task)

            file_issues = [issue for issue_list in results for issue in issue_list]
            if file_issues:
                precompiled_issues[abs_path] = file_issues

        with jobs_lock:
            jobs[job_id]["progress"] = "Running audit agent..."

        report = await asyncio.to_thread(run_audit_agent, repo_url, temp_dir, precompiled_issues)

        with jobs_lock:
            jobs[job_id]["report"] = report
            jobs[job_id]["status"] = "done"
            jobs[job_id]["progress"] = "Audit completed successfully."
        logger.info("Job %s completed successfully.", job_id)

    except Exception as exc:  # noqa: BLE001 - top-level guard, must never crash the worker
        logger.error("Error executing audit for job %s: %s", job_id, exc, exc_info=True)
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
            jobs[job_id]["progress"] = "Audit failed."
    finally:
        try:
            await asyncio.to_thread(temp_dir_obj.cleanup)
        except Exception as cleanup_err:  # noqa: BLE001
            logger.warning("Failed to clean up temp dir %s: %s", temp_dir, cleanup_err)


def execute_audit_pipeline(job_id: str, repo_url: str) -> None:
    """Sync wrapper for FastAPI BackgroundTasks; runs its own event loop in a worker thread."""
    asyncio.run(async_audit_pipeline(job_id, repo_url))


@router.post("/audit", response_model=AuditResponse)
@limiter.limit(settings.rate_limit_audit)
def audit_repository(request: Request, body: AuditRequest, background_tasks: BackgroundTasks):
    _purge_expired_jobs()

    if _count_active_jobs() >= settings.max_concurrent_jobs:
        raise HTTPException(
            status_code=429,
            detail="Server is busy processing other audits. Please try again shortly.",
        )

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {
            "status": "pending",
            "progress": "Queued...",
            "report": None,
            "error": None,
            "created_at": time.time(),
        }

    # body.repo_url is already validated/normalized by AuditRequest's field_validator.
    background_tasks.add_task(execute_audit_pipeline, job_id, body.repo_url)
    return AuditResponse(job_id=job_id, status="pending")


@router.get("/audit/{job_id}/status", response_model=StatusResponse)
def get_audit_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Audit job not found.")
        return StatusResponse(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            error=job["error"],
        )


@router.get("/audit/{job_id}/report", response_model=AuditReport)
def get_audit_report(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Audit job not found.")
        status_val = job["status"]
        report = job["report"]
        error = job["error"]

    if status_val == "error":
        raise HTTPException(status_code=400, detail=f"Audit job failed: {error}")
    if status_val != "done":
        raise HTTPException(status_code=400, detail=f"Audit job is still in progress (status: {status_val}).")
    return report


@router.get("/audit/{job_id}/readme")
def download_readme(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Audit job not found.")
        status_val = job["status"]
        report = job["report"]

    if status_val != "done" or not report:
        raise HTTPException(status_code=400, detail="Readme download is not ready yet.")

    readme_content = report.generated_readme
    return StreamingResponse(
        io.BytesIO(readme_content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=README_{job_id[:8]}.md"},
    )