#!/bin/bash
# post-git-push-context-check.sh - Context gate check on git push
#
# PostToolUse hook that runs after git push to check context usage.
# Outputs info normally, warning at ≥60% to signal graceful exit consideration.
# AI has final say - this is informational, not blocking.
#
# Refs: DaveX2001/claude-code-improvements#287

set -e

# Read hook input from stdin
INPUT=$(cat)

# Extract command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Only process git push commands (direct or chained)
if [[ ! "$COMMAND" =~ git\ push ]]; then
    exit 0
fi

# Get transcript path from hook input
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)

if [[ -z "$TRANSCRIPT_PATH" || ! -f "$TRANSCRIPT_PATH" ]]; then
    exit 0
fi

# Get plugin root (set by Claude Code when running plugin hooks)
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"

# Run context usage calculation
RESULT=$(uv run "$PLUGIN_ROOT/lib/context_usage.py" "$TRANSCRIPT_PATH" 2>/dev/null)

if [[ -z "$RESULT" ]]; then
    exit 0
fi

# Parse result
PERCENTAGE=$(echo "$RESULT" | jq -r '.percentage // 0' 2>/dev/null)
TOKENS=$(echo "$RESULT" | jq -r '.tokens // 0' 2>/dev/null)

# Format token count for readability
if [[ "$TOKENS" -ge 1000 ]]; then
    TOKENS_DISPLAY="$((TOKENS / 1000))k"
else
    TOKENS_DISPLAY="$TOKENS"
fi

# Output JSON with additionalContext so Claude sees the context percentage
# Plain echo only goes to verbose mode; JSON additionalContext reaches Claude
if [[ "$PERCENTAGE" -ge 60 ]]; then
    # Warning at ≥60% - signal graceful exit consideration
    MESSAGE="⚠️ CONTEXT GATE: ${PERCENTAGE}% (${TOKENS_DISPLAY}/200k tokens). Consider graceful exit after completing current task."
elif [[ "$PERCENTAGE" -ge 30 ]]; then
    # Info for notable percentages
    MESSAGE="Context: ${PERCENTAGE}% (${TOKENS_DISPLAY}/200k)"
else
    # Below 30% - no output needed
    exit 0
fi

# Output structured JSON that Claude Code injects into context
jq -n --arg msg "$MESSAGE" '{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": $msg
  }
}'

exit 0
