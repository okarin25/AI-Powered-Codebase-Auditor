# Automated Codebase Auditor & Documentation Agent

> **Instructions for AI coding agents (Gemini Code Assist, Claude Code, Copilot, etc.):**
> This file is the single source of truth for this project. Read it fully before writing any code.
> Build incrementally following the **Build Roadmap** section — do not skip phases. Ask the user
> for clarification only when a decision genuinely blocks progress; otherwise make a reasonable
> choice and note it in a `DECISIONS.md` file at the repo root.

---

## 1. Project Overview

**What it does:** A web app where a user pastes a public GitHub repo URL. An AI agent then:
1. Clones/fetches the repo
2. Runs static analysis (complexity, code smells, security issues)
3. Uses an LLM agent to reason over the results + source files
4. Generates a structured **audit report** (quality score, hotspots, security flags)
5. Auto-generates **documentation** (README, module-level docstrings, architecture summary)
6. Displays everything in a dashboard, with the option to download the generated docs

**Why this project (resume framing):** Demonstrates LLM agent orchestration (LangChain, tool-calling),
static analysis integration, full-stack delivery, and free-tier cloud deployment — a good signal for
AI/ML engineer and full-stack roles alike.

---

## 2. Tech Stack (100% free to build & run)

| Layer | Choice | Why |
|---|---|---|
| Backend framework | **Python 3.11+ / FastAPI** | Async, modern, great resume signal |
| Agent orchestration | **LangChain** (`langchain`, `langchain-google-genai`) | Tool-calling agent, chains, memory |
| LLM | **Google Gemini API** (`gemini-1.5-flash` or `gemini-2.0-flash`) | Generous free tier |
| Static analysis (Python) | `radon` (complexity), `bandit` (security), `pylint` (lint) | Free, open-source, native Python |
| Static analysis (multi-language) | `semgrep` (free OSS rules) | Extends beyond Python later |
| Repo access | `GitPython` (clone) or GitHub REST API | No auth needed for public repos |
| Vector store (optional, Phase 4) | `FAISS` (local, free) | Enables Q&A-over-codebase feature |
| Frontend | **React + Vite + Tailwind CSS** | Fast dev, free hosting fit |
| Backend hosting | **Render** (free web service tier) or **Railway** (free trial credits) | No-cost deploy for FastAPI |
| Frontend hosting | **Vercel** or **Netlify** (free tier) | Zero-cost static/SPA hosting |
| Package/env management | `venv` + `requirements.txt` (or `poetry`) | Standard, free |

> Note: Free backend tiers (Render) spin down on inactivity — mention this as a known limitation in
> the README; it's normal for a portfolio project.

---

## 3. High-Level Architecture

```
┌─────────────┐     repo URL      ┌───────────────────────┐
│   Frontend   │ ───────────────▶ │   FastAPI Backend      │
│ (React/Vite) │ ◀─────────────── │                        │
└─────────────┘   audit + docs    │  ┌──────────────────┐  │
                                   │  │ Ingestion Layer   │  │  (clone repo, list files)
                                   │  └────────┬─────────┘  │
                                   │           ▼            │
                                   │  ┌──────────────────┐  │
                                   │  │ Static Analysis   │  │  (radon, bandit, pylint, semgrep)
                                   │  │ Tool Layer         │  │
                                   │  └────────┬─────────┘  │
                                   │           ▼            │
                                   │  ┌──────────────────┐  │
                                   │  │ LangChain Agent   │  │──▶ Gemini API
                                   │  │ (tool-calling)     │  │
                                   │  └────────┬─────────┘  │
                                   │           ▼            │
                                   │  ┌──────────────────┐  │
                                   │  │ Report + Doc Gen   │  │  (JSON report, README.md, docstrings)
                                   │  └──────────────────┘  │
                                   └───────────────────────┘
```

---

## 4. Folder Structure

```
codebase-auditor/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── api/
│   │   │   └── routes.py          # /audit, /status, /report endpoints
│   │   ├── agent/
│   │   │   ├── agent.py           # LangChain agent setup
│   │   │   └── tools.py           # Tool wrappers (radon, bandit, pylint, semgrep)
│   │   ├── ingestion/
│   │   │   └── repo_loader.py     # Clone repo, walk file tree
│   │   ├── analysis/
│   │   │   ├── complexity.py
│   │   │   ├── security.py
│   │   │   └── lint.py
│   │   ├── docgen/
│   │   │   └── generator.py       # README + docstring generation
│   │   └── models/
│   │       └── schemas.py         # Pydantic models for requests/responses
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/                   # fetch calls to backend
│   │   └── App.tsx
│   ├── package.json
│   └── .env.example
├── DECISIONS.md                   # agent logs assumptions/decisions here
├── README.md                      # final polished project README (write last)
└── PROJECT_SPEC.md                # this file
```

