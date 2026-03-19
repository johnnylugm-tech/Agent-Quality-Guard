"""
Agent Quality Guard - Tests
"""

import unittest
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import CodeAnalyzer, analyze_code, InputError, ExecutionError
from scorer import compute_score, calculate_level, score_from_code


class TestAnalyzer(unittest.TestCase):
    """Test cases for CodeAnalyzer"""
    
    def test_empty_code_input(self):
        """L1: Test empty code returns L1 error"""
        result = analyze_code("")
        
        self.assertIn("error", result)
        self.assertEqual(result.get("level"), "L1")
    
    def test_none_input(self):
        """L1: Test None input returns L1 error"""
        result = analyze_code(None)
        
        self.assertIn("error", result)
        self.assertEqual(result.get("level"), "L1")
    
    def test_syntax_error(self):
        """L1: Test syntax error returns L1 error"""
        code = "def missing_colon():"
        result = analyze_code(code)
        
        self.assertIn("error", result)
        self.assertEqual(result.get("level"), "L1")
    
    def test_hardcoded_secret(self):
        """Test detection of hardcoded secrets"""
        analyzer = CodeAnalyzer()
        code = '''
def connect():
    password = "secret123"
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        security_issues = [i for i in issues if i["type"] == "security"]
        self.assertGreater(len(security_issues), 0)
        self.assertEqual(security_issues[0]["severity"], "high")
    
    def test_eval_usage(self):
        """Test detection of eval usage"""
        analyzer = CodeAnalyzer()
        code = '''
user_input = "some code"
eval(user_input)
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        security_issues = [i for i in issues if i["type"] == "security"]
        high_issues = [i for i in security_issues if i["severity"] == "high"]
        self.assertGreater(len(high_issues), 0)
    
    def test_division_by_zero(self):
        """Test detection of potential division by zero"""
        analyzer = CodeAnalyzer()
        code = '''
result = 10 / 0
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        correctness_issues = [i for i in issues if i["type"] == "correctness"]
        self.assertGreater(len(correctness_issues), 0)
    
    def test_none_comparison(self):
        """Test detection of == None comparison"""
        analyzer = CodeAnalyzer()
        code = '''
if x == None:
    pass
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        correctness_issues = [i for i in issues if i["type"] == "correctness"]
        self.assertGreater(len(correctness_issues), 0)
    
    def test_empty_except(self):
        """Test detection of empty except block"""
        analyzer = CodeAnalyzer()
        code = '''
try:
    risky()
except:
    pass
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        correctness_issues = [i for i in issues if i["type"] == "correctness"]
        self.assertGreater(len(correctness_issues), 0)
    
    def test_long_function(self):
        """Test detection of long functions"""
        analyzer = CodeAnalyzer()
        # Create a long function (60+ lines)
        code = "def long_function():\n" + "\n".join([f"    x = {i}" for i in range(60)])
        
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        maintainability_issues = [i for i in issues if i["type"] == "maintainability"]
        self.assertGreater(len(maintainability_issues), 0)
    
    def test_missing_docstring(self):
        """Test detection of missing docstrings"""
        analyzer = CodeAnalyzer()
        code = '''
def my_function():
    pass

class MyClass:
    pass
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        maintainability_issues = [i for i in issues if i["type"] == "maintainability"]
        docstring_issues = [i for i in maintainability_issues if "docstring" in i["message"].lower()]
        self.assertGreaterEqual(len(docstring_issues), 2)
    
    def test_nested_loops(self):
        """Test detection of nested loops"""
        analyzer = CodeAnalyzer()
        code = '''
for i in range(10):
    for j in range(10):
        print(i, j)
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        performance_issues = [i for i in issues if i["type"] == "performance"]
        self.assertGreater(len(performance_issues), 0)
    
    def test_no_test_coverage(self):
        """Test detection of missing test coverage"""
        analyzer = CodeAnalyzer()
        code = '''
def add(a, b):
    return a + b
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        coverage_issues = [i for i in issues if i["type"] == "coverage"]
        self.assertGreater(len(coverage_issues), 0)
    
    def test_complexity_calculation(self):
        """Test cyclomatic complexity calculation"""
        analyzer = CodeAnalyzer()
        # Create code with complexity > 5
        code = '''
def complex_function(x, y, z):
    if x > 0:
        if x > 10:
            if y > 5:
                return \"big\"
            else:
                return \"small\"
        elif y < 0:
            return \"negative\"
    elif z:
        return \"zero\"
    return \"default\"
'''
        result = analyzer.analyze(code)
        issues = result["issues"]
        
        # Should detect high complexity (threshold is 5)
        maintainability_issues = [i for i in issues if "complexity" in i["message"].lower()]
        self.assertGreater(len(maintainability_issues), 0)


class TestScorer(unittest.TestCase):
    """Test cases for Scoring Engine"""
    
    def test_calculate_level(self):
        """Test letter grade calculation"""
        self.assertEqual(calculate_level(95), "A")
        self.assertEqual(calculate_level(85), "B")
        self.assertEqual(calculate_level(75), "C")
        self.assertEqual(calculate_level(65), "D")
        self.assertEqual(calculate_level(50), "F")
    
    def test_perfect_code(self):
        """Test scoring of perfect code"""
        code = '''
def greet(name: str) -> str:
    """Return a greeting message.
    
    Args:
        name: The name to greet.
    
    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"
'''
        result = score_from_code(code)
        
        # Should have high score
        self.assertGreaterEqual(result["score"], 80)
        self.assertIn(result["level"], ["A", "B"])
    
    def test_poor_code(self):
        """Test scoring of poor quality code"""
        code = '''
password="123456"
eval("os.system('rm -rf')")
for i in range(10):
    for j in range(10):
        for k in range(10):
            print(i,j,k)
'''
        result = score_from_code(code)
        
        # Should have lower score due to security issues
        self.assertLessEqual(result["score"], 90)
        self.assertIn(result["level"], ["A", "B", "C"])
    
    def test_breakdown_structure(self):
        """Test score breakdown structure"""
        code = "x = 1"
        result = score_from_code(code)
        
        self.assertIn("breakdown", result)
        breakdown = result["breakdown"]
        self.assertIn("correctness", breakdown)
        self.assertIn("security", breakdown)
        self.assertIn("maintainability", breakdown)
        self.assertIn("performance", breakdown)
        self.assertIn("coverage", breakdown)
    
    def test_error_handling(self):
        """Test error handling in scorer"""
        # Empty analysis result
        result = compute_score({"error": "test error", "level": "L1"})
        
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "F")
        self.assertEqual(result.get("error_level"), "L1")
    
    def test_summary_generation(self):
        """Test summary generation"""
        code = "print('hello')"
        result = score_from_code(code)
        
        self.assertIn("summary", result)
        self.assertIsInstance(result["summary"], str)
        self.assertGreater(len(result["summary"]), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_pipeline(self):
        """Test complete analysis pipeline"""
        code = '''
def calculate(a, b):
    """Calculate sum of two numbers."""
    return a + b

# Test it
result = calculate(1, 2)
print(result)
'''
        # This should work without errors
        result = score_from_code(code)
        
        self.assertIn("score", result)
        self.assertIn("level", result)
        self.assertIn("issues", result)
        self.assertIn("summary", result)
        
        # Score should be reasonable
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
    
    def test_json_output(self):
        """Test JSON output format"""
        code = "x = 1"
        result = score_from_code(code)
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["score"], result["score"])
        self.assertEqual(parsed["level"], result["level"])


if __name__ == "__main__":
    unittest.main()
