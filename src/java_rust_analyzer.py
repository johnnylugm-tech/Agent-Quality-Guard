#!/usr/bin/env python3
"""
Java Analyzer - Pattern-based security scanning
"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class Issue:
    type: str
    severity: str
    message: str
    line: int


class JavaAnalyzer:
    """Java code analyzer"""
    
    SECURITY_PATTERNS = {
        "hardcoded_secret": [
            (re.compile(r'private\s+static\s+final\s+String\s+\w*[Kk]ey\s*='), "Hardcoded API key"),
            (re.compile(r'private\s+static\s+final\s+String\s+\w*[Pp]assword\s*='), "Hardcoded password"),
            (re.compile(r'"[A-Za-z0-9]{32,}"'), "Potential hardcoded secret"),
        ],
        "sql_injection": [
            (re.compile(r'Statement\.executeQuery\s*\('), "SQL injection risk - use PreparedStatement"),
            (re.compile(r'createStatement\s*\(\s*\)'), "SQL injection risk"),
        ],
        "xss": [
            (re.compile(r'response\.getWriter\(\)\.write\s*\('), "Potential XSS"),
        ],
        "deserialization": [
            (re.compile(r'ObjectInputStream'), "Unsafe deserialization"),
            (re.compile(r'SerializationUtils\.deserialize'), "Unsafe deserialization"),
        ],
        "crypto": [
            (re.compile(r'Cipher\.getInstance\s*\(\s*"DES'), "Weak cipher: DES"),
            (re.compile(r'Cipher\.getInstance\s*\(\s*"MD5'), "Weak hash: MD5"),
        ],
    }
    
    QUALITY_PATTERNS = {
        "todo": [
            (re.compile(r'//\s*(TODO|FIXME|HACK|XXX):?'), "TODO comment"),
        ],
        "empty_catch": [
            (re.compile(r'catch\s*\([^)]*\)\s*\{\s*\}'), "Empty catch block"),
        ],
        "system_out": [
            (re.compile(r'System\.out\.print'), "System.out usage - use logger"),
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


class RustAnalyzer:
    """Rust code analyzer"""
    
    SECURITY_PATTERNS = {
        "hardcoded_secret": [
            (re.compile(r'const\s+\w*[Kk]ey\s*:'), "Hardcoded API key"),
            (re.compile(r'const\s+\w*[Pp]assword\s*:'), "Hardcoded password"),
            (re.compile(r'let\s+api[_-]?key\s*='), "Hardcoded API key"),
        ],
        "unsafe": [
            (re.compile(r'unsafe\s*\{'), "Unsafe block - review carefully"),
        ],
        "unwrap": [
            (re.compile(r'\.unwrap\s*\('), "unwrap() can panic - use ? or match"),
        ],
        "println_debug": [
            (re.compile(r'println!\s*\(\s*"'), "Debug print - use log crate"),
        ],
    }
    
    QUALITY_PATTERNS = {
        "todo": [
            (re.compile(r'//\s*(TODO|FIXME|HACK):?'), "TODO comment"),
        ],
        "clippy": [
            (re.compile(r'#\[allow\s*\(\w+\)\]'), "Clippy allow attribute"),
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


if __name__ == "__main__":
    # Test
    java_code = """
    public class Test {
        private static final String API_KEY = "sk-1234567890";
        public void query(String input) {
            Statement stmt = connection.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id=" + input);
        }
    }
    // TODO: fix this
    """
    
    rust_code = """
    const API_KEY: &str = "secret123";
    
    fn unsafe_function() {
        unsafe { *ptr }
    }
    
    fn main() {
        let result = maybe_fail().unwrap();
    }
    // TODO: improve
    """
    
    java_analyzer = JavaAnalyzer()
    issues = java_analyzer.analyze(java_code)
    print("Java Issues:")
    for i in issues:
        print(f"  L{i.line}: [{i.severity}] {i.message}")
    
    rust_analyzer = RustAnalyzer()
    issues = rust_analyzer.analyze(rust_code)
    print("\nRust Issues:")
    for i in issues:
        print(f"  L{i.line}: [{i.severity}] {i.message}")
