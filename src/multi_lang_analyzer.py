#!/usr/bin/env python3
"""
Multi-Language Code Analyzer
Supports: JavaScript, TypeScript, Go

This extends the Python AST analyzer to handle other languages
using pattern-based scanning.
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Issue:
    """Code quality issue"""
    type: str
    severity: str
    message: str
    line: int
    column: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
            "column": self.column
        }


class JavaScriptAnalyzer:
    """JavaScript/TypeScript analyzer"""
    
    SECURITY_PATTERNS = {
        "hardcoded_secret": [
            (re.compile(r'["\']api[_-]?key["\']\s*:\s*["\'][^"\']+["\']'), "Hardcoded API key"),
            (re.compile(r'["\']password["\']\s*:\s*["\'][^"\']+["\']'), "Hardcoded password"),
            (re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'), "GitHub Token"),
            (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key"),
        ],
        "xss": [
            (re.compile(r'innerHTML\s*='), "Potential XSS"),
            (re.compile(r'dangerouslySetInnerHTML'), "React XSS risk"),
        ],
        "sql_injection": [
            (re.compile(r'execute\s*\(\s*[`\'"].*\$\{'), "SQL injection risk"),
        ],
        "command_injection": [
            (re.compile(r'exec\s*\(\s*'), "Command execution risk"),
            (re.compile(r'eval\s*\('), "eval() dangerous"),
        ],
    }
    
    QUALITY_PATTERNS = {
        "console_debug": [
            (re.compile(r'console\.(log|debug|warn|error)\('), "Console statement"),
        ],
        "todo": [
            (re.compile(r'//\s*(TODO|FIXME|HACK|XXX):?'), "TODO comment"),
        ],
    }
    
    def analyze(self, code: str) -> List[Issue]:
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for category, patterns in self.SECURITY_PATTERNS.items():
                for pattern, message in patterns:
                    if pattern.search(line):
                        issues.append(Issue(
                            type="security", severity="high",
                            message=message, line=line_num
                        ))
            
            for category, patterns in self.QUALITY_PATTERNS.items():
                for pattern, message in patterns:
                    if pattern.search(line):
                        issues.append(Issue(
                            type="maintainability", severity="low",
                            message=message, line=line_num
                        ))
        
        return issues


class GoAnalyzer:
    """Go analyzer"""
    
    PATTERNS = {
        "hardcoded_secret": [
            (re.compile(r'api[_-]?key\s*:=\s*["\'][^"\']+["\']'), "Hardcoded API key"),
            (re.compile(r'password\s*:=\s*["\'][^"\']+["\']'), "Hardcoded password"),
        ],
        "sql_injection": [
            (re.compile(r'Query\s*\(\s*".*\+'), "SQL injection risk"),
        ],
        "command_injection": [
            (re.compile(r'syscall\.Exec\s*\('), "Command execution risk"),
        ],
        "todo": [
            (re.compile(r'//\s*(TODO|FIXME|HACK):?'), "TODO comment"),
        ],
    }
    
    def analyze(self, code: str) -> List[Issue]:
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for category, patterns in self.PATTERNS.items():
                for pattern, message in patterns:
                    if pattern.search(line):
                        severity = "high" if "security" in category else "low"
                        issues.append(Issue(
                            type="security" if severity == "high" else "maintainability",
                            severity=severity, message=message, line=line_num
                        ))
        
        return issues


class MultiLanguageAnalyzer:
    """Multi-language analyzer dispatcher"""
    
    def __init__(self):
        self.analyzers = {
            '.js': JavaScriptAnalyzer(),
            '.jsx': JavaScriptAnalyzer(),
            '.ts': JavaScriptAnalyzer(),
            '.tsx': JavaScriptAnalyzer(),
            '.go': GoAnalyzer(),
        }
    
    def analyze(self, code: str, extension: str) -> List[Issue]:
        analyzer = self.analyzers.get(extension.lower())
        if not analyzer:
            return [Issue(
                type="info", severity="low",
                message=f"Unsupported: {extension}", line=1
            )]
        return analyzer.analyze(code)


if __name__ == "__main__":
    js_code = """
    const apiKey = "sk-1234567890";
    eval(userInput);
    // TODO: fix this
    """
    
    analyzer = MultiLanguageAnalyzer()
    issues = analyzer.analyze(js_code, ".js")
    
    print("JavaScript Analysis:")
    for issue in issues:
        print(f"  [{issue.severity}] L{issue.line}: {issue.message}")
