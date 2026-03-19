"""
Agent Quality Guard - Main Analyzer v3.1
Uses AST for static code analysis with performance optimizations
"""

import ast
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from functools import lru_cache


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Issue:
    """Represents a code quality issue"""
    type: str  # correctness, security, maintainability, performance, coverage
    severity: str  # high, medium, low
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary representation.
        
        Returns:
            Dictionary with type, severity, message, and line
        """
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "line": self.line
        }


# =============================================================================
# Exception Hierarchy (L1-L4 Error Classification)
# =============================================================================

class AnalyzerError(Exception):
    """Base exception for analyzer errors.
    
    Attributes:
        message: Error message
        level: Error level (L1-L4)
        recoverable: Whether the error is recoverable
    """
    def __init__(self, message: str, level: str, recoverable: bool = False):
        """Initialize analyzer error.
        
        Args:
            message: Error message
            level: Error level (L1-L4)
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.level = level
        self.recoverable = recoverable


class InputError(AnalyzerError):
    """L1: Input error - immediate return.
    
    Raised when input validation fails (e.g., None, empty string, syntax error).
    """
    def __init__(self, message: str):
        """Initialize input error.
        
        Args:
            message: Error message
        """
        super().__init__(message, "L1", recoverable=False)


class ToolError(AnalyzerError):
    """L2: Tool error - retry.
    
    Raised when an external tool fails but may succeed on retry.
    """
    def __init__(self, message: str):
        """Initialize tool error.
        
        Args:
            message: Error message
        """
        super().__init__(message, "L2", recoverable=True)


class ExecutionError(AnalyzerError):
    """L3: Execution error - degrade/report.
    
    Raised when analysis fails but can continue with degraded functionality.
    """
    def __init__(self, message: str):
        """Initialize execution error.
        
        Args:
            message: Error message
        """
        super().__init__(message, "L3", recoverable=True)


class SystemError(AnalyzerError):
    """L4: System error - circuit breaker.
    
    Raised when system-level errors occur (e.g., out of memory).
    """
    def __init__(self, message: str):
        """Initialize system error.
        
        Args:
            message: Error message
        """
        super().__init__(message, "L4", recoverable=False)


# =============================================================================
# Performance Optimization: Pre-compiled Regex Patterns
# =============================================================================

