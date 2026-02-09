#!/bin/bash
# Wrapper script for gh issue create
# Used by deliverable-tracking skill to bypass the command-blocker hook
#
# Usage: create_tracking_issue.sh [gh issue create args...]
# Example: create_tracking_issue.sh --repo DaveX2001/deliverable-tracking --title "My Issue" --body "Content" --label "client"
#
# This script exists because:
# 1. gh issue create is blocked by command-blocker.sh hook
# 2. The hook enforces using deliverable-tracking skill for issue creation
# 3. The skill uses this wrapper to actually create the issue
# 4. This wrapper is allowlisted in settings.json

# Pass all arguments directly to gh issue create and capture output
output=$(gh issue create "$@" 2>&1)
exit_code=$?

echo "$output"

if [ $exit_code -eq 0 ]; then
  echo ""
  echo "📋 IMPORTANT: Share the issue link above with the user."
fi

exit $exit_code
