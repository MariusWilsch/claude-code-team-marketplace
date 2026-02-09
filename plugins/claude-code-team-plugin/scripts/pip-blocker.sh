#!/bin/bash
# Pip Blocker Hook
# Enforces uv usage instead of pip/pip3/uv pip commands.
# Denies pip commands and instructs Claude to use proper uv workflow.

# Read hook input from stdin
input=$(cat)

# Extract the command from tool_input
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Skip gh commands (GitHub CLI) - they may contain pip in comment text
if echo "$command" | grep -qE '^gh\s'; then
  exit 0
fi

# Check if command contains pip install patterns
if echo "$command" | grep -qE '(^|\s|&&|\|)(pip|pip3)\s+install|uv\s+pip\s+install'; then
  cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "pip/pip3/uv pip commands are blocked. Use native uv instead:\n\n**One-off script (temporary deps):**\nuv run --with package script.py\n\n**Project with pyproject.toml:**\nuv add package\nuv run script.py\n\n**Run with multiple temp deps:**\nuv run --with httpx --with rich script.py\n\nNever use pip, pip3, or uv pip. Native uv handles venvs automatically."
  }
}
EOF
  exit 0
fi

# Check if command runs python/python3 directly (should use uv run instead)
# Skip if using uv run (with any flags before python)
if echo "$command" | grep -qE '(^|\s|&&|\|)python3?\s' && \
   ! echo "$command" | grep -qE 'uv run(\s+--?[a-z]|\s+python)' && \
   ! echo "$command" | grep -qE 'python3?\s+(--version|-V)' && \
   ! echo "$command" | grep -qE '(^docker\s|^ssh\s.*docker\s)'; then
  cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Direct python/python3 execution is blocked. Use uv run instead:\n\n**Run script:**\nuv run script.py\n\n**Inline code:**\nuv run python -c \"print('hello')\"\n\n**With temp deps:**\nuv run --with numpy script.py\n\nuv handles venvs and dependencies automatically."
  }
}
EOF
  exit 0
fi
