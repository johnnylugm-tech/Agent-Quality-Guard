#!/usr/bin/env python3
"""
Agent Quality Guard - CLI Entry Point
A Python CLI tool for code quality analysis
Version 3.0 - Performance optimized with lazy evaluation and caching
"""

import argparse
import json
import sys
import os
from typing import Optional

from analyzer import analyze_code, InputError, ToolError, ExecutionError, SystemError
from scorer import compute_score, score_from_code


VERSION = "1.0.0"


def read_code_from_file(file_path: str) -> str:
    """Read code from a file"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def output_json(result: dict, pretty: bool = True):
    """Output result as JSON"""
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))


def output_human_readable(result: dict):
    """Output result in human-readable format"""
    score = result.get("score", 0)
    level = result.get("level", "F")
    issues = result.get("issues", [])
    summary = result.get("summary", "")
    
    print(f"\n{'='*50}")
    print(f"  Agent Quality Guard - Code Analysis Results")
    print(f"{'='*50}")
    
    level_colors = {
        "A": "\033[92m",
        "B": "\033[93m",
        "C": "\033[93m",
        "D": "\033[91m",
        "F": "\033[91m",
    }
    reset = "\033[0m"
    
    color = level_colors.get(level, "")
    print(f"\n  Score: {color}{score}/100{reset} (Level: {color}{level}{reset})")
    
    breakdown = result.get("breakdown", {})
    if breakdown:
        print(f"\n  Score Breakdown:")
        for dim, value in breakdown.items():
            dim_name = dim.capitalize()
            weight = {"correctness": 30, "security": 25, "maintainability": 20, 
                     "performance": 15, "coverage": 10}.get(dim, 0)
            bar_len = int(value / 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            print(f"    {dim_name:16} ({weight:2}%): {bar} {value:.0f}")
    
    print(f"\n  Summary:")
    print(f"    {summary}")
    
    if issues:
        high = [i for i in issues if i.get("severity") == "high"]
        medium = [i for i in issues if i.get("severity") == "medium"]
        low = [i for i in issues if i.get("severity") == "low"]
        
        print(f"\n  Issues Found: {len(issues)}")
        if high:
            print(f"    🔴 High:     {len(high)}")
        if medium:
            print(f"    🟡 Medium:   {len(medium)}")
        if low:
            print(f"    🟢 Low:      {len(low)}")
        
        print(f"\n  Issue Details:")
        for issue in high + medium[:5]:
            line_info = f" (line {issue['line']})" if issue.get("line") else ""
            print(f"    [{issue['severity'].upper():6}] {issue['type']:16} {issue['message']}{line_info}")
        
        if len(medium) > 5:
            print(f"    ... and {len(medium) - 5} more medium issues")
    else:
        print(f"\n  ✅ No issues detected!")
    
    print(f"\n{'='*50}\n")


def run_llm_review(code: str, file_path: Optional[str] = None) -> dict:
    """Run LLM-based review"""
    try:
        from llm_judge import llm_review
        context = {}
        if file_path:
            context["file_path"] = file_path
        return llm_review(code, context)
    except ImportError:
        return {"error": "LLM judge not available", "review_score": None}
    except Exception as e:
        return {"error": str(e), "review_score": None}


def show_llm_results(llm_result: dict):
    """Display LLM review results"""
    if "error" in llm_result and not llm_result.get("review_score"):
        print(f"\n  ⚠️ LLM Review: {llm_result.get('error', 'Failed')}")
        return
    
    score = llm_result.get("review_score", 0)
    level = llm_result.get("review_level", "N/A")
    
    print(f"\n  🤖 LLM Review:")
    print(f"    Score: {score}/100 (Level: {level})")
    
    improvements = llm_result.get("improvements", [])
    if improvements:
        print(f"\n    💡 Improvements ({len(improvements)}):")
        for imp in improvements[:3]:
            print(f"      - {imp[:100]}")
    
    security = llm_result.get("security_concerns", [])
    if security:
        print(f"\n    🔒 Security Concerns:")
        for sec in security[:3]:
            print(f"      - {sec[:100]}")


def show_trends(days: int = 30):
    """Show trend statistics"""
    try:
        from reporter import ReportGenerator
        reporter = ReportGenerator()
        summary = reporter.trend_data.get_summary(days=days)
        
        print(f"\n  📈 Trend Analysis (last {days} days):")
        print(f"    Total Runs: {summary['total_runs']}")
        print(f"    Avg Score: {summary['avg_score']}")
        print(f"    Avg Level: {summary['avg_level']}")
        
        trend = summary.get("trend", "unknown")
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️", 
                       "insufficient_data": "❓"}.get(trend, "❓")
        print(f"    Trend: {trend_emoji} {trend}")
    except ImportError:
        pass


def main():
    """Main CLI entry point"""
    # Build main parser with all options for backward compatibility
    parser = argparse.ArgumentParser(
        prog="agent-quality-guard",
        description="Agent Quality Guard v2.0 - Code Quality Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --code "def hello(): print('Hello')"
  %(prog)s --file path/to/code.py
  %(prog)s analyze --file path/to/code.py --llm
  %(prog)s hook install
  %(prog)s trends --days 7
        """
    )
    
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    # Analysis options (backward compatible)
    parser.add_argument("--code", "-c", help="Python code to analyze")
    parser.add_argument("--file", "-f", help="Python file to analyze")
    parser.add_argument("--stdin", "-s", action="store_true", help="Read code from stdin")
    parser.add_argument("--json", "-j", action="store_true", help="Output in JSON format")
    
    # v2.0 features
    parser.add_argument("--llm", "-l", action="store_true", help="Enable LLM review")
    parser.add_argument("--trends", "-t", action="store_true", help="Show trend analysis")
    parser.add_argument("--trends-days", type=int, default=30, help="Days for trend analysis")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--report-format", choices=["markdown", "html"], default="markdown")
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="subcommand", help="Commands")
    
    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code quality")
    analyze_parser.add_argument("--code", "-c", help="Python code to analyze")
    analyze_parser.add_argument("--file", "-f", help="Python file to analyze")
    analyze_parser.add_argument("--stdin", "-s", action="store_true", help="Read from stdin")
    analyze_parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    analyze_parser.add_argument("--llm", "-l", action="store_true", help="Enable LLM review")
    analyze_parser.add_argument("--trends", "-t", action="store_true", help="Show trends")
    analyze_parser.add_argument("--trends-days", type=int, default=30)
    analyze_parser.add_argument("--report", action="store_true", help="Generate report")
    analyze_parser.add_argument("--report-format", choices=["markdown", "html"], default="markdown")
    analyze_parser.add_argument("--output", "-o")
    analyze_parser.add_argument("--verbose", "-v", action="store_true")
    
    # hook subcommand
    hook_parser = subparsers.add_parser("hook", help="Git hook management")
    hook_parser.add_argument("action", choices=["install", "uninstall", "run"])
    hook_parser.add_argument("--root")
    hook_parser.add_argument("--force", "-f", action="store_true")
    hook_parser.add_argument("--all", action="store_true")
    hook_parser.add_argument("--no-fail", action="store_true")
    hook_parser.add_argument("--min-score", type=int, default=60)
    
    # trends subcommand
    trends_parser = subparsers.add_parser("trends", help="Show trend statistics")
    trends_parser.add_argument("--days", type=int, default=30)
    
    args = parser.parse_args()
    
    # Handle subcommands
    if args.subcommand == "analyze":
        code = None
        file_path = args.file
        
        if args.code:
            code = args.code
        elif args.file:
            try:
                code = read_code_from_file(args.file)
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.stdin:
            code = sys.stdin.read()
        
        if not code:
            print("Error: No code provided", file=sys.stderr)
            sys.exit(1)
            
    elif args.subcommand == "hook":
        from git_hook import GitHook
        hook = GitHook(args.root)
        
        if args.action == "install":
            success = hook.install(force=args.force)
            print(f"{'✅ Successfully' if success else '❌ Failed to'} install hook")
            sys.exit(0 if success else 1)
        elif args.action == "uninstall":
            success = hook.uninstall()
            print(f"{'✅ Successfully' if success else '❌ Failed to'} uninstall hook")
            sys.exit(0 if success else 1)
        elif args.action == "run":
            success, results = hook.run(
                staged_only=not args.all,
                fail_on_low_score=not args.no_fail,
                min_score=args.min_score
            )
            print(f"\nChecked {len(results)} file(s)")
            sys.exit(0 if success else 1)
    
    elif args.subcommand == "trends":
        from reporter import ReportGenerator
        reporter = ReportGenerator()
        summary = reporter.trend_data.get_summary(days=args.days)
        
        print(f"\n📈 Agent Quality Guard - Trend Statistics")
        print(f"   (Last {args.days} days)")
        print(f"\n  Total Runs:     {summary['total_runs']}")
        print(f"  Average Score:  {summary['avg_score']}")
        print(f"  Average Level:  {summary['avg_level']}")
        print(f"  Files Analyzed: {summary['files_analyzed']}")
        
        trend = summary.get("trend", "unknown")
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️", 
                       "insufficient_data": "❓"}.get(trend, "❓")
        print(f"  Trend:          {trend_emoji} {trend}")
        print(f"  High Issues:    {summary['high_issues']}")
        sys.exit(0)
    
    else:
        # Legacy mode: analyze directly provided code
        code = None
        file_path = args.file
        
        if args.code:
            code = args.code
        elif args.file:
            try:
                code = read_code_from_file(args.file)
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.stdin:
            code = sys.stdin.read()
        
        if not code:
            print("Error: No code provided", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
    
    # Run analysis (common for analyze subcommand and legacy mode)
    try:
        result = score_from_code(code)
    except InputError as e:
        result = {
            "score": 0, "level": "F", "issues": [],
            "summary": f"Input error: {str(e)}", "error_level": "L1"
        }
    except ToolError as e:
        try:
            result = score_from_code(code)
        except:
            result = {
                "score": 0, "level": "F", "issues": [],
                "summary": f"Tool error: {str(e)}", "error_level": "L2"
            }
    except ExecutionError as e:
        result = {
            "score": 0, "level": "F", "issues": [],
            "summary": f"Execution error: {str(e)}", "error_level": "L3"
        }
    except SystemError as e:
        result = {
            "score": 0, "level": "F", "issues": [],
            "summary": f"System error: {str(e)}", "error_level": "L4"
        }
    except Exception as e:
        result = {
            "score": 0, "level": "F", "issues": [],
            "summary": f"Unexpected error: {str(e)}", "error_level": "L3"
        }
    
    if file_path:
        result["file_path"] = file_path
    
    # Output
    if args.json:
        output_json(result)
    else:
        output_human_readable(result)
    
    # LLM review
    if args.llm:
        llm_result = run_llm_review(code, file_path)
        if not args.json:
            show_llm_results(llm_result)
        else:
            result["llm_review"] = llm_result
            output_json(result)
    
    # Trends
    if args.trends and not args.json:
        show_trends(args.trends_days)
    
    # Report generation
    if args.report:
        try:
            from reporter import generate_report
            report = generate_report(
                result, format=args.report_format,
                output=args.output, file_path=file_path,
                include_trends=args.trends
            )
            if not args.output:
                print(f"\n--- {args.report_format.upper()} Report ---")
                print(report)
            else:
                print(f"Report saved to: {args.output}")
        except ImportError:
            print("Warning: Reporter not available", file=sys.stderr)
    
    # Record for trends
    try:
        from reporter import ReportGenerator
        reporter = ReportGenerator()
        reporter.record_analysis(result, file_path)
    except:
        pass
    
    # Exit code
    if result.get("level") == "F" and "error_level" in result:
        sys.exit(1)
    elif result.get("score", 0) < 60:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()