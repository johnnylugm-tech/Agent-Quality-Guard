"""
Agent Quality Guard - Enhanced Reporter v3.0
Markdown/HTML report generation and trend tracking
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import defaultdict


class ReporterError(Exception):
    """Base exception for reporter errors"""
    pass


class ReporterConfigError(ReporterError):
    """Configuration error"""
    pass


# =============================================================================
# Trend Data Management
# =============================================================================

class TrendData:
    """
    Trend data manager for tracking code quality over time.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.expanduser("~/.agent-quality-guard"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.trend_file = self.data_dir / "trends.json"
    
    def load(self) -> List[Dict[str, Any]]:
        """Load existing trend data."""
        if not self.trend_file.exists():
            return []
        
        try:
            with open(self.trend_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save(self, data: List[Dict[str, Any]]):
        """Save trend data."""
        try:
            with open(self.trend_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise ReporterError(f"Failed to save trends: {e}")
    
    def add_entry(self, entry: Dict[str, Any]):
        """Add a new trend entry."""
        data = self.load()
        
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        
        # Add to data
        data.append(entry)
        
        # Keep last 100 entries
        if len(data) > 100:
            data = data[-100:]
        
        self.save(data)
    
    def get_trends(
        self, 
        file_path: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trend data for a specific file or overall."""
        data = self.load()
        
        # Filter by date
        cutoff = time.time() - (days * 86400)
        filtered = []
        
        for entry in data:
            timestamp = entry.get("timestamp", "")
            try:
                entry_time = datetime.fromisoformat(timestamp).timestamp()
                if entry_time >= cutoff:
                    # Filter by file if specified
                    if file_path:
                        if entry.get("file") == file_path:
                            filtered.append(entry)
                    else:
                        filtered.append(entry)
            except:
                continue
        
        return filtered
    
    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary statistics."""
        trends = self.get_trends(days=days)
        
        if not trends:
            return {
                "total_runs": 0,
                "avg_score": 0,
                "avg_level": "N/A",
                "trend": "neutral"
            }
        
        # Calculate statistics
        scores = [t.get("score", 0) for t in trends if "score" in t]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine trend
        if len(scores) >= 2:
            recent = sum(scores[-5:]) / min(5, len(scores))
            earlier = sum(scores[:5]) / min(5, len(scores))
            if recent > earlier + 5:
                trend = "improving"
            elif recent < earlier - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "total_runs": len(trends),
            "avg_score": round(avg_score, 1),
            "avg_level": self._score_to_level(avg_score),
            "trend": trend,
            "high_issues": sum(1 for t in trends for i in t.get("issues", []) if i.get("severity") == "high"),
            "files_analyzed": len(set(t.get("file") for t in trends if "file" in t))
        }
    
    def _score_to_level(self, score: float) -> str:
        """Convert score to level."""
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


# =============================================================================
# Report Generator v3.0 - Split into Collect, Format, Write
# =============================================================================

class ReportGenerator:
    """
    Generate Markdown and HTML reports.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.trend_data = TrendData(data_dir)
    
    # =========================================================================
    # Stage 1: Collect (Gather data for report)
    # =========================================================================
    
    def _collect_data(
        self,
        result: Dict[str, Any],
        file_path: Optional[str],
        days: int
    ) -> Dict[str, Any]:
        """
        Stage 1: Collect all data needed for the report.
        
        Args:
            result: Analysis result
            file_path: Analyzed file path
            days: Days for trend data
            
        Returns:
            Collected data as dict
        """
        score = result.get("score", 0)
        level = result.get("level", "F")
        issues = result.get("issues", [])
        breakdown = result.get("breakdown", {})
        summary = result.get("summary", "")
        
        # Get trend summary
        trend_summary = self.trend_data.get_summary(days=days)
        
        # Get file-specific trends if file specified
        file_trends = None
        if file_path:
            file_trends = self.trend_data.get_trends(file_path=file_path, days=days)
        
        return {
            "score": score,
            "level": level,
            "issues": issues,
            "breakdown": breakdown,
            "summary": summary,
            "file_path": file_path,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "trend_summary": trend_summary,
            "file_trends": file_trends,
            "days": days
        }
    
    # =========================================================================
    # Stage 2: Format (Generate report content)
    # =========================================================================
    
    def _format_markdown(self, data: Dict[str, Any]) -> str:
        """
        Stage 2a: Format report as Markdown.
        
        Args:
            data: Collected report data
            
        Returns:
            Markdown formatted string
        """
        score = data["score"]
        level = data["level"]
        issues = data["issues"]
        breakdown = data["breakdown"]
        summary = data["summary"]
        file_path = data["file_path"]
        timestamp = data["timestamp"]
        trend_summary = data["trend_summary"]
        file_trends = data["file_trends"]
        days = data["days"]
        
        md = []
        
        # Header
        md.append(f"# Agent Quality Guard Report")
        md.append(f"\n*Generated: {timestamp}*")
        
        if file_path:
            md.append(f"\n**File:** `{file_path}`")
        
        md.append("\n---\n")
        
        # Score section
        md.append("## Score Summary")
        md.append(f"\n| Metric | Value |")
        md.append(f"|--------|-------|")
        md.append(f"| **Score** | {score}/100 |")
        md.append(f"| **Level** | {level} |")
        md.append(f"| **Summary** | {summary} |")
        
        # Breakdown
        if breakdown:
            md.append("\n### Score Breakdown\n")
            for dim, value in breakdown.items():
                weight = {"correctness": 30, "security": 25, "maintainability": 20, 
                          "performance": 15, "coverage": 10}.get(dim, 0)
                bar = "█" * int(value / 10) + "░" * (10 - int(value / 10))
                md.append(f"- **{dim.capitalize()}** ({weight}%): `{bar}` {value:.0f}")
        
        # Issues
        md.append("\n## Issues Found\n")
        
        if not issues:
            md.append("*No issues detected!* ✅\n")
        else:
            high = [i for i in issues if i.get("severity") == "high"]
            medium = [i for i in issues if i.get("severity") == "medium"]
            low = [i for i in issues if i.get("severity") == "low"]
            
            md.append(f"Total: **{len(issues)}** issues\n")
            
            if high:
                md.append("\n### 🔴 High Priority\n")
                for issue in high:
                    line = f" (line {issue['line']})" if issue.get("line") else ""
                    md.append(f"- **{issue['type']}**: {issue['message']}{line}")
            
            if medium:
                md.append("\n### 🟡 Medium Priority\n")
                for issue in medium[:10]:
                    line = f" (line {issue['line']})" if issue.get("line") else ""
                    md.append(f"- **{issue['type']}**: {issue['message']}{line}")
                if len(medium) > 10:
                    md.append(f"- ... and {len(medium) - 10} more")
            
            if low:
                md.append("\n### 🟢 Low Priority\n")
                for issue in low[:5]:
                    md.append(f"- **{issue['type']}**: {issue['message']}")
        
        # Trend section
        md.append("\n---\n")
        md.append("## Trend Analysis\n")
        
        md.append(f"\n| Metric | Value |")
        md.append(f"|--------|-------|")
        md.append(f"| Total Runs | {trend_summary['total_runs']} |")
        md.append(f"| Average Score | {trend_summary['avg_score']} |")
        md.append(f"| Average Level | {trend_summary['avg_level']} |")
        md.append(f"| Trend | {trend_summary['trend']} |")
        md.append(f"| Files Analyzed | {trend_summary['files_analyzed']} |")
        
        # Per-file trends if file specified
        if file_path and file_trends:
            md.append(f"\n### Recent Runs for {file_path}\n")
            for entry in file_trends[-5:]:
                ts = entry.get("timestamp", "")[:10]
                md.append(f"- **{ts}**: Score {entry.get('score', 0)} ({entry.get('level', 'F')})")
        
        # Footer
        md.append("\n---\n")
        md.append("*Report generated by Agent Quality Guard v3.0*")
        
        return "\n".join(md)
    
    def _format_html(self, data: Dict[str, Any]) -> str:
        """
        Stage 2b: Format report as HTML.
        
        Args:
            data: Collected report data
            
        Returns:
            HTML formatted string
        """
        score = data["score"]
        level = data["level"]
        issues = data["issues"]
        breakdown = data["breakdown"]
        summary = data["summary"]
        file_path = data["file_path"]
        timestamp = data["timestamp"]
        trend_summary = data["trend_summary"]
        
        # Color scheme based on level
        colors = {
            "A": "#28a745",  # Green
            "B": "#7cb342",  # Light green
            "C": "#ffc107",  # Yellow
            "D": "#fd7e14",  # Orange
            "F": "#dc3545"   # Red
        }
        color = colors.get(level, "#6c757d")
        
        html = []
        
        # HTML header
        html.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Quality Guard Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 { color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        h3 { color: #666; }
        .score-card {
            display: flex;
            align-items: center;
            gap: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
            margin: 20px 0;
        }
        .score-value {
            font-size: 48px;
            font-weight: bold;
        }
        .score-level {
            font-size: 72px;
            font-weight: bold;
            color: """ + color + """;
        }
        .breakdown {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .breakdown-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .breakdown-label { font-weight: bold; color: #555; }
        .breakdown-value { font-size: 24px; color: #333; }
        .progress-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #667eea;
            border-radius: 4px;
            transition: width 0.3s;
        }
        .issue {
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }
        .issue-high { background: #ffe6e6; border-color: #dc3545; }
        .issue-medium { background: #fff3cd; border-color: #ffc107; }
        .issue-low { background: #d4edda; border-color: #28a745; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .badge-high { background: #dc3545; }
        .badge-medium { background: #ffc107; color: #333; }
        .badge-low { background: #28a745; }
        .trend-card {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 15px 0;
        }
        .trend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .trend-item {
            text-align: center;
        }
        .trend-value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .trend-label {
            color: #666;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th { background: #f8f9fa; font-weight: bold; }
        .footer {
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
""")
        
        # Title
        html.append(f"        <h1>🔍 Agent Quality Guard Report</h1>")
        html.append(f"        <p><em>Generated: {timestamp}</em></p>")
        
        if file_path:
            html.append(f"        <p><strong>File:</strong> <code>{file_path}</code></p>")
        
        # Score card
        html.append("""
        <div class="score-card">
            <div>
                <div class="score-value">""")
        html.append(f"{score}/100")
        html.append("""</div>
                <div>Score</div>
            </div>
            <div class="score-level">""")
        html.append(f"{level}")
        html.append("""</div>
        </div>
""")
        
        # Summary
        html.append(f"        <p><strong>Summary:</strong> {summary}</p>")
        
        # Breakdown
        if breakdown:
            html.append("        <h2>📊 Score Breakdown</h2>")
            html.append('        <div class="breakdown">')
            
            for dim, value in breakdown.items():
                weight = {"correctness": 30, "security": 25, "maintainability": 20, 
                          "performance": 15, "coverage": 10}.get(dim, 0)
                html.append(f"""
            <div class="breakdown-item">
                <div class="breakdown-label">{dim.capitalize()} ({weight}%)</div>
                <div class="breakdown-value">{value:.0f}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {value}%"></div>
                </div>
            </div>""")
            
            html.append("        </div>")
        
        # Issues
        html.append("        <h2>🐛 Issues Found</h2>")
        
        if not issues:
            html.append("        <p>✅ No issues detected!</p>")
        else:
            high = [i for i in issues if i.get("severity") == "high"]
            medium = [i for i in issues if i.get("severity") == "medium"]
            low = [i for i in issues if i.get("severity") == "low"]
            
            html.append(f"        <p>Total: <strong>{len(issues)}</strong> issues</p>")
            
            if high:
                html.append("        <h3>🔴 High Priority</h3>")
                for issue in high:
                    line = f" (line {issue['line']})" if issue.get("line") else ""
                    html.append(f"""        <div class="issue issue-high">
            <span class="badge badge-high">{issue['type']}</span>
            {issue['message']}{line}
        </div>""")
            
            if medium:
                html.append("        <h3>🟡 Medium Priority</h3>")
                for issue in medium[:10]:
                    line = f" (line {issue['line']})" if issue.get("line") else ""
                    html.append(f"""        <div class="issue issue-medium">
            <span class="badge badge-medium">{issue['type']}</span>
            {issue['message']}{line}
        </div>""")
            
            if low:
                html.append("        <h3>🟢 Low Priority</h3>")
                for issue in low[:5]:
                    html.append(f"""        <div class="issue issue-low">
            <span class="badge badge-low">{issue['type']}</span>
            {issue['message']}
        </div>""")
        
        # Trends
        html.append("        <h2>📈 Trend Analysis</h2>")
        
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️", 
                       "insufficient_data": "❓"}.get(trend_summary["trend"], "❓")
        
        html.append(f"""        <div class="trend-card">
            <div class="trend-grid">
                <div class="trend-item">
                    <div class="trend-value">{trend_summary['total_runs']}</div>
                    <div class="trend-label">Total Runs</div>
                </div>
                <div class="trend-item">
                    <div class="trend-value">{trend_summary['avg_score']}</div>
                    <div class="trend-label">Avg Score</div>
                </div>
                <div class="trend-item">
                    <div class="trend-value">{trend_summary['avg_level']}</div>
                    <div class="trend-label">Avg Level</div>
                </div>
                <div class="trend-item">
                    <div class="trend-value">{trend_emoji} {trend_summary['trend']}</div>
                    <div class="trend-label">Trend</div>
                </div>
            </div>
        </div>""")
        
        # Footer
        html.append("""
        <div class="footer">
            <p>Report generated by Agent Quality Guard v3.0</p>
        </div>
    </div>
</body>
</html>""")
        
        return "\n".join(html)
    
    # =========================================================================
    # Stage 3: Write (Save to file)
    # =========================================================================
    
    def _write_report(self, content: str, output_path: str, format: str) -> bool:
        """
        Stage 3: Write report to file.
        
        Args:
            content: Report content
            output_path: Output file path
            format: Report format (markdown/html)
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            raise ReporterError(f"Failed to save report: {e}")
    
    # =========================================================================
    # Public API: Generate (uses collect → format → write)
    # =========================================================================
    
    def generate_markdown(
        self,
        result: Dict[str, Any],
        file_path: Optional[str] = None,
        include_trends: bool = True,
        days: int = 30
    ) -> str:
        """Generate Markdown report."""
        # Stage 1: Collect
        data = self._collect_data(result, file_path, days)
        
        # Stage 2: Format
        return self._format_markdown(data)
    
    def generate_html(
        self,
        result: Dict[str, Any],
        file_path: Optional[str] = None,
        include_trends: bool = True,
        days: int = 30
    ) -> str:
        """Generate HTML report."""
        # Stage 1: Collect
        data = self._collect_data(result, file_path, days)
        
        # Stage 2: Format
        return self._format_html(data)
    
    def save_report(
        self,
        content: str,
        output_path: str,
        format: str = "markdown"
    ):
        """Save report to file."""
        return self._write_report(content, output_path, format)
    
    def record_analysis(
        self,
        result: Dict[str, Any],
        file_path: Optional[str] = None
    ):
        """Record analysis for trend tracking."""
        entry = {
            "file": file_path,
            "score": result.get("score", 0),
            "level": result.get("level", "F"),
            "issues": result.get("issues", [])
        }
        
        self.trend_data.add_entry(entry)


# =============================================================================
# Convenience Function
# =============================================================================

def generate_report(
    result: Dict[str, Any],
    format: str = "markdown",
    output: Optional[str] = None,
    file_path: Optional[str] = None,
    include_trends: bool = True,
    days: int = 30
) -> str:
    """
    Convenience function to generate report.
    Uses split stages: collect → format → write.
    
    Args:
        result: Analysis result
        format: "markdown" or "html"
        output: Optional output file path
        file_path: Analyzed file path
        include_trends: Include trend data
        days: Days to include in trends
        
    Returns:
        Report content as string
    """
    reporter = ReportGenerator()
    
    # Stage 1 + 2: Collect and Format
    if format.lower() == "html":
        content = reporter.generate_html(result, file_path, include_trends, days)
    else:
        content = reporter.generate_markdown(result, file_path, include_trends, days)
    
    # Stage 3: Write (if output path provided)
    if output:
        reporter.save_report(content, output, format)
    
    # Record for trends
    if include_trends:
        reporter.record_analysis(result, file_path)
    
    return content