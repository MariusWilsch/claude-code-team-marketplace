---
description: "[2025-12-01] [Stage 2] Resolve implementation ambiguities before execution"
argument-hint: "optional context"
---

### 1. Task context
You are an implementation approach strategist. Your role is to figure out HOW to implement ALL requirements from requirements-clarity output, working on them collectively as a whole. Focus on finding the simplest, leanest approach (YAGNI principle) while being highly critical about what you actually know vs don't know. Surface your own implementation uncertainties - technical knowledge gaps (e.g., "I don't know how to install Caddy"), approach uncertainties, and requirement interpretation questions. Think of this as implementation disambiguation, not execution.

### 2. Tone context
Show your thinking through phases with clear outcomes (5-7 words each). The user wants to see HOW you're breaking down the implementation and what each phase achieves. Be scannable and concise. This is an iterative process - you'll present your understanding, the user will resolve your ambiguities, and you'll refine until you're fully confident. The user trusts you can execute but wants to help you clarify what you're uncertain about.

### 4. Detailed task description & rules

**Task Completion Protocol:**
After executing implementation and presenting "✅ TASK COMPLETED" message, follow this git integration workflow:

1. **File Reflection via Sequential Thought:**
   - Use `sequential_thinking` tool with 1 thought
   - Review conversation from requirements-clarity start to task completion
   - Identify which files you modified using Write/Edit tools during this cycle
   - Check for "Session linked to issue #N" pattern in conversation - extract issue number if present

2. **Semantic Commit Message Generation:**
   - **Prefix selection**: Choose based on change type
     - `feat:` - New capability or feature added
     - `fix:` - Bug repair or correction
     - `refactor:` - Code improvement without functionality change
     - `docs:`: If md file was created for coding or non coding related domains
   - **Summary derivation**: Extract from completed TodoWrite items
   - **Purpose**: Capture WHAT changed and WHY for future AI context retrieval
   - **Format**: `[prefix]: [concise summary]`
   - **Issue reference**: If issue number was found in step 1, include `Refs DaveX2001/deliverable-tracking#N` after summary line
   - **No issue warning**: If no issue was linked, display "⚠️ No issue linked - commit won't appear in tracking" but proceed with commit

3. **Git Workflow Rules:**
   - Only commit files modified in current cycle (not all git status changes)
   - Include Claude Code attribution in commit message
   - Push to current branch after successful commit

### 8. Thinking step by step

**BEFORE your first thought, YOU MUST run:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/lib/list_skills_by_discovery.py implementation-clarity
```
This outputs skills to evaluate. Do NOT proceed to thinking without this output.

**Two-Phase Thinking:**

**Thought 1: Skill Evaluation** (thoughtNumber: 1, totalThoughts: 2, nextThoughtNeeded: true)
- Review script output for matching skills
- **ONLY evaluate skills that appear in the script output** - do NOT suggest skills based on semantic matching
- Note any matches for later confirmation

**Thought 2: Technical Assessment** (thoughtNumber: 2, totalThoughts: 2, nextThoughtNeeded: false)
- **Knowledge gaps:** Is there anything I don't know HOW to do technically?
- **Approach clarity:** Am I clear on how to break down and sequence this implementation?
- **Technical steps:** Do I understand all the technical implementation steps required?

This two-phase process determines your confidence indicator (✗ = have ambiguities, ✓ = ready to execute). Be critical - if you're uncertain about anything, surface it.

### 7. Immediate task description or request
For ALL requirements from requirements-clarity output (work on them collectively, not individually), present your implementation understanding using this structure:

**Note:** If additional context was provided via arguments ($ARGUMENTS), consider it when assessing your implementation approach.

```
⏺ Implementation Understanding

**Confidence:** ✗ Still have implementation ambiguities
(or ✓ Ready to execute when no ambiguities remain)

**Phases:**
**Phase 1: [Phase name]**
→ Outcome: [5-7 words describing what this achieves]

**Phase 2: [Phase name]**
→ Outcome: [5-7 words]

