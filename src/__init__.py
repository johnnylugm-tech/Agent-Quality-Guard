"""
Agent Quality Guard - Python Code Quality Analysis Tool

A CLI tool that analyzes Python code using AST and provides quality scores.
Version 2.0 - Now with LLM Judge, Git Hook integration, and Enhanced Reporting
"""

__version__ = "2.0.0"
__author__ = "Agent Quality Guard Team"

from analyzer import CodeAnalyzer, analyze_code, InputError, ToolError, ExecutionError, SystemError
from scorer import compute_score, score_from_code
from llm_judge import LLMJudge, llm_review, LLMConfigError as LLMConfigError
from git_hook import GitHook, install_hook, run_hook
from reporter import ReportGenerator, generate_report, TrendData

__all__ = [
    # Core
    "CodeAnalyzer",
    "analyze_code",
    "compute_score",
    "score_from_code",
    # Errors
    "InputError",
    "ToolError", 
    "ExecutionError",
    "SystemError",
    # LLM Judge
    "LLMJudge",
    "llm_review",
    "LLMConfigError",
    # Git Hook
    "GitHook",
    "install_hook",
    "run_hook",
    # Reporter
    "ReportGenerator",
    "generate_report",
    "TrendData",
]