#!/usr/bin/env python3
"""Onboarding bootstrap script - consolidates session context into single JSON output.

Replaces onboarding_bootstrap.sh with Python for cleaner JSON handling.

Outputs:
    JSON with session metadata, validated label, and issue list for the detected project.

Usage:
    uv run ~/.claude/lib/onboarding_bootstrap.py
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str], capture: bool = True) -> str | None:
    """Run command and return stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_ssh_hosts() -> str:
    """Parse SSH config for host names."""
    ssh_config = Path.home() / ".ssh" / "config"
    if not ssh_config.exists():
        return "none"

    try:
        content = ssh_config.read_text()
        hosts = re.findall(r"^Host\s+(\S+)", content, re.MULTILINE)
        hosts = [h for h in hosts if "*" not in h]  # Exclude wildcards
        return ",".join(hosts) if hosts else "none"
    except Exception:
        return "none"


def get_gh_extensions() -> str:
    """Get installed GitHub CLI extensions."""
    if not shutil.which("gh"):
        return "none"

    output = run_cmd(["gh", "extension", "list"])
    if not output:
        return "none"

    # Format: gh repo  name  version
    extensions = [line.split()[1] if len(line.split()) > 1 else ""
                  for line in output.splitlines()]
    extensions = [e for e in extensions if e]
    return ",".join(extensions) if extensions else "none"


def get_available_clis() -> str:
    """Check which CLIs are available."""
    clis = []
    for cli in ["vercel", "gh", "docker", "node", "npm", "uv"]:
        if shutil.which(cli):
            clis.append(cli)
    return ",".join(clis) if clis else "none"


def validate_label(label: str) -> bool | None:
    """Check if label exists in DaveX2001/deliverable-tracking repo."""
    if not label or not shutil.which("gh"):
        return None

    output = run_cmd([
        "gh", "label", "list",
        "--repo", "DaveX2001/deliverable-tracking",
        "--json", "name",
        "--jq", ".[].name"
    ])

    if output is None:
        return None

    labels = output.splitlines()
    return label in labels


def get_issue_list(label: str) -> list[dict]:
    """Fetch actionable issues for a label from deliverable-tracking repo."""
    if not label or not shutil.which("gh"):
        return []

    output = run_cmd([
        "gh", "issue", "list",
        "--repo", "DaveX2001/deliverable-tracking",
        "--label", label,
        "--state", "open",
        "--json", "number,title,labels"
    ])

    if not output:
        return []

    try:
        issues = json.loads(output)
        result = []
        for issue in issues:
            # Filter to to-do or in-progress only
            label_names = [lbl["name"] for lbl in issue.get("labels", [])]
            status = None
            if "to-do" in label_names:
                status = "to-do"
            elif "in-progress" in label_names:
                status = "in-progress"

            if status:
                result.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "status": status
                })
        return result
    except json.JSONDecodeError:
        return []


def main():
    # Get conversation path from env
    conv_path = os.environ.get("CLAUDE_CONVERSATION_PATH", "")

    # Detect environment
    pwd_path = Path.cwd()
    # Detect local vs remote: local if path starts with user's home directory
    home_dir = str(Path.home())
    env_type = "Local" if str(pwd_path).startswith(home_dir) or str(pwd_path).startswith("/mnt/") else "Remote"

    # Extract folder name and detect label
    folder_name = pwd_path.name
    detected_label = ""
    if "__" in folder_name:
        detected_label = folder_name.split("__")[0]

    # Get SSH hosts (always parse - useful for context regardless of environment)
    ssh_hosts = get_ssh_hosts()

    # Get GH extensions
    gh_extensions = get_gh_extensions()

    # Get available CLIs
    clis = get_available_clis()

    # Validate label and fetch issues
    validated_label = validate_label(detected_label)
    issue_list = get_issue_list(detected_label) if validated_label else []

    # Output JSON
    output = {
        "conversation_path": conv_path,
        "environment": env_type,
        "folder_name": folder_name,
        "detected_label": detected_label,
        "validated_label": validated_label,
        "issue_list": issue_list,
        "ssh_hosts": ssh_hosts,
        "gh_extensions": gh_extensions,
        "clis": clis
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