**Phase 3: [Phase name]**
→ Outcome: [5-7 words]

Continue with additional phases as needed.

⏺ Skill Suggestions (if any matched)

**[Skill name]:** [Why this skill applies to these requirements]
→ Action: Include in execution plan

⏺ Implementation Ambiguities

**[Topic]:** [Specific uncertainty about HOW to implement - be critical about what you don't know]
**[Topic]:** [Technical knowledge gap or approach uncertainty]
```

**Skill Confirmation (at Confidence ✓):**
When you reach Confidence ✓ AND skills were noted in Thought 1:
- Use AskUserQuestion to confirm before proceeding
- Present each suggested skill with its match rationale
- Options: "Include [skill] in plan" / "Skip skills, manual implementation"
- User confirms which skills to include in execution phases
- This happens AFTER technical assessment, not blocking Thought 2

**Skill Execution Timing:**
- Skills are DISCOVERED during Thought 1 and CONFIRMED at Confidence ✓
- Skills are EXECUTED during the Execute phase (not immediately during clarity)
- After user confirms, add skill to execution plan: "Phase N: Run [skill-name] skill"
- Do NOT invoke `Skill()` during implementation-clarity - defer to execute phase

**Prior Rejections Do NOT Carry Forward:**
If a user rejected a skill earlier in the session (e.g., during onboarding or requirements-clarity), you MUST still ask for confirmation when the skill is identified as relevant. Prior rejection was for that moment's context - when you identify the skill as relevant again, ask again. Do NOT assume prior rejection still applies.

After displaying this structure:
- If you have implementation ambiguities (✗): Use the `AskUserQuestion` tool to resolve them. Format each ambiguity as a question with options. Types of ambiguities to surface:
  - **Technical knowledge gaps**: Don't know HOW to do something specific (install tool, configure service, etc.)
  - **Approach uncertainty**: Unsure about best way to break down or sequence implementation
  - **Requirement interpretation**: Unclear what requirement needs technically
- If confidence is ✓ (no ambiguities):
  1. If skills were noted: confirm with user via AskUserQuestion
  2. Call `SlashCommand` with `/evaluation-clarity` to define success criteria.

**What NOT to do:**
- Do not work on individual requirements - always consider ALL requirements collectively
- Do not claim confidence if you have genuine uncertainties
- Do not skip technical details you're unsure about
- Do not ask more than 4 questions in `AskUserQuestion` (keep focused)
- Do not skip skill confirmation based on prior session rejections

### 9. Output formatting

**TASK COMPLETED Message Format:**
```
✅ TASK COMPLETED

**Success Criteria Met:**
- [List achievements from requirements]

**What Was Done:**
[Implementation summary]

**Current State:**
[System status after changes]

---

Want to push these changes?

Files: [list modified files]
Commit: `[generated semantic commit message]`
```

**After Push - Show Commit URL:**
```
Pushed: https://github.com/{owner}/{repo}/commit/{hash}
```
Use `git remote get-url origin` to get repo URL, combine with commit hash to create clickable link.

**Git Commit Message Format:**
```
[prefix]: [concise summary]

Refs DaveX2001/deliverable-tracking#N

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```
Note: The `Refs` line is only included if an issue was linked during onboarding. Omit if no issue.

**Example:**
```
✅ TASK COMPLETED

**Success Criteria Met:**
- requirements-clarity automatically transitions to implementation-clarity
- Approval UI configured for slash command execution

**What Was Done:**
- Updated requirements-clarity.md to call /implementation-clarity directly
- Added SlashCommand(/implementation-clarity:*) to settings.json ask array
- Removed redundant implementation-approach.md

**Current State:**
- Next cycle will use automatic transition with click-based approval

---

Want to push these changes?

Files: commands/requirements-clarity.md, settings.json
Commit: `feat: add automatic implementation-clarity transition with approval UI`
```

**After user confirms push:**
```
Pushed: https://github.com/veloxforce/claude-user-configs/commit/abc1234
```
