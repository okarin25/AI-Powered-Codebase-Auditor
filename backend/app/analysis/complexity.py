import os
import logging
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from app.models.schemas import FileIssue

logger = logging.getLogger(__name__)

def analyze_complexity(file_path: str, repo_root: str) -> list[FileIssue]:
    """
    Analyzes the cyclomatic complexity and maintainability index of a Python file.
    Returns a list of FileIssue objects.
    """
    issues = []
    rel_path = os.path.relpath(file_path, repo_root).replace("\\", "/")
    
    if not file_path.endswith(".py"):
        return issues

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
            
        # 1. Cyclomatic Complexity
        try:
            blocks = cc_visit(code)
            for block in blocks:
                # We flag blocks with complexity > 5 (Grade B and worse)
                if block.complexity > 5:
                    if block.complexity <= 10:
                        severity = "low"
                    elif block.complexity <= 20:
                        severity = "medium"
                    else:
                        severity = "high"
                    
                    # FIX: Safely extract type name since block items don't have a '.construct' property
                    block_type = type(block).__name__
                    
                    issues.append(FileIssue(
                        file=rel_path,
                        line=block.lineno,
                        tool="radon",
                        severity=severity,
                        message=f"{block_type} '{block.name}' has high cyclomatic complexity of {block.complexity} (Grade {block.letter})."
                    ))
        except Exception as e:
            logger.error(f"Radon complexity check failed for {rel_path}: {e}")
            
        # 2. Maintainability Index
        try:
            mi_score = mi_visit(code, multi=True)
            # Radon MI scale: A (100-20), B (19-10), C (9-0)
            # Flag any MI score below 70 as a general best practice.
            if mi_score < 70:
                if mi_score >= 50:
                    severity = "low"
                elif mi_score >= 20:
                    severity = "medium"
                else:
                    severity = "high"
                    
                issues.append(FileIssue(
                    file=rel_path,
                    line=1,
                    tool="radon",
                    severity=severity,
                    message=f"File has a low Maintainability Index of {mi_score:.1f}/100."
                ))
        except Exception as e:
            logger.error(f"Radon MI check failed for {rel_path}: {e}")

    except Exception as e:
        logger.error(f"Failed to read/process file {file_path} for complexity analysis: {e}")
        
    return issues