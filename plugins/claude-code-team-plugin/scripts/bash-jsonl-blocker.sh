#!/bin/bash
# Bash JSONL Blocker Hook
# Blocks ANY Bash command that references conversation JSONL files.
# Forces use of conversation-reader skill for proper extraction.

# Read hook input from stdin
input=$(cat)

# Extract the command from tool_input
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Allow extract_conversation.py (the conversation-reader implementation)
if echo "$command" | grep -qE 'extract_conversation\.py'; then
  exit 0
fi

# Allow context_usage.py (Ralph context gate check)
if echo "$command" | grep -qE 'context_usage\.py'; then
  exit 0
fi

# Allow gh issue commands (JSONL path in body is fine - just a reference for traceability)
if echo "$command" | grep -qE '^gh issue (comment|create|edit)'; then
  exit 0
fi

# Block ANY command that references .claude/projects/*.jsonl
if echo "$command" | grep -qE '\.claude/projects/.*\.jsonl'; then
  cat << 'EOF'
{
  "decision": "block",
  "reason": "Direct access to conversation JSONL is blocked. Invoke Skill(conversation-reader) for proper extraction."
}
EOF
  exit 0
fi

# Allow command
exit 0
