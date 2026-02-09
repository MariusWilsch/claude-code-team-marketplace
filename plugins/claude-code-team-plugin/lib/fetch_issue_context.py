#!/usr/bin/env python3
"""Fetch GitHub issue context with body, comments, status, worktree, ancestors, and tracking.

Replaces fetch_issue_context.sh with Python for JSON output.

Usage:
    uv run ~/.claude/lib/fetch_issue_context.py <issue_number> [repo]
    uv run ~/.claude/lib/fetch_issue_context.py <issue_number> --repo <repo>

Examples:
    fetch_issue_context.py 377                                    # Uses default repo
    fetch_issue_context.py 89 DaveX2001/claude-code-improvements  # Positional repo
    fetch_issue_context.py 89 --repo DaveX2001/claude-code-improvements

Default repo: DaveX2001/deliverable-tracking

Output fields:
    - issue, repo, title, state, status, labels, body, comments
    - worktree: path to issue worktree or null
    - ancestors: list of parent issues with their worktree status (via GraphQL)
    - tracking: MISSING | NO_AC | HAS_AC
"""

import argparse
import json
import os
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str], cwd: str | None = None) -> str | None:
    """Run command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=cwd
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_issue_data(issue: str, repo: str) -> dict | None:
    """Fetch issue data from GitHub."""
    output = run_cmd([
        "gh", "issue", "view", issue,
        "--repo", repo,
        "--json", "title,state,body,labels,comments"
    ])

    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def get_parent_issue(issue: str, repo: str) -> dict | None:
    """Get parent issue via GraphQL API.

    Returns dict with number, title, state if parent exists, else None.
    """
    owner, name = repo.split("/")
    query = f'''
    {{
      repository(owner: "{owner}", name: "{name}") {{
        issue(number: {issue}) {{
          parent {{
            number
            title
            state
          }}
        }}
      }}
    }}
    '''

    output = run_cmd(["gh", "api", "graphql", "-f", f"query={query}"])
    if not output:
        return None

    try:
        data = json.loads(output)
        parent = data.get("data", {}).get("repository", {}).get("issue", {}).get("parent")
        if parent:
            return {
                "number": parent["number"],
                "title": parent["title"],
                "state": parent["state"].lower()
            }
        return None
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def get_ancestors(issue: str, repo: str) -> list[dict]:
    """Traverse ancestor chain via GraphQL, collecting worktree info for each.

    Returns list of ancestors from immediate parent to root, each with:
    - number: issue number
    - title: issue title
    - state: open/closed
    - worktree: path or null
    """
    ancestors = []
    current = issue

    # Traverse up to 10 levels (safety limit)
    for _ in range(10):
        parent = get_parent_issue(current, repo)
        if not parent:
            break

        # Check worktree for this ancestor
        worktree = detect_worktree(str(parent["number"]))

        ancestors.append({
            "number": parent["number"],
            "title": parent["title"],
            "state": parent["state"],
            "worktree": worktree
        })

        current = str(parent["number"])

    return ancestors


def detect_worktree(issue: str) -> str | None:
    """Check if a worktree exists for this issue."""
    output = run_cmd(["git", "worktree", "list"])
    if not output:
        return None

    for line in output.splitlines():
        if f"issue-{issue}" in line:
            # Format: /path/to/worktree  abc1234 [branch-name]
            parts = line.split()
            if parts:
                return parts[0]  # Return the path

    return None


def check_tracking_status(issue: str) -> str:
    """Check tracking file status for this issue.

    Returns:
        MISSING: No tracking file
        NO_AC: File exists but no AC section
        HAS_AC: File exists with AC section
    """
    tracking_file = Path.cwd() / ".claude" / "tracking" / f"issue-{issue}" / "tracking.md"

    if not tracking_file.exists():
        return "MISSING"

    try:
        content = tracking_file.read_text()
        if "## Acceptance Criteria" in content:
            return "HAS_AC"
        return "NO_AC"
    except Exception:
        return "MISSING"


def format_comments(comments: list[dict], limit_recent: int = 5, limit_history: int = 15) -> dict:
    """Split comments into history and recent.

    Args:
        comments: List of comment objects from GitHub API
        limit_recent: Number of comments to include in recent
        limit_history: Max older comments to include in history
    """
    # Limit to last 20 comments total to avoid truncation
    comments = comments[-20:] if len(comments) > 20 else comments

    history = []
    recent = []

    if len(comments) > limit_recent:
        history_comments = comments[:-limit_recent][-limit_history:]
        recent_comments = comments[-limit_recent:]
    else:
        history_comments = []
        recent_comments = comments

    for c in history_comments:
        history.append({
            "author": c.get("author", {}).get("login", "unknown"),
            "date": c.get("createdAt", ""),
            "body": c.get("body", "")
        })

    for c in recent_comments:
        recent.append({
            "author": c.get("author", {}).get("login", "unknown"),
            "date": c.get("createdAt", ""),
            "body": c.get("body", "")
        })

    return {
        "count": len(comments),
        "history": history,
        "recent": recent
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub issue context")
    parser.add_argument("issue", help="Issue number")
    parser.add_argument("repo_positional", nargs="?", help="Repository (positional)")
    parser.add_argument("--repo", dest="repo_flag", help="Repository (flag)")

    args = parser.parse_args()

    # Determine repo (flag takes precedence over positional)
    repo = args.repo_flag or args.repo_positional or "DaveX2001/deliverable-tracking"
    issue = args.issue

    # Fetch issue data
    data = get_issue_data(issue, repo)
    if not data:
        print(json.dumps({"error": f"Failed to fetch issue #{issue} from {repo}"}))
        return

    # Extract status from labels
    label_names = [lbl["name"] for lbl in data.get("labels", [])]
    status = None
    if "to-do" in label_names:
        status = "to-do"
    elif "in-progress" in label_names:
        status = "in-progress"
    elif "blocked" in label_names:
        status = "blocked"

    # Detect worktree
    worktree = detect_worktree(issue)

    # Get ancestor chain with worktrees
    ancestors = get_ancestors(issue, repo)

    # Check tracking status
    tracking = check_tracking_status(issue)

    # Format output
    output = {
        "issue": int(issue),
        "repo": repo,
        "title": data.get("title", ""),
        "state": data.get("state", ""),
        "status": status,
        "labels": label_names,
        "body": data.get("body", ""),
        "comments": format_comments(data.get("comments", [])),
        "worktree": worktree,
        "ancestors": ancestors,
        "tracking": tracking
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
