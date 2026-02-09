#!/bin/bash
# Create tracking folder structure for an issue
# Usage: create_tracking_file.sh <issue_number> <title>
# Returns: path to tracking.md
#
# Creates:
#   .claude/tracking/issue-{N}/
#   ├── tracking.md        # DoD + AC
#   ├── verification.jsonl # Decision trace (empty initially)
#   └── artifacts/         # Screenshots for failures

set -e

ISSUE_NUM="$1"
TITLE="$2"

if [[ -z "$ISSUE_NUM" ]] || [[ -z "$TITLE" ]]; then
    echo "Usage: create_tracking_file.sh <issue_number> <title>" >&2
    exit 1
fi

# Create subfolder structure
TRACKING_DIR=.claude/tracking/issue-${ISSUE_NUM}
mkdir -p "$TRACKING_DIR/artifacts"

# Create tracking.md
TRACKING_FILE="$TRACKING_DIR/tracking.md"
cat > "$TRACKING_FILE" << EOF
# Issue #${ISSUE_NUM}: ${TITLE}

## Definition of Done
- [ ]

## Acceptance Criteria
<!-- Defined via /rubber-duck -->

<!-- Verify Phase: Use ac-verify skill for schema + workflow -->
EOF

# Create empty verification.jsonl
touch "$TRACKING_DIR/verification.jsonl"

echo "$TRACKING_FILE"
