import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.logging_config import configure_logging

# Loading settings here (before anything else) means a missing GOOGLE_API_KEY
# crashes the app immediately on startup with a clear error, instead of
# failing silently on the first real audit request.
settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Codebase Auditor & Documentation Agent API",
    description="Backend API for static analysis and LLM-agent codebase auditing",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Codebase Auditor API starting up. API key protection: %s.",
        "ENABLED" if settings.api_key else "DISABLED (set API_KEY env var before deploying publicly)",
    )


@app.get("/")
def read_root():
    """Root endpoint for health checks."""
    return {"status": "ok", "service": "Codebase Auditor Backend"}