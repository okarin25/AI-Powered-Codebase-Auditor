import os
import json
import logging
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.analysis.complexity import analyze_complexity
from app.analysis.security import analyze_security
from app.analysis.lint import analyze_lint
from app.docgen.generator import generate_docstring, generate_readme_section
from app.ingestion.repo_loader import get_repo_structure

logger = logging.getLogger(__name__)

class AuditSessionContext:
    """
    Holds the state of the current audit session, including the repository root,
    and caches results of the static analysis tools.
    """
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.complexity_cache: Dict[str, List[Any]] = {}
        self.security_cache: Dict[str, List[Any]] = {}
        self.lint_cache: Dict[str, List[Any]] = {}

    def get_absolute_path(self, rel_path: str) -> str:
        """
        Safely resolves a relative path to absolute, preventing directory traversal.
        """
        # Clean relative path
        rel_path = rel_path.strip().replace("\\", "/")
        if rel_path.startswith("./"):
            rel_path = rel_path[2:]
            
        abs_path = os.path.abspath(os.path.join(self.repo_root, rel_path))
        if not abs_path.startswith(self.repo_root):
            raise ValueError(f"Security Warning: Attempted directory traversal outside repo root: {rel_path}")
        return abs_path

def get_agent_tools(context: AuditSessionContext) -> List[Any]:
    """
    Creates and returns the list of LangChain tools configured for the current repository context.
    """
    
    @tool
    def list_repo_structure() -> str:
        """
        Returns the tree-like directory structure of the repository.
        Use this first to understand the layout and locate key source files.
        """
        try:
            return get_repo_structure(context.repo_root)
        except Exception as e:
            return f"Error listing repository structure: {e}"

    @tool
    def read_file(file_path: str) -> str:
        """
        Reads the contents of a file given its relative path from the repository root.
        Use this to inspect files like requirements.txt, package.json, or key source files.
        """
        try:
            abs_path = context.get_absolute_path(file_path)
            if not os.path.isfile(abs_path):
                return f"Error: File not found at relative path {file_path}"
                
            # Limit file reading to 40KB to avoid token overflow
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(40000)
                if len(content) >= 40000:
                    content += "\n... [Content Truncated due to size limits] ..."
                return content
        except Exception as e:
            return f"Error reading file {file_path}: {e}"

    @tool
    def run_complexity_analysis(file_path: str) -> str:
        """
        Runs Radon on a Python file to check cyclomatic complexity and maintainability index.
        Takes a relative file path and returns a JSON string of detected complexity hotspots.
        """
        try:
            abs_path = context.get_absolute_path(file_path)
            
            # Check cache first
            if file_path in context.complexity_cache:
                issues = context.complexity_cache[file_path]
            else:
                issues = analyze_complexity(abs_path, context.repo_root)
                context.complexity_cache[file_path] = issues
                
            issues_serialized = [issue.model_dump() for issue in issues]
            return json.dumps(issues_serialized, indent=2)
        except Exception as e:
            return f"Error running complexity analysis on {file_path}: {e}"

    @tool
    def run_security_scan(file_path: str) -> str:
        """
        Runs Bandit on a Python file to check for security vulnerabilities and code issues.
        Takes a relative file path and returns a JSON string of detected security problems.
        """
        try:
            abs_path = context.get_absolute_path(file_path)
            
            # Check cache first
            if file_path in context.security_cache:
                issues = context.security_cache[file_path]
            else:
                issues = analyze_security(abs_path, context.repo_root)
                context.security_cache[file_path] = issues
                
            issues_serialized = [issue.model_dump() for issue in issues]
            return json.dumps(issues_serialized, indent=2)
        except Exception as e:
            return f"Error running security scan on {file_path}: {e}"

    @tool
    def run_lint_check(file_path: str) -> str:
        """
        Runs Pylint on a Python file to check for style issues and general code quality.
        Takes a relative file path and returns a JSON string of detected linting errors.
        """
        try:
            abs_path = context.get_absolute_path(file_path)
            
            # Check cache first
            if file_path in context.lint_cache:
                issues = context.lint_cache[file_path]
            else:
                issues = analyze_lint(abs_path, context.repo_root)
                context.lint_cache[file_path] = issues
                
            issues_serialized = [issue.model_dump() for issue in issues]
            return json.dumps(issues_serialized, indent=2)
        except Exception as e:
            return f"Error running lint check on {file_path}: {e}"

    @tool
    def generate_docstring_tool(code_snippet: str) -> str:
        """
        Generates a Google-style docstring for the provided code snippet using the Gemini model.
        """
        try:
            return generate_docstring(code_snippet)
        except Exception as e:
            return f"Error generating docstring: {e}"

    @tool
    def generate_readme_section_tool(section_name: str, context_details: str) -> str:
        """
        Generates a specific section of the README.md based on provided context details.
        Specify section_name (e.g. 'Installation', 'Usage', 'Tech Stack') and context_details.
        """
        try:
            return generate_readme_section(section_name, context_details)
        except Exception as e:
            return f"Error generating README section '{section_name}': {e}"

    return [
        list_repo_structure,
        read_file,
        run_complexity_analysis,
        run_security_scan,
        run_lint_check,
        generate_docstring_tool,
        generate_readme_section_tool
    ]
