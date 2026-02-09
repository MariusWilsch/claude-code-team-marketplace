#!/bin/bash
# JSONL Blocker Hook
# Blocks raw Read on conversation JSONL files.
# Redirects to conversation-reader skill for proper extraction.

# Read hook input from stdin
input=$(cat)

# Extract the file_path from tool_input
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Check if file_path matches conversation JSONL pattern
if echo "$file_path" | grep -qE '\.claude/projects/.*\.jsonl$'; then
  cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Raw JSONL file read is blocked. Invoke Skill(conversation-reader) for extraction commands."
  }
}
EOF
  exit 0
fi
