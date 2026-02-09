#!/usr/bin/env python3
"""PreToolUse hook for nuanced Bash command permissions.

Handles commands that need finer control than settings.json allow/deny lists:
- gh api: Allow GET, ask for POST/PUT/PATCH/DELETE
- gh issue edit: Allow label-only ops, ask for title/body/assignee changes
- git -c: Allow by default, ask for risky operations

Exit behavior:
- Exit 0 with JSON {"permissionDecision": "allow"} = auto-approve
- Exit 0 without JSON = fall through to settings.json behavior (ask)
"""
import json
import sys
import re


def allow(reason: str):
    """Auto-approve with reason."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def ask():
    """Fall through to settings.json ask behavior."""
    sys.exit(0)


def check_gh_api(command: str):
    """Handle gh api commands: allow GET, ask for write operations."""
    write_patterns = [
        r"--method\s+DELETE",
        r"--method\s+PATCH",
        r"--method\s+POST",
        r"--method\s+PUT",
        r"-X\s+DELETE",
        r"-X\s+PATCH",
        r"-X\s+POST",
        r"-X\s+PUT",
    ]

    if any(re.search(p, command, re.IGNORECASE) for p in write_patterns):
        ask()

    allow("Read-only gh api operation (GET)")


def check_git_c(command: str):
    """Handle git -c commands: allow by default, ask for risky operations."""
    risky_patterns = [
        r'reset\s+--hard',
        r'push\s+.*(-f|--force)',
        r'commit\s+.*--amend',
        r'clean\s+-[fd]',
        r'\brebase\b',
        r'branch\s+-[dD]',
        r'stash\s+(drop|clear)',
    ]

    if any(re.search(p, command) for p in risky_patterns):
        ask()

    allow("Safe git -c operation")


def check_gh_issue_edit(command: str):
    """Handle gh issue edit: allow label-only ops, ask for others."""
    # Label-only patterns (safe operations)
    label_patterns = [
        r'--add-label',
        r'--remove-label',
    ]

    # Non-label patterns (need confirmation)
    non_label_patterns = [
        r'--title',
        r'--body',
        r'--assignee',
        r'--milestone',
        r'--project',
    ]

    has_label_op = any(re.search(p, command) for p in label_patterns)
    has_non_label_op = any(re.search(p, command) for p in non_label_patterns)

    # If only label operations, auto-allow
    if has_label_op and not has_non_label_op:
        allow("Label-only gh issue edit")

    # Otherwise fall through to ask
    ask()


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")

    # Route to appropriate handler
    if "gh api" in command:
        check_gh_api(command)
    elif "gh issue edit" in command:
        check_gh_issue_edit(command)
    elif re.search(r'^git\s+-c\b', command):
        check_git_c(command)

    # Not a command we handle - fall through
    sys.exit(0)


if __name__ == "__main__":
    main()
