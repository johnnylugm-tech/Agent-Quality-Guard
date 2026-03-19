"""
Agent Quality Guard - Scoring Engine
Computes quality scores based on analysis results
"""

from typing import Dict, Any, List
from dataclasses import dataclass


# Weight configuration for each dimension
WEIGHTS = {
    "correctness": 0.30,
    "security": 0.25,
    "maintainability": 0.20,
    "performance": 0.15,
    "coverage": 0.10
}

# Severity penalties
SEVERITY_PENALTIES = {
    "high": 15,
    "medium": 8,
    "low": 3
}

# Dimension starting scores (max 100 per dimension)
DIMENSION_START_SCORE = 100


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown by dimension"""
    correctness: float = 0
    security: float = 0
    maintainability: float = 0
    performance: float = 0
    coverage: float = 0
    
    def total(self) -> float:
        return (self.correctness * WEIGHTS["correctness"] +
                self.security * WEIGHTS["security"] +
                self.maintainability * WEIGHTS["maintainability"] +
                self.performance * WEIGHTS["performance"] +
                self.coverage * WEIGHTS["coverage"])


def calculate_level(score: float) -> str:
    """Calculate letter grade from score"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def count_issues_by_type_and_severity(issues: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Count issues grouped by type and severity"""
    result = {}
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "low")
        
        if issue_type not in result:
            result[issue_type] = {"high": 0, "medium": 0, "low": 0}
        
        if severity in result[issue_type]:
            result[issue_type][severity] += 1
    
    return result


def calculate_dimension_score(issues: List[Dict[str, Any]], dimension: str) -> float:
    """
    Calculate score for a specific dimension
    Returns score from 0-100
    """
    # Start with perfect score
    score = DIMENSION_START_SCORE
    
    # Filter issues for this dimension
    dimension_issues = [i for i in issues if i.get("type") == dimension]
    
    # Apply penalties based on severity
    for issue in dimension_issues:
        severity = issue.get("severity", "low")
        penalty = SEVERITY_PENALTIES.get(severity, SEVERITY_PENALTIES["low"])
        score -= penalty
    
    # Ensure score doesn't go below 0
    return max(0, score)


def generate_summary(issues: List[Dict[str, Any]], score: float, level: str) -> str:
    """Generate human-readable summary"""
    issue_count = len(issues)
    high_count = sum(1 for i in issues if i.get("severity") == "high")
    medium_count = sum(1 for i in issues if i.get("severity") == "medium")
    low_count = sum(1 for i in issues if i.get("severity") == "low")
    
    summary_parts = []
    
    # Overall assessment
    if level == "A":
        summary_parts.append("Excellent code quality. Minor or no issues detected.")
    elif level == "B":
        summary_parts.append("Good code quality. Some improvements recommended.")
    elif level == "C":
        summary_parts.append("Acceptable code quality. Multiple issues need attention.")
    elif level == "D":
        summary_parts.append("Below average quality. Significant issues detected.")
    else:
        summary_parts.append("Poor quality. Critical issues require immediate attention.")
    
    # Issue breakdown
    if issue_count > 0:
        summary_parts.append(
            f"Found {issue_count} issue(s): {high_count} high, "
            f"{medium_count} medium, {low_count} low."
        )
    else:
        summary_parts.append("No issues detected.")
    
    # Priority recommendations
    if high_count > 0:
        summary_parts.append("Priority: Fix high-severity security and correctness issues first.")
    elif medium_count > 0:
        summary_parts.append("Priority: Address medium-severity issues to improve maintainability.")
    
    return " ".join(summary_parts)


def compute_score(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute final quality score from analysis result
    
    Returns:
        dict with score (0-100), level (A/B/C/D/F), issues, summary
    """
    # Handle error cases
    if "error" in analysis_result:
        return {
            "score": 0,
            "level": "F",
            "issues": [],
            "summary": f"Analysis failed: {analysis_result.get('error')}",
            "breakdown": {},
            "error_level": analysis_result.get("level", "L1")
        }
    
    issues = analysis_result.get("issues", [])
    
    # Calculate dimension scores
    breakdown = ScoreBreakdown(
        correctness=calculate_dimension_score(issues, "correctness"),
        security=calculate_dimension_score(issues, "security"),
        maintainability=calculate_dimension_score(issues, "maintainability"),
        performance=calculate_dimension_score(issues, "performance"),
        coverage=calculate_dimension_score(issues, "coverage")
    )
    
    # Calculate weighted total score
    total_score = breakdown.total()
    
    # Round to integer
    final_score = round(total_score)
    
    # Calculate letter grade
    level = calculate_level(final_score)
    
    # Generate summary
    summary = generate_summary(issues, final_score, level)
    
    return {
        "score": final_score,
        "level": level,
        "issues": issues,
        "summary": summary,
        "breakdown": {
            "correctness": round(breakdown.correctness, 1),
            "security": round(breakdown.security, 1),
            "maintainability": round(breakdown.maintainability, 1),
            "performance": round(breakdown.performance, 1),
            "coverage": round(breakdown.coverage, 1)
        }
    }


def score_from_code(code: str) -> Dict[str, Any]:
    """
    Convenience function to analyze and score code in one call
    """
    from analyzer import analyze_code
    
    analysis_result = analyze_code(code)
    return compute_score(analysis_result)
