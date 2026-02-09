#!/bin/bash
# Block gh issue create - must use deliverable-tracking skill
# This ensures issues are created with proper tracking structure
# EXCEPTION: Allow calls from create_tracking_issue.sh (plugin or local path)

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Allow if command uses create_tracking_issue.sh (plugin or local path)
if echo "$command" | grep -qE 'create_tracking_issue\.sh'; then
  exit 0
fi

# Block direct gh issue create - must use deliverable-tracking skill
if echo "$command" | grep -qE '^gh\s+issue\s+create'; then
  cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "gh issue create is blocked. Use Skill(claude-code-team-plugin:deliverable-tracking) or Skill(deliverable-tracking) to create issues with proper tracking structure."
  }
}
EOF
  exit 0
fi
