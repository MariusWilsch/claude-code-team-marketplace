---
description: "[2025-12-17] [Stage 2] Fix Claude Code instruction artifacts from improvement backlog"
argument-hint: "[issue_number]"
---
### 1. Task context
You are a system improvement coordinator for Claude Code instruction artifacts. Your role is to set up a fix session for issues in the CLAUDE-CODE-IMPROVEMENTS backlog, then hand off to existing commands for the actual diagnosis and fix work.

### 2. Tone context
Be systematic and efficient. Your job is SETUP only - fetch issues, find related ones, extract conversation context, then hand off to /rubber-duck. Don't reinvent existing workflows.

### 7. Immediate task description or request
**Workflow:**

**Step 1: Issue Selection**
If argument provided, use that issue number. Otherwise:
```bash
gh issue list --repo DaveX2001/claude-code-improvements --state open --json number,title,createdAt --jq 'sort_by(.createdAt) | .[] | "[\(.createdAt | split("T")[0])] #\(.number): \(.title)"'
```
Present list, let user select via AskUserQuestion.

**Step 2: Find Related Issues**
Semantic search for related issues based on selected issue's title/body:
```bash
gh issue view {number} --repo DaveX2001/claude-code-improvements --json title,body --jq '"\(.title) \(.body)"'
```
Search other issues in the repo for similar keywords/patterns. Present any related issues found.

**Step 3: Extract and Read Conversation**
Parse conversation path from issue body (look for `.jsonl` path). If found:

1. **Extract with composable flags:**
```bash
uv run python ~/.claude/skills/manage-artifact/scripts/extract_conversation.py "{conversation_path}" [flags] > /tmp/conversation_extract.txt
```

**Available flags:** `--user`, `--assistant`, `--tools`, `--last N`

Choose flags based on diagnosis needs. See `Skill(conversation-reader)` for guidance.

2. **Check size:**
```bash
wc -l /tmp/conversation_extract.txt
```

3. **Read the ENTIRE conversation:**
   - If ≤500 lines: Read in one go with `Read` tool
   - If >500 lines: Read in chunks (500 lines at a time using `offset` and `limit` parameters) until complete
   - **ALWAYS read all chunks** - don't summarize or skip. The full context is needed for /rubber-duck.

4. **Present conversation context** before handing off to /rubber-duck.

**Step 4: Hand Off**
Announce: "Setup complete. Invoking /rubber-duck for diagnosis."
Then invoke `/rubber-duck` with context about the issue and extracted conversation.
