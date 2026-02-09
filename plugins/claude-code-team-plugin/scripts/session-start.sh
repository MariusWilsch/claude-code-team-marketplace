#!/bin/bash
# session-start.sh - Set and display conversation path at session start
#
# Receives JSON via stdin with transcript_path field.
# Sets CLAUDE_CONVERSATION_PATH env var and instructs AI to print path.
# Stdout goes to AI context (SessionStart special behavior).

INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [ -n "$TRANSCRIPT_PATH" ]; then
    # Set env var for session
    echo "export CLAUDE_CONVERSATION_PATH=\"$TRANSCRIPT_PATH\"" >> "$CLAUDE_ENV_FILE"

    # Instruction to AI (SessionStart stdout becomes AI context)
    echo "<session-start-instruction>"
    echo "ALWAYS print this line at the very beginning of your first response:"
    echo "📂 Conversation: $TRANSCRIPT_PATH"
    echo "Print it exactly as shown above, then continue with your normal response."
    echo "</session-start-instruction>"
fi