---

## 5. Core Agent Tools (LangChain Tool-Calling)

The LangChain agent should have access to these tools, each a thin wrapper around a static-analysis
library:

1. **`run_complexity_analysis(file_path)`** → wraps `radon` → cyclomatic complexity + maintainability index
2. **`run_security_scan(file_path)`** → wraps `bandit` → security issues with severity
3. **`run_lint_check(file_path)`** → wraps `pylint` → style/code-smell issues
4. **`read_file(file_path)`** → returns file contents (chunked if large) for the agent to reason over
5. **`list_repo_structure()`** → returns directory tree so the agent can decide what to prioritize
6. **`generate_docstring(code_snippet)`** → LLM call to produce a docstring for a function/class
7. **`generate_readme_section(section_name, context)`** → LLM call to draft one README section at a time

The agent's job: walk the repo, call analysis tools, synthesize results into a single structured
**AuditReport** (see schema below), then use `generate_readme_section` to build the final README.

---

## 6. Data Schema (Pydantic)

```python
class FileIssue(BaseModel):
    file: str
    line: int | None
    tool: str            # "radon" | "bandit" | "pylint"
    severity: str         # "low" | "medium" | "high"
    message: str

class AuditReport(BaseModel):
    repo_url: str
    overall_score: float  # 0-100
    summary: str           # LLM-generated plain-English summary
    complexity_hotspots: list[FileIssue]
    security_issues: list[FileIssue]
    lint_issues: list[FileIssue]
    generated_readme: str
```

---

## 7. API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/audit` | Accepts `{ repo_url }`, kicks off the pipeline, returns `job_id` |
| `GET` | `/api/audit/{job_id}/status` | Poll job status (`pending`, `running`, `done`, `error`) |
| `GET` | `/api/audit/{job_id}/report` | Returns the final `AuditReport` JSON |
| `GET` | `/api/audit/{job_id}/readme` | Returns generated README as downloadable markdown |

Run the pipeline as a background task (`FastAPI BackgroundTasks` or a simple in-memory job queue) so
the frontend can poll instead of holding a long request open — keeps it simple and free-tier friendly.

---

## 8. Environment Variables

**backend/.env.example**
```
GOOGLE_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
MAX_REPO_SIZE_MB=50
```

**frontend/.env.example**
```
VITE_API_BASE_URL=http://localhost:8000
```

---

## 9. Local Setup Instructions

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # then add your Gemini API key
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

---

## 10. Deployment Plan (Free Tier)

1. **Backend → Render**
   - New "Web Service" → connect GitHub repo → root dir `backend/`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add `GOOGLE_API_KEY` as an environment variable in Render's dashboard
   - Select the **Free** instance type

2. **Frontend → Vercel**
   - Import repo → root dir `frontend/`
   - Framework preset: Vite
   - Add `VITE_API_BASE_URL` env var pointing to the Render backend URL

3. Update `ALLOWED_ORIGINS` in the backend env to include the deployed Vercel URL (CORS).

---

## 11. Build Roadmap (build in this order)

- **Phase 0 — Scaffold:** Create folder structure above, empty FastAPI app that returns `{status: "ok"}`, empty Vite React app that renders a title. Confirm both run locally.
- **Phase 1 — Ingestion:** Implement `repo_loader.py` to clone a public repo into a temp dir and list Python files.
- **Phase 2 — Static Analysis:** Wire up `radon`, `bandit`, `pylint` as plain function calls (no LLM yet). Return raw JSON from `/api/audit`.
- **Phase 3 — LangChain Agent:** Wrap the analysis functions as LangChain tools. Build the agent that calls them and produces the `AuditReport.summary`.
- **Phase 4 — Doc Generation:** Add `generate_readme_section` and docstring generation tools. Assemble a full README from sections.
- **Phase 5 — Frontend Dashboard:** Build the UI — repo URL input, polling status, report view (score, issues table), README preview + download button.
- **Phase 6 — Deploy:** Follow Section 10. Test end-to-end on the deployed URLs.
- **Phase 7 (stretch) — RAG Q&A:** Add FAISS vector store over the repo so users can ask questions like "where is auth handled?"

---

## 12. Coding Conventions

- Python: type hints everywhere, Pydantic models for all API I/O, `black` for formatting.
- Keep LLM prompts in a dedicated `prompts.py` file per module — never inline large prompt strings in logic code.
- Every static-analysis tool wrapper must fail gracefully (repo may not be pure Python, files may be huge) — never let one bad file crash the whole audit.
- Log agent tool calls (which tool, which file) so the audit process is debuggable and demoable in an interview.