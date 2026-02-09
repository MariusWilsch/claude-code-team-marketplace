#!/bin/bash
# Git Commit Guard - Requires issue reference in commit messages
# Workaround for hookify plugin output not being visible to AI
# See: https://github.com/DaveX2001/claude-code-improvements/issues/125

# Read hook input from stdin
input=$(cat)

# Extract the bash command from the JSON
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only validate git commit commands
if [[ ! "$command" =~ git\ commit ]]; then
  exit 0  # Not a git commit, allow it
fi

# Check if the command contains a GitHub issue reference (any repo)
# Pattern: Refs {owner}/{repo}#{number}
if [[ "$command" =~ Refs\ [a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+#[0-9]+ ]]; then
  exit 0  # Has required reference, allow it
fi

# Blocked: git commit without required reference
cat >&2 << 'EOF'
**[require-issue-ref]**
**Issue reference required in commit message.**

This session is linked to an issue. All commits must include:

```
Refs {owner}/{repo}#N
```

Examples:
- Refs DaveX2001/deliverable-tracking#227
- Refs DaveX2001/claude-code-improvements#111
- Refs MariusWilsch/some-repo#42

Add this to your commit message before proceeding.
EOF

exit 2  # Exit code 2 blocks the tool call
