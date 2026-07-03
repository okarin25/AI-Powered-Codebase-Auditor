import re

from pydantic import BaseModel, field_validator

GITHUB_REPO_PATTERN = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+$")


class FileIssue(BaseModel):
    file: str
    line: int | None
    tool: str  # "radon" | "bandit" | "pylint"
    severity: str  # "low" | "medium" | "high"
    message: str


class AuditReport(BaseModel):
    repo_url: str
    overall_score: float  # 0-100
    summary: str  # LLM-generated plain-English summary
    complexity_hotspots: list[FileIssue]
    security_issues: list[FileIssue]
    lint_issues: list[FileIssue]
    generated_readme: str


class AuditRequest(BaseModel):
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        if not GITHUB_REPO_PATTERN.match(cleaned):
            raise ValueError(
                "repo_url must be a public GitHub repository URL in the form "
                "https://github.com/<owner>/<repo>"
            )
        return cleaned


class AuditResponse(BaseModel):
    job_id: str
    status: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: str | None = None
    error: str | None = None