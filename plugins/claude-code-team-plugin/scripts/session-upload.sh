#!/bin/bash
# session-upload.sh - Upload conversation JSONL at session end
# Issue: #348 - Session End Hook: Conversation Upload & Persistence
#
# Receives JSON via stdin with transcript_path field.
# Copies conversation to plugin repo projects/ folder and pushes.
# Always exits 0 to not block session termination.

set -o pipefail

# Find destination repo - check dev path first, then derive from CLAUDE_PLUGIN_ROOT
DEV_PATH="$HOME/Documents/projects/claude-code-team-plugin"
SEARCHED_PATHS="$DEV_PATH"

if [ -d "$DEV_PATH/.git" ]; then
    DEST_REPO="$DEV_PATH"
elif [ -n "$CLAUDE_PLUGIN_ROOT" ] && [[ "$CLAUDE_PLUGIN_ROOT" == *"/cache/"* ]]; then
    # Running from marketplace cache - extract marketplace name and find marketplace repo
    # Cache path format: ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/
    MARKETPLACE_NAME=$(echo "$CLAUDE_PLUGIN_ROOT" | sed 's|.*/cache/\([^/]*\)/.*|\1|')
    MARKETPLACE_REPO="$HOME/.claude/plugins/marketplaces/$MARKETPLACE_NAME"
    SEARCHED_PATHS="$SEARCHED_PATHS, $MARKETPLACE_REPO"

    if [ -d "$MARKETPLACE_REPO/.git" ]; then
        DEST_REPO="$MARKETPLACE_REPO"
    fi
fi

if [ -z "$DEST_REPO" ]; then
    echo "session-upload: No plugin repo found. Searched: $SEARCHED_PATHS" >&2
    echo "session-upload: Set CLAUDE_PLUGIN_ROOT or ensure dev path exists" >&2
    exit 1
fi

# Read JSON input from stdin
INPUT=$(cat)

# Extract transcript_path from JSON
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ]; then
    echo "session-upload: No transcript_path in input" >&2
    exit 0
fi

# Verify source file exists
if [ ! -f "$TRANSCRIPT_PATH" ]; then
    echo "session-upload: Transcript file not found: $TRANSCRIPT_PATH" >&2
    exit 0
fi

# Verify destination repo exists
if [ ! -d "$DEST_REPO/.git" ]; then
    echo "session-upload: Destination repo not found: $DEST_REPO" >&2
    exit 0
fi

# Compute relative path: strip ~/.claude/projects/ prefix
# Example: ~/.claude/projects/-Users-verdant-.../{uuid}.jsonl -> -Users-verdant-.../{uuid}.jsonl
RELATIVE_PATH="${TRANSCRIPT_PATH#$HOME/.claude/projects/}"

# Destination: projects/{relative_path}
DEST_PATH="$DEST_REPO/projects/$RELATIVE_PATH"
DEST_DIR=$(dirname "$DEST_PATH")

# Create destination directory
mkdir -p "$DEST_DIR" 2>/dev/null || {
    echo "session-upload: Failed to create directory: $DEST_DIR" >&2
    exit 0
}

# Copy conversation file
cp "$TRANSCRIPT_PATH" "$DEST_PATH" 2>/dev/null || {
    echo "session-upload: Failed to copy file to: $DEST_PATH" >&2
    exit 0
}

# Git operations in destination repo
cd "$DEST_REPO" || exit 0

# Add, commit, and push
git add "projects/$RELATIVE_PATH" 2>/dev/null || {
    echo "session-upload: Git add failed" >&2
    exit 0
}

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "session-upload: No changes to commit" >&2
    exit 0
fi

git commit -m "Upload conversation: $RELATIVE_PATH" 2>/dev/null || {
    echo "session-upload: Git commit failed" >&2
    exit 0
}

# Push with pull --rebase retry for concurrent uploads
git push 2>/dev/null || {
    # Push failed - likely remote has new commits, try pull --rebase
    git pull --rebase 2>/dev/null || {
        echo "session-upload: Git pull --rebase failed" >&2
        exit 0
    }
    git push 2>/dev/null || {
        echo "session-upload: Git push failed after rebase" >&2
        exit 0
    }
}

# Success - don't log to avoid cluttering session end
exit 0