# Pre-compile regex patterns once at module level
_SECURITY_PATTERNS = {
    "hardcoded_secret": [
        re.compile(r'password\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        re.compile(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        re.compile(r'secret\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
        re.compile(r'token\s*=\s*["\'][^"\']+["\']', re.IGNORECASE),
    ],
    "sql_injection": [
        re.compile(r'execute\s*\(\s*["\'].*\%s'),
        re.compile(r'cursor\.execute\s*\([^,]+\+'),
    ],
    "eval_usage": [
        re.compile(r'\beval\s*\('),
        re.compile(r'\bexec\s*\('),
    ],
    "insecure_random": [
        re.compile(r'random\.random\s*\('),
    ],
}


# =============================================================================
# Utility Functions
# =============================================================================

def _get_function_body_lines(tree: ast.AST, node: ast.FunctionDef) -> int:
    """
    Get the number of lines in a function body.
    
    Args:
        tree: Full AST tree
        node: FunctionDef node
        
    Returns:
        Number of lines in the function body
    """
    if not hasattr(node, 'body') or not node.body:
        return 0
    
    # Get the end line of the function
    end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno + len(node.body)
    
    # Count non-empty, non-comment lines within the function
    lines = []
    for i in range(node.lineno - 1, end_line):
        # This is a simplified version - in production, we'd need the source
        lines.append(i)
    
    return max(0, end_line - node.lineno + 1)


def _calculate_ast_hash(tree: ast.AST) -> int:
    """Calculate a hash for the AST for caching purposes."""
    return hash(ast.dump(tree))


@lru_cache(maxsize=256)
def _calculate_complexity_cached(tree_hash: int, tree_dump: str) -> int:
    """
    Calculate cyclomatic complexity with caching.
    
    Args:
        tree_hash: Hash of the AST
        tree_dump: String dump of AST for cache key
        
    Returns:
        Cyclomatic complexity value
    """
    # Re-parse from dump for actual calculation
    tree = ast.parse(tree_dump)
    return _compute_complexity(tree)


def _compute_complexity(tree: ast.AST) -> int:
    """
    Compute cyclomatic complexity.
    
    Complexity = 1 + number of decision points (if, while, for, except, and, or)
    This counts all decision points in the AST.
    
    Args:
        tree: AST tree to analyze
        
    Returns:
        Cyclomatic complexity value
    """
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity


# =============================================================================
# Lazy Parser with Caching
# =============================================================================

class LazyParser:
    """
    Lazy AST parser with caching.
    Only parses when needed and caches results.
    """
    
    def __init__(self, max_cache_size: int = 100):
        """Initialize lazy parser with cache."""
        self._cache: Dict[int, ast.AST] = {}
        self._max_cache_size = max_cache_size
    
    def parse(self, code: str) -> ast.AST:
        """
        Parse code with caching.
        
        Args:
            code: Python source code to parse
            
        Returns:
            Parsed AST tree
        """
        cache_key = hash(code)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        tree = ast.parse(code)
        
        # Manage cache size with simple FIFO
        if len(self._cache) >= self._max_cache_size:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        
        self._cache[cache_key] = tree
        return tree
    
    def parse_if_valid(self, code: str) -> Optional[ast.AST]:
        """
        Parse only if code is valid.
        
        Args:
            code: Python source code
            
        Returns:
            AST tree if valid, None otherwise
        """
        try:
            return self.parse(code)
        except SyntaxError:
            return None


# Global lazy parser instance
_lazy_parser = LazyParser()


# =============================================================================
# Main Analyzer Class
# =============================================================================

class CodeAnalyzer:
    """
    Main code analyzer using AST with performance optimizations.
    
    Uses lazy evaluation: parse → analyze → report
    Optimized to minimize redundant AST traversals.
    """
    
    def __init__(self):
        """Initialize the code analyzer."""
        self.issues: List[Issue] = []
        self._lines: List[str] = []
        self._tree: Optional[ast.AST] = None
        self._complexity: Optional[int] = None
        self._function_locs: Dict[str, Tuple[int, int]] = {}
    
    # =========================================================================
    # Stage 1: Parse (Lazy Evaluation)
    # =========================================================================
    
    def _parse_code(self, code: str) -> ast.AST:
        """
        Stage 1: Parse code into AST.
        
        Args:
            code: Python source code
            
        Returns:
            Parsed AST tree
        """
        self._lines = code.split('\n')
        return _lazy_parser.parse(code)
    
    # =========================================================================
    # Stage 2: Analyze (Optimized Single Pass)
    # =========================================================================
    
    def _analyze(self, tree: ast.AST, code: str) -> None:
        """
        Stage 2: Run all analysis passes.
        
        Optimized to do single AST walk for multiple checks.
        
        Args:
            tree: Parsed AST tree
            code: Source code
        """
        # Pre-calculate complexity once
        self._complexity = _compute_complexity(tree)
        
        # Build function location map for accurate line counting
        self._build_function_map(tree)
        
        # Single pass for correctness, security, and structure
        self._analyze_correctness_and_security(tree)
        
        # Single pass for maintainability
        self._analyze_maintainability(tree)
        
        # Single pass for performance
        self._analyze_performance(tree)
        
        # Single pass for coverage
        self._analyze_coverage(tree)
    
    def _build_function_map(self, tree: ast.AST) -> None:
        """
        Build a map of function names to their line ranges.
        
        Args:
            tree: AST tree
        """
        self._function_locs = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else node.lineno
                self._function_locs[node.name] = (node.lineno, end_line)
    
    def _is_in_function(self, line: int) -> Optional[str]:
        """
        Check if a line is inside a function and return the function name.
        
        Args:
            line: Line number to check
            
        Returns:
            Function name if line is inside a function, None otherwise
        """
        for func_name, (start, end) in self._function_locs.items():
            if start <= line <= end:
                return func_name
        return None
    
    def _analyze_correctness_and_security(self, tree: ast.AST) -> None:
        """
        Combined correctness and security analysis.
        
        Args:
            tree: AST tree
        """
        for node in ast.walk(tree):
            # Correctness: Division by zero
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    self._add_issue(
                        "correctness", "high",
                        "Potential division by zero",
                        node.lineno
                    )
            
            # Correctness: None comparison
            if isinstance(node, ast.Compare):
                for comp in node.ops:
                    if isinstance(comp, (ast.Eq, ast.NotEq)):
                        for comparator in node.comparators:
                            if isinstance(comparator, ast.Constant) and comparator.value is None:
                                self._add_issue(
                                    "correctness", "medium",
                                    "Use 'is None' instead of '== None' for None comparison",
                                    node.lineno
                                )
            
            # Correctness: Empty except block
            if isinstance(node, ast.ExceptHandler):
                if node.body and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    self._add_issue(
                        "correctness", "medium",
                        "Empty except block found",
                        node.lineno
                    )
            
            # Security: pickle usage
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id == "pickle":
                        self._add_issue(
                            "security", "medium",
                            "Using pickle can be unsafe with untrusted data",
                            node.lineno
                        )
        
        # Security: Regex patterns (pre-compiled for performance)
        for idx, line in enumerate(self._lines, 1):
            # Skip comment lines
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            # Hardcoded secrets
            for pattern in _SECURITY_PATTERNS["hardcoded_secret"]:
                if pattern.search(line):
                    self._add_issue(
                        "security", "high",
                        f"Hardcoded secret detected: {line.strip()[:50]}",
                        idx
                    )
            
            # Eval/exec usage
            for pattern in _SECURITY_PATTERNS["eval_usage"]:
                if pattern.search(line):
                    self._add_issue(
                        "security", "high",
                        "Use of eval/exec is a security risk",
                        idx
                    )
            
            # SQL injection patterns
            for pattern in _SECURITY_PATTERNS["sql_injection"]:
                if pattern.search(line):
                    self._add_issue(
                        "security", "high",
                        "Potential SQL injection vulnerability",
                        idx
                    )
    
    def _analyze_maintainability(self, tree: ast.AST) -> None:
        """
        Check maintainability issues.
        
        Args:
            tree: AST tree
        """
        # Check function lengths using the accurate function map
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line
                
                # Count actual function body lines
                func_length = end_line - start_line + 1
                
                if func_length > 100:
                    self._add_issue(
                        "maintainability", "medium",
                        f"Function '{func_name}' is too long ({func_length} lines). Consider splitting.",
                        start_line
                    )
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self._add_issue(
                        "maintainability", "low",
                        f"Missing docstring for {node.__class__.__name__} '{node.name}'",
                        node.lineno
                    )
        
        # Check complexity
        if self._complexity and self._complexity > 5:
            self._add_issue(
                "maintainability", "medium",
                f"Cyclomatic complexity is {self._complexity}, consider simplifying",
                1
            )
    
    def _analyze_performance(self, tree: ast.AST) -> None:
        """
        Check performance issues.
        
        Args:
            tree: AST tree
        """
        # Check for nested loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if there's another for/while inside
                nested = False
                for child in ast.walk(node):
                    if child is not node and isinstance(child, (ast.For, ast.While)):
                        nested = True
                        break
                if nested:
                    self._add_issue(
                        "performance", "medium",
                        "Nested loops detected - possible performance issue",
                        node.lineno
                    )
    
    def _analyze_coverage(self, tree: ast.AST) -> None:
        """
        Check test coverage.
        
        Args:
            tree: AST tree
        """
        has_test_functions = False
        has_asserts = False
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('test_') or node.name.endswith('_test'):
                    has_test_functions = True
            if isinstance(node, ast.Assert):
                has_asserts = True
        
        # Check for test file naming
        if self._lines and 'test' not in self._lines[0].lower():
            has_test_import = any(
                isinstance(n, ast.ImportFrom) and n.module and 'test' in n.module
                for n in ast.walk(tree)
            )
            if not has_test_import and not has_test_functions:
                self._add_issue(
                    "coverage", "medium",
                    "No test file or test functions detected",
                    1
                )
        
        if not has_asserts and has_test_functions:
            self._add_issue(
                "coverage", "low",
                "Test functions found but no assertions detected",
                1
            )
    
    # =========================================================================
    # Stage 3: Report Generation
    # =========================================================================
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        Stage 3: Generate analysis report.
        
        Returns:
            Dictionary with issues and counts
        """
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "issue_count": len(self.issues)
        }
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        message: str,
        line: Optional[int] = None
    ) -> None:
        """
        Add an issue to the list.
        
        Args:
            issue_type: Type of issue
            severity: Severity level
            message: Issue message
            line: Line number
        """
        self.issues.append(Issue(
            type=issue_type,
            severity=severity,
            message=message,
            line=line
        ))
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code and return issues.
        
        Uses lazy evaluation: parse → analyze → report.
        L1: Validate input first.
        
        Args:
            code: Python source code to analyze
            
        Returns:
            Dictionary with analysis results
            
        Raises:
            InputError: L1 - Invalid input
            ExecutionError: L3 - Analysis failed
            SystemError: L4 - System error
        """
        # L1: Input validation
        if code is None:
            raise InputError("Code input is None")
        
        if not isinstance(code, str):
            raise InputError("Code input must be a string")
        
        if len(code.strip()) == 0:
            raise InputError("Code input is empty")
        
        try:
            # Stage 1: Parse (lazy)
            tree = self._parse_code(code)
            
            # Stage 2: Analyze (optimized)
            self._analyze(tree, code)
            
            # Stage 3: Report
            return self._generate_report()
            
        except SyntaxError as e:
            # L1: Syntax error in input code
            raise InputError(f"Syntax error at line {e.lineno}: {e.msg}")
        except MemoryError:
            # L4: System error - code too large
            raise SystemError("Code too large to analyze - memory limit exceeded")
        except Exception as e:
            # L3: Execution error - unexpected
            raise ExecutionError(f"Analysis failed: {str(e)}")


# =============================================================================
# Convenience Function with Error Handling
# =============================================================================

def analyze_code(code: str) -> Dict[str, Any]:
    """
    Convenience function to analyze code.
    
    Handles L1-L4 error classification.
    
    Args:
        code: Python source code to analyze
        
    Returns:
        Dict with issues, issue_count, and optional error info
    """
    analyzer = CodeAnalyzer()
    
    try:
        return analyzer.analyze(code)
    except InputError as e:
        # L1: Input error - return immediately
        return {
            "error": str(e),
            "level": "L1",
            "issues": [],
            "issue_count": 0
        }
    except ToolError as e:
        # L2: Tool error - could retry
        return {
            "error": str(e),
            "level": "L2", 
            "issues": [],
            "issue_count": 0
        }
    except ExecutionError as e:
        # L3: Execution error - degrade
        return {
            "error": str(e),
            "level": "L3",
            "issues": [],
            "issue_count": 0
        }
    except SystemError as e:
        # L4: System error - circuit breaker
        return {
            "error": str(e),
            "level": "L4",
            "issues": [],
            "issue_count": 0
        }
