#!/usr/bin/env python3
"""Calculate Claude Code context usage from conversation JSONL.

Reads the most recent main-chain entry's token usage and returns percentage
against 200k token limit. Skips sidechain entries, API errors, and entries
without usage data.

Usage:
    uv run ~/.claude/lib/context_usage.py <conversation_path>
    uv run ~/.claude/lib/context_usage.py --help

Returns:
    JSON with tokens and percentage, or error message.

Reference: https://codelynx.dev/posts/calculate-claude-code-context
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

MAX_CONTEXT_TOKENS = 200_000


def get_context_usage(transcript_path: str) -> dict:
    """Calculate context usage from conversation JSONL.

    Args:
        transcript_path: Path to conversation JSONL file

    Returns:
        dict with 'tokens', 'percentage', or 'error'
    """
    path = Path(transcript_path)

    if not path.exists():
        return {"error": f"File not found: {transcript_path}"}

    try:
        content = path.read_text()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    lines = content.strip().split("\n")
    if not lines or lines == [""]:
        return {"tokens": 0, "percentage": 0}

    most_recent_usage = None
    most_recent_timestamp = None

    for line in lines:
        if not line.strip():
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Skip if no usage data
        message = data.get("message", {})
        if not message or not message.get("usage"):
            continue

        # Skip sidechain entries (agent calls)
        if data.get("isSidechain") is True:
            continue

        # Skip API error messages
        if data.get("isApiErrorMessage") is True:
            continue

        # Skip entries without timestamp
        timestamp_str = data.get("timestamp")
        if not timestamp_str:
            continue

        try:
            entry_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        if most_recent_timestamp is None or entry_time > most_recent_timestamp:
            most_recent_timestamp = entry_time
            most_recent_usage = message.get("usage")

    if not most_recent_usage:
        return {"tokens": 0, "percentage": 0}

    # Sum all input token types
    input_tokens = most_recent_usage.get("input_tokens", 0) or 0
    cache_read = most_recent_usage.get("cache_read_input_tokens", 0) or 0
    cache_creation = most_recent_usage.get("cache_creation_input_tokens", 0) or 0

    total_tokens = input_tokens + cache_read + cache_creation
    percentage = min(100, round((total_tokens / MAX_CONTEXT_TOKENS) * 100))

    return {
        "tokens": total_tokens,
        "percentage": percentage
    }


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Claude Code context usage from conversation JSONL"
    )
    parser.add_argument(
        "conversation_path",
        nargs="?",
        help="Path to conversation JSONL file"
    )

    args = parser.parse_args()

    if not args.conversation_path:
        parser.print_help()
        sys.exit(1)

    result = get_context_usage(args.conversation_path)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
