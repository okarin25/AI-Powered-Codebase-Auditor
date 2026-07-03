import logging
import threading

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.core.llm_utils import invoke_with_resilience
from app.docgen.prompts import DOCSTRING_PROMPT, README_SECTION_PROMPT

logger = logging.getLogger(__name__)

_cached_model_name: str | None = None
_model_lock = threading.Lock()

_FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",  # most generous free-tier RPM as of mid-2026
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def get_llm() -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI model.
    Auto-detects and caches (thread-safely) the first available model from
    the fallback list, so concurrent jobs don't each redo model discovery.
    """
    global _cached_model_name

    settings = get_settings()
    api_key = settings.google_api_key

    if _cached_model_name:
        return ChatGoogleGenerativeAI(model=_cached_model_name, google_api_key=api_key, temperature=0.2)

    with _model_lock:
        # Double-checked locking: another thread may have finished discovery
        # while this one was waiting for the lock.
        if _cached_model_name:
            return ChatGoogleGenerativeAI(model=_cached_model_name, google_api_key=api_key, temperature=0.2)

        last_err: Exception | None = None
        for model_name in _FALLBACK_MODELS:
            try:
                logger.info("Attempting to initialize model %s...", model_name)
                llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=0.2)
                invoke_with_resilience(lambda: llm.invoke("test"))
                logger.info("Successfully initialized model: %s", model_name)
                _cached_model_name = model_name
                return llm
            except Exception as exc:  # noqa: BLE001
                logger.warning("Model %s initialization failed: %s", model_name, exc)
                last_err = exc

        raise ValueError(f"None of the fallback Gemini models could be initialized. Last error: {last_err}")


def generate_docstring(code_snippet: str) -> str:
    """Calls the Gemini LLM to generate a Google-style docstring for a Python function/class."""
    try:
        llm = get_llm()
        prompt = PromptTemplate.from_template(DOCSTRING_PROMPT)
        chain = prompt | llm
        response = invoke_with_resilience(lambda: chain.invoke({"code_snippet": code_snippet}))
        return response.content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.error("Docstring generation failed: %s", exc)
        return f'"""Error generating docstring: {exc}"""'


def generate_readme_section(section_name: str, context: str) -> str:
    """Calls the Gemini LLM to generate a specific section of the README.md."""
    try:
        llm = get_llm()
        prompt = PromptTemplate.from_template(README_SECTION_PROMPT)
        chain = prompt | llm
        response = invoke_with_resilience(
            lambda: chain.invoke({"section_name": section_name, "context": context})
        )
        return response.content.strip()
    except Exception as exc:  # noqa: BLE001
        logger.error("README section generation failed for %s: %s", section_name, exc)
        return f"Error generating README section: {exc}"