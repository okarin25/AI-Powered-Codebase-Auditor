import json
import logging
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools import AuditSessionContext, get_agent_tools
from app.core.config import get_settings
from app.core.llm_utils import invoke_with_resilience
from app.models.schemas import AuditReport, FileIssue

logger = logging.getLogger(__name__)


# Pydantic schema specifically for the LLM to structure the audit summary and metadata
class LLMAuditResponse(BaseModel):
    overall_score: float
    summary: str
    generated_readme: str


def run_audit_agent(repo_url: str, repo_root: str, precompiled_issues: Dict[str, List[FileIssue]]) -> AuditReport:
    """
    Orchestrates the LangChain agent execution over the repository using a
    custom tool-calling loop. Every direct call to the model goes through
    `invoke_with_resilience`, which rate-limits and retries — without this,
    a single free-tier 429 partway through the loop kills the whole job.
    """
    logger.info("Setting up LangChain agent for %s...", repo_url)
    settings = get_settings()

    context = AuditSessionContext(repo_root)

    for file_path, issues in precompiled_issues.items():
        rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/")
        for issue in issues:
            if issue.tool == "radon":
                context.complexity_cache.setdefault(rel_path, []).append(issue)
            elif issue.tool == "bandit":
                context.security_cache.setdefault(rel_path, []).append(issue)
            elif issue.tool == "pylint":
                context.lint_cache.setdefault(rel_path, []).append(issue)

    tools = get_agent_tools(context)

    from app.docgen.generator import get_llm

    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    summary_counts = {
        "radon": sum(len(issues) for issues in context.complexity_cache.values()),
        "bandit": sum(len(issues) for issues in context.security_cache.values()),
        "pylint": sum(len(issues) for issues in context.lint_cache.values()),
    }

    analysis_overview = (
        f"Pre-run Static Analysis results found:\n"
        f"- Complexity Hotspots (Radon): {summary_counts['radon']} issues detected\n"
        f"- Security Flags (Bandit): {summary_counts['bandit']} issues detected\n"
        f"- Code Smells / Lint (Pylint): {summary_counts['pylint']} issues detected\n"
    )

    user_input = (
        f"Perform a complete audit on the repository. Cloned path is located at: {repo_root}.\n"
        f"URL of the repository is {repo_url}.\n\n"
        f"{analysis_overview}\n"
        f"Explore the file tree, read critical code files and dependency files, and check details of these analysis errors.\n"
        f"When you have completed the analysis, write a detailed executive summary, determine an overall quality score (0-100), and construct a beautiful, comprehensive, and modular README.md (combining details of stack, architecture, installation, usage, and audit results).\n"
        f"Assemble all of this into your final report output."
    )

    messages: List[Any] = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ]

    max_iterations = settings.agent_max_iterations
    agent_output = ""

    logger.info("Executing custom agent tool-calling loop (max %d iterations)...", max_iterations)

    for i in range(max_iterations):
        logger.info("Agent loop iteration %d/%d", i + 1, max_iterations)

        # Rate-limited + retried: this is the call that previously crashed
        # the whole job on the first free-tier 429 it hit.
        response = invoke_with_resilience(lambda: llm_with_tools.invoke(messages))
        messages.append(response)

        if not response.tool_calls:
            agent_output = response.content
            logger.info("Agent reached final answer.")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            logger.info("Agent executing tool: '%s' with arguments: %s", tool_name, json.dumps(tool_args))

            tool_fn = next((t for t in tools if t.name == tool_name), None)
            if not tool_fn:
                result_str = f"Error: Tool '{tool_name}' not found."
            else:
                try:
                    result_str = tool_fn.invoke(tool_args)
                except Exception as ex:  # noqa: BLE001 - tool errors are surfaced to the agent, not raised
                    result_str = f"Error executing tool '{tool_name}': {ex}"

            logger.info("Tool '%s' completed. Result length: %d", tool_name, len(str(result_str)))

            messages.append(ToolMessage(content=str(result_str), name=tool_name, tool_call_id=tool_id))

    if not agent_output:
        agent_output = messages[-1].content if messages else "Max iterations reached without a clean exit."
        logger.warning("Agent exhausted iterations without a clean exit.")

    logger.info("Agent loop complete. Structuring output...")

    structured_llm = llm.with_structured_output(LLMAuditResponse)

    structure_prompt = (
        f"You are a structured parser. Read the following audit conversation transcript and notes from our agent, "
        f"and format it into the required JSON schema.\n\n"
        f"Agent Notes:\n"
        f"{agent_output}\n\n"
        f"Extract:\n"
        f"1. `overall_score`: The score between 0 and 100.\n"
        f"2. `summary`: The plain-English summary of the codebase quality and features.\n"
        f"3. `generated_readme`: The full generated markdown README.\n"
    )

    try:
        structured_response = invoke_with_resilience(lambda: structured_llm.invoke(structure_prompt))

        complexity_flat = [issue for issues in context.complexity_cache.values() for issue in issues]
        security_flat = [issue for issues in context.security_cache.values() for issue in issues]
        lint_flat = [issue for issues in context.lint_cache.values() for issue in issues]

        return AuditReport(
            repo_url=repo_url,
            overall_score=structured_response.overall_score,
            summary=structured_response.summary,
            complexity_hotspots=complexity_flat,
            security_issues=security_flat,
            lint_issues=lint_flat,
            generated_readme=structured_response.generated_readme,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to structure the final audit report: %s", exc)
        return AuditReport(
            repo_url=repo_url,
            overall_score=75.0,
            summary="Audit completed. However, there was an issue structuring the summary details.",
            complexity_hotspots=[],
            security_issues=[],
            lint_issues=[],
            generated_readme=agent_output if agent_output else "No readme generated.",
        )