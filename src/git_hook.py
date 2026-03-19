"""
Agent Quality Guard - Git Hook Integration v3.0
Pre-commit hook for automatic code quality checks
"""

import os
import sys
import subprocess
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class GitHookError(Exception):
    """Base exception for git hook errors"""
    pass


class GitHookConfigError(GitHookError):
    """Configuration error"""
    pass


class GitHookInstallError(GitHookError):
    """Installation error"""
    pass


class GitHookRunError(GitHookError):
    """Runtime error during hook execution"""
    pass


# =============================================================================
# Utility Functions with Error Handling
# =============================================================================

def get_staged_files(staged: bool = True) -> List[str]:
    """
    Get list of staged Python files.
    
    Args:
        staged: If True, get staged files. If False, get all changed files.
        
    Returns:
        List of file paths
    """
    try:
        if staged:
            # Get staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # Get changed files (staged + unstaged)
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # Parse status line (e.g., "M  path/to/file.py")
                if len(line) > 3:
                    files.append(line[3:])
        
        # Filter for Python files only
        py_files = [f for f in files if f.endswith('.py')]
        return py_files
        
    except subprocess.CalledProcessError as e:
        raise GitHookRunError(f"Failed to get git files: {e}")
    except FileNotFoundError:
        raise GitHookRunError("Git not found. Make sure git is installed.")


def get_file_diff(file_path: str) -> str:
    """Get the diff for a specific file."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def get_file_content(file_path: str) -> str:
    """Get current file content (staged version)."""
    try:
        # Try to get staged version first
        result = subprocess.run(
            ["git", "show", f":{file_path}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        
        # Fall back to working directory version
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        # Last resort: read from filesystem
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""


# =============================================================================
# Git Hook Manager v3.0 - Split into Check, Create, Register
# =============================================================================

class GitHook:
    """
    Git hook manager for pre-commit integration.
    
    Usage:
        # Install hook
        git_hook = GitHook()
        git_hook.install()
        
        # Run hook manually
        git_hook.run()
    """
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.git_dir = self.project_root / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        self.hook_script = self.hooks_dir / "pre-commit"
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return self.git_dir.exists()
    
    def is_installed(self) -> bool:
        """Check if pre-commit hook is already installed."""
        if not self.hook_script.exists():
            return False
        
        # Check if our hook is in there
        try:
            with open(self.hook_script, 'r') as f:
                content = f.read()
                return "agent-quality-guard" in content or "quality-guard" in content
        except:
            return False
    
    # =========================================================================
    # Stage 1: Check (Pre-installation validation)
    # =========================================================================
    
    def _check_installation_prerequisites(self) -> Dict[str, Any]:
        """
        Stage 1: Check prerequisites before installation.
        
        Returns:
            Dict with check results: {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []
        
        # Check if it's a git repository
        if not self.is_git_repo():
            errors.append("Not a git repository")
        
        # Check if hook already exists
        if self.is_installed():
            warnings.append("Hook already installed (use force=True to replace)")
        
        # Check if we can write to hooks directory
        if self.hooks_dir.exists():
            if not os.access(self.hooks_dir, os.W_OK):
                errors.append(f"Hooks directory not writable: {self.hooks_dir}")
        else:
            # Try to create it
            try:
                self.hooks_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create hooks directory: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    # =========================================================================
    # Stage 2: Create (Generate hook content)
    # =========================================================================
    
    def _create_hook_content(self) -> str:
        """
        Stage 2: Create hook script content.
        
        Returns:
            Hook script content as string
        """
        # Get the path to our analyzer
        src_dir = self.project_root / "src"
        if not src_dir.exists():
            # Maybe it's installed as a package
            try:
                import agent_quality_guard
                package_dir = Path(agent_quality_guard.__file__).parent
                src_dir = package_dir
            except ImportError:
                src_dir = self.project_root
        
        hook_content = f"""#!/bin/bash
# Agent Quality Guard - Pre-commit Hook
# This hook runs code quality checks before commit

AGENT_QUALITY_GUARD_DIR="{src_dir}"
PYTHON="$(command -v python3 || command -v python)"

# Get list of staged Python files
STAGED_FILES=$($PYTHON -c "
import subprocess
import sys
try:
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True, check=True
    )
    files = [f.strip() for f in result.stdout.split('\\n') if f.endswith('.py')]
    print(' '.join(files))
except:
    print('')
")

if [ -z "$STAGED_FILES" ]; then
    echo 'No Python files to check'
    exit 0
fi

echo 'Running Agent Quality Guard...'
echo 'Checking: ${{STAGED_FILES}}'

# Run quality check on each file
EXIT_CODE=0
for FILE in $STAGED_FILES; do
    RESULT=$($PYTHON -m agent_quality_guard.main --file "$FILE" 2>&1) || EXIT_CODE=1
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo "$RESULT"
        echo ""
        echo "Commit blocked due to code quality issues in $FILE"
        echo "Fix the issues or use --no-verify to skip"
        exit 1
    fi
done

echo '✓ All checks passed'
exit 0
"""
        
        return hook_content
    
    # =========================================================================
    # Stage 3: Register (Write hook to filesystem)
    # =========================================================================
    
    def _register_hook(self, content: str) -> bool:
        """
        Stage 3: Register (write) hook to filesystem.
        
        Args:
            content: Hook script content
            
        Returns:
            True if successful
        """
        try:
            with open(self.hook_script, 'w') as f:
                f.write(content)
            
            # Make executable
            os.chmod(self.hook_script, 0o755)
            return True
            
        except Exception as e:
            raise GitHookInstallError(f"Failed to install hook: {e}")
    
    # =========================================================================
    # Public API: Install (uses check → create → register)
    # =========================================================================
    
    def install(self, force: bool = False) -> bool:
        """
        Install pre-commit hook.
        Uses split stages: check → create → register.
        
        Args:
            force: If True, replace existing hook
            
        Returns:
            True if successful
        """
        # Stage 1: Check prerequisites
        check_result = self._check_installation_prerequisites()
        
        if not check_result["valid"]:
            raise GitHookConfigError("; ".join(check_result["errors"]))
        
        if check_result["warnings"] and not force:
            print(f"Warnings: {check_result['warnings']}")
        
        # Stage 2: Create hook content
        hook_content = self._create_hook_content()
        
        # Stage 3: Register hook
        return self._register_hook(hook_content)
    
    def uninstall(self) -> bool:
        """Remove pre-commit hook."""
        if not self.hook_script.exists():
            return True
        
        try:
            # Read current content
            with open(self.hook_script, 'r') as f:
                content = f.read()
            
            # Check if it's our hook
            if "agent-quality-guard" not in content:
                print("Hook appears to be from another tool. Manual removal required.")
                return False
            
            # Remove the file
            self.hook_script.unlink()
            return True
            
        except Exception as e:
            raise GitHookError(f"Failed to uninstall hook: {e}")
    
    def run(
        self, 
        staged_only: bool = True,
        fail_on_low_score: bool = True,
        min_score: int = 60
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Run pre-commit checks.
        
        Args:
            staged_only: Only check staged files
            fail_on_low_score: Exit with error if score is low
            min_score: Minimum acceptable score
            
        Returns:
            (success: bool, results: list)
        """
        # Import here to avoid circular imports
        try:
            from scorer import score_from_code
        except ImportError:
            # Try alternative import
            sys.path.insert(0, str(self.project_root / "src"))
            from scorer import score_from_code
        
        # Get files to check
        try:
            files = get_staged_files(staged=staged_only)
        except GitHookRunError as e:
            print(f"Warning: {e}")
            files = []
        
        if not files:
            print("No Python files to check")
            return True, []
        
        results = []
        all_passed = True
        
        for file_path in files:
            print(f"\nChecking: {file_path}")
            
            try:
                # Get file content
                code = get_file_content(file_path)
                
                if not code:
                    print(f"  Skipping empty file: {file_path}")
                    continue
                
                # Run analysis
                result = score_from_code(code)
                
                # Store result
                results.append({
                    "file": file_path,
                    "score": result.get("score", 0),
                    "level": result.get("level", "F"),
                    "issues": result.get("issues", [])
                })
                
                # Print summary
                score = result.get("score", 0)
                level = result.get("level", "F")
                issue_count = len(result.get("issues", []))
                
                print(f"  Score: {score}/100 (Level: {level})")
                print(f"  Issues: {issue_count}")
                
                # Check if should fail
                if fail_on_low_score and score < min_score:
                    print(f"  ❌ FAILED: Score below minimum ({min_score})")
                    all_passed = False
                    
                    # Show critical issues
                    issues = result.get("issues", [])
                    high_issues = [i for i in issues if i.get("severity") == "high"]
                    for issue in high_issues[:3]:
                        print(f"    - {issue.get('message', 'Unknown issue')}")
                        
                else:
                    print(f"  ✓ Passed")
                    
            except Exception as e:
                print(f"  Error analyzing {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "error": str(e),
                    "score": 0,
                    "level": "F"
                })
                all_passed = False
        
        return all_passed, results


# =============================================================================
# Convenience Functions
# =============================================================================

def install_hook(project_root: Optional[str] = None, force: bool = False) -> bool:
    """Convenience function to install pre-commit hook."""
    hook = GitHook(project_root)
    return hook.install(force=force)


def run_hook(project_root: Optional[str] = None, **kwargs) -> Tuple[bool, List[Dict[str, Any]]]:
    """Convenience function to run pre-commit checks."""
    hook = GitHook(project_root)
    return hook.run(**kwargs)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Quality Guard Git Hook")
    parser.add_argument("command", choices=["install", "uninstall", "run"],
                        help="Command to execute")
    parser.add_argument("--root", help="Project root directory")
    parser.add_argument("--force", action="store_true", help="Force install")
    parser.add_argument("--all", action="store_true", 
                        help="Check all changed files, not just staged")
    
    args = parser.parse_args()
    
    hook = GitHook(args.root)
    
    if args.command == "install":
        success = hook.install(force=args.force)
        print(f"{'Successfully' if success else 'Failed to'} install hook")
        
    elif args.command == "uninstall":
        success = hook.uninstall()
        print(f"{'Successfully' if success else 'Failed to'} uninstall hook")
        
    elif args.command == "run":
        success, results = hook.run(staged_only=not args.all)
        print(f"\nChecked {len(results)} files")
        sys.exit(0 if success else 1)