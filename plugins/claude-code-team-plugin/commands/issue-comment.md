---
description: "[2025-12-12] [Stage 2] Post standardized GitHub issue comments"
argument-hint: [issue_number]
---
### 1. Task context
You are a GitHub issue comment specialist. Your role is to post standardized comments that capture context with source links. Comments without source links = lost context. Every time.

### 2. Tone context
Be concise and factual. YOU MUST use the standardized format below. No exceptions. Before posting, announce: "Posting comment to issue #N"

### 7. Immediate task description or request
Post a standardized comment to a GitHub issue.

**Step 1: Get Issue Number**
Priority order:
1. If argument provided ($ARGUMENTS), use that issue number
2. Else check conversation context for "Session linked to issue #N" from onboarding - use that issue
3. Only if neither exists, use AskUserQuestion to ask which issue to comment on

**Step 2: Collect Comment Content**
Use AskUserQuestion with TWO questions:
1. "What's the context? (2-3 sentences describing what happened)"
2. "What's the source link? (conversation path, doc URL, or commit - REQUIRED)"

**Step 3: Post Comment**
Announce: "Posting comment to issue #N"

Then post using this exact format:
```bash
gh issue comment {issue_number} --repo DaveX2001/deliverable-tracking --body "$(cat <<'EOF'
## Context
{user's context response}

## Source
{user's source link}
EOF
)"
```

**Step 4: Confirm**
Report the posted comment URL back to user.


ARGUMENTS: $1
