---
name: ac-create
description: "Define acceptance criteria using Given-When-Then format (discovery: rubber-duck). MUST load when user says 'acceptance criteria', 'ACs', 'Given-When-Then', 'how do we verify', or 'let's define AC'. Contains the methodology - do not reason about ACs from scratch. Provides DoD dependency analysis, AC scoping, enumeration method, path prioritization, and format best practices."
---

### 1. Task context
Define acceptance criteria that verify features work correctly using Given-When-Then format.

**DoD and AC are separate concepts:**

| Concept | Question | Focus |
|---------|----------|-------|
| **DoD** | "Does it exist?" | What to build |
| **AC** | "Does it work?" | How to verify behavior |

**Key insight:** Parallel gates, not traced. Both must pass independently.

### 3. Background data

**AC Scoping Principle:**

> **AC = User-observable behavior at the boundary where value is delivered**

- Focus on WHAT users observe, not HOW system works internally
- Each feature owns its observable boundary
- Internal effects become observable in downstream features

**Decision tree:**
- HOW it's implemented? → Too narrow (implementation detail)
- WHAT value users receive? → Correct scope
- EVERYTHING the feature does? → Too broad (split it)

**Rule:** If users can't observe it, it's not AC scope.

**AC Enumeration Method:**

**YOU MUST follow this sequence. Skipping steps = incomplete coverage.**

**Step 1:** List user choices (inputs)
```
script_type: [youtube_url, custom_script, title_gen]
autopilot: [true, false]
```

**Step 2:** Enumerate combinations
```
3 × 2 = 6 paths
```

**Step 3:** Map to observable outcomes
```
(youtube_url, false) → Step 2
(youtube_url, true)  → Queue
```

**Step 4:** Each distinct outcome = 1 AC

**Path Prioritization (Pareto):**

| Tier | Path | Rule | When to Include |
|------|------|------|-----------------|
| **1** | Happy | All valid combinations | Always |
| **2** | Sad | Critical field validation | Required fields only |
| **3** | Error | Data-mutating operations | Creates/updates/deletes only |

**Skip:** Sad paths for optional fields. Error paths for read-only operations.

**Given-When-Then Format:**

**YOU MUST use business language. Technical details = wrong scope.**

| Do | Don't |
|----|-------|
| Business language | UI element IDs |
| Observable outcomes | Database state |
| Specific ("3 seconds") | Vague ("fast") |
| One behavior per AC | Multiple behaviors |
| Keep <10 steps per scenario | Long imperative scripts |
| Write declaratively | Write imperatively ("click", "verify") |

**Timing:**

**40% of early-written AC need revision.** JIT creation (just before implementation) produces higher quality AC.

| Element | When | Quality |
|---------|------|---------|
| DoD | Issue creation | Can be refined |
| AC | Before implementation | Best quality |

**Sources:**
- [Scrum.org: DoD vs AC](https://www.scrum.org/resources/blog/what-difference-between-definition-done-and-acceptance-criteria)
- [Cucumber: Better Gherkin](https://cucumber.io/docs/bdd/better-gherkin/)
- [Martin Fowler: Given-When-Then](https://martinfowler.com/bliki/GivenWhenThen.html)

### 4. Detailed task description & rules

**7-Step I/O Pipeline:**

| Step | Name | Input | Output |
|------|------|-------|--------|
| **1** | Scout | Issue body, codebase | Context understanding |
| **2** | Analyze | Scout findings | Structured DoD + passes |
| **3** | Enumerate | DoD items | Raw ACs (choices × outcomes) |
| **4** | Format | Raw ACs | Given-When-Then (business language) |
| **5** | Refinement Gate | Draft ACs | Refined ACs + Testability |
| **6** | Save | Final ACs | Tracking file |
| **7** | Inform | Link | User confirmation |

#### Step 1: Scout (Conditional)

**User decides if Scout is needed.** If context already gathered from rubber-duck, skip to Step 2.

**If Scout runs:** Use the two-agent pattern:

**Phase 1 - Scout Agent (Sonnet):**
```
Task(subagent_type="general-purpose", model="sonnet", prompt="
Quick source scan for AC creation:
1. Legacy code: Does a previous version exist? (migration/parity scenarios)
2. Current code: Is the feature already implemented? What components?
3. DoD triggers: Check for 'parity', 'migration', 'legacy', 'existing behavior'
4. Hippocampus: Any relevant project docs, patterns, or domain guides?

Return summary:
- Legacy: [exists/not found] - [what was found]
- Current: [exists/not found] - [components/files]
- DoD triggers: [keywords found]
- Hippocampus: [relevant docs]
")
```

**Phase 2 - User Decision:**
Present findings via AskUserQuestion:
- Show what Scout found
- Options: [Investigate legacy], [Investigate current], [Both], [Hippocampus], [Skip - DoD only]

**Phase 3 - Investigator Agent (Sonnet):**
Based on user selection, spawn deep investigation for observable boundaries from selected sources.

**Why this matters:** AC grounded in actual system understanding > abstract reasoning. If DoD mentions parity/migration, you MUST compare with existing behavior.

#### Step 2: Analyze

Use `sequential_thinking` to:
1. Create structured DoD from scout findings (or issue body if Scout skipped)
2. Determine if DoD items have dependencies: "Does item X require item Y to exist first?"
3. If dependencies found → group into passes
4. If independent → single list

**Output:** Structured DoD with passes (if applicable)

**DoD Dependency Analysis (when DoD has multiple items):**

Analyze DoD items. If ANY of these apply, dependency analysis is REQUIRED:
- DoD has 3+ items
- Items span different layers (database, API, UI, etc.)
- Items have implicit dependencies ("X requires Y first")

**Skip only for:** Single-item DoD or items with no dependencies.

**YOU MUST use sequential_thinking to reason about item dependencies. No hardcoded layers.**

**Step 2.1:** Use sequential_thinking to analyze each DoD item:
- What does this item depend on? (other items that must exist first)
- What depends on this item? (items that need this to exist)
- Can this be done independently?

**Step 2.2:** Mark existing vs new using Scout output
```
Item A: ✓exists
Item B: NEW, depends on nothing
Item C: NEW, depends on Item B
Item D: NEW, depends on Item C
```

**Step 2.3:** Group items into passes based on dependency chains:
- **Pass 1:** Items with NO dependencies (can start immediately)
- **Pass 2:** Items that depend ONLY on Pass 1 items
- **Pass N:** Items that depend on Pass N-1 items

**Key principle:** Pass count is DYNAMIC - determined by actual dependency chains, not hardcoded layers.

**Present passes via AskUserQuestion:**
```
Question: "Which pass should we define ACs for?"
Header: "AC Scope"
Options:
- Pass 1: [items] - (no dependencies)
- Pass 2: [items] - (depends on Pass 1)
- Pass N: [items] - (depends on Pass N-1)
- All items - Full scope
```

#### Step 3: Enumerate

**Use `sequential_thinking` to reason about enumeration approach:**
- What are the user choices (inputs)?
- What combinations exist?
- What observable outcomes map to each combination?

Apply choices × outcomes method (see "AC Enumeration Method" in Background data).
Apply Pareto tiers (see "Path Prioritization" in Background data).

#### Step 4: Format

**Use `sequential_thinking` to verify business language:**
- Is this describing WHAT users observe (correct) or HOW system works (wrong)?
- Are outcomes specific and measurable?
- Is each AC testing one behavior?

Write Given-When-Then using business language (see "Given-When-Then Format" in Background data).
Check against anti-patterns list (see Examples section).

#### Step 5: Refinement Gate

**YOU MUST complete all 4 checks SEQUENTIALLY with user judgment after EACH check. Batching checks = skipped collaboration. Every time.**

The Refinement Gate is collaborative spec design refinement - the last opportunity before implementation. AI proposes → User agrees/denies/adds. Each check requires explicit user judgment.

**For EACH check, YOU MUST:**
1. Use `sequential_thinking` (1 thought) to analyze the check
2. Present findings
3. Use AskUserQuestion with adaptive options
4. Wait for user response before proceeding to next check

---

**Check 1: Observable Output**

"Does this AC produce an observable, inspectable output?"

**Observable outputs include:**
- Files that exist (can `ls`/`cat`)
- API responses (can `curl`)
- UI state (can screenshot)
- Command outputs (can run and see result)

**Non-observable (problematic):**
- AI internal behavior ("AI reasons correctly")
- Code quality ("code is clean")
- Subjective interpretation ("follows best practices")
- **Ephemeral UI (toasts, spinners, notifications)** → Reframe to console.log or network response

**YOU MUST present findings, then use AskUserQuestion with adaptive options:**

*If confident (all ACs are observable):*
```
Question: "Observable Output check complete. All ACs produce inspectable outputs. Agreed?"
Header: "Check 1"
Options:
- Agreed, proceed to Check 2
- Actually, [AC] isn't observable - discuss
- I see it differently
```

*If issues found (some ACs not observable):*
```
Question: "Observable Output check: [list problematic ACs]. How should we handle these?"
Header: "Check 1"
Options:
- Reframe to observable output
- Mark as user-verified (manual check)
- Keep as-is (accept limitation)
```

**Only proceed to Check 2 after user responds. No exceptions.**

---

**Check 2: Test Data Availability**

**Use `sequential_thinking`:** "For each AC, can this be tested with existing fixtures/data?"

**Test data includes:**
- Test fixtures (JSON files, sample data, test projects)
- Environment access (admin URL, server, database)
- Preconditions (existing records, state setup)

**YOU MUST present findings, then use AskUserQuestion with adaptive options:**

*If confident (all test data exists):*
```
Question: "Test Data check complete. All ACs have available test data. Agreed?"
Header: "Check 2"
Options:
- Agreed, proceed to Check 3
- Missing data for [AC] - discuss
- I have additional context
```

*If gaps found (missing test data):*
```
Question: "Test Data gaps: [list gaps]. How should we handle these?"
Header: "Check 2"
Options:
- I'll provide during verification
- Add test data creation to DoD
- Let me explain the situation
```

**Only proceed to Check 3 after user responds. No exceptions.**

---

**Check 3: Design Questions**

"What implementation decisions are NOT specified in the DoD?"

Look at each DoD item and AC - are there choices the implementer would need to make that aren't documented?

**Examples of undocumented decisions:**
- Where should this component live? (file location, module structure)
- Which library/approach to use? (multiple valid options)
- Error handling strategy? (fail silently, throw, retry)
- Edge case behavior? (nulls, empty states, timeouts)

**YOU MUST present findings, then use AskUserQuestion with adaptive options:**

*If confident (no open decisions):*
```
Question: "Design Questions check complete. No undocumented decisions found. Agreed?"
Header: "Check 3"
Options:
- Agreed, proceed to Check 4
- Actually, there's an open decision
- Let me think about this
```

*If open decisions found:*
```
Question: "Design decisions to resolve: [list questions]. How should we proceed?"
Header: "Check 3"
Options:
- Let me answer each one
- Add as TBD in implementation notes
- These aren't actually open - let me explain
```

**Only proceed to Check 4 after user responds. No exceptions.**

---

**Check 4: Blocking Dependencies**

"What actions require coordination before AI can verify ACs?"
- Surface all potential blocking dependencies explicitly
- Discuss each one with user - don't assume AI can't do something
- Clarify what AI can do vs what user needs to do

**YOU MUST present findings, then use AskUserQuestion with adaptive options:**

*If confident (no blocking dependencies):*
```
Question: "Blocking Dependencies check complete. AI can verify all ACs independently. Agreed?"
Header: "Check 4"
Options:
- Agreed, Refinement Gate complete
- There's something I need to do first
- Let me think about this
```

*If dependencies found:*
```
Question: "Blocking dependencies: [list items]. How should we handle these?"
Header: "Check 4"
Options:
- I'll handle before verification
- AI can actually do [X] - let me explain
- Let's discuss workflow
```

**Only proceed to Step 6 after user responds. No exceptions.**

---

**Required Output:** Step cannot complete without:
- `**Testability:**` section documenting fixtures, URLs, setup
- All 4 checks completed with user judgment captured
- No batching - each check discussed individually

#### Step 6: Save (Validation Gate)

**Before invoking deliverable-tracking, verify Refinement Gate output exists.**

If Testability section missing OR design questions unresolved OR blockers undiscussed:
→ Return to Step 5

**If validation passes:** Invoke `Skill(deliverable-tracking)` to create tracking file.

#### Step 7: Inform

Present tracking file link and prompt for review:

```
ACs saved: [GitHub URL to tracking.md]

Review the ACs and let me know if any issues.
```

Use AskUserQuestion: "Any issues with these ACs?" with options:
- "Looks good" → Complete
- "Need changes" → Return to relevant step

### 5. Examples

**Good:**
```gherkin
Given I am on the login page
When I enter valid credentials
Then I should see the dashboard
```

**Bad:**
```gherkin
Given the database is running
When I POST to /api/auth
Then a JWT token should be generated
```

**Anti-Patterns to Avoid:**

| Anti-Pattern | Why It's Wrong | Fix |
|--------------|----------------|-----|
| Testing database state | Not user-observable | Test user-facing outcome |
| UI element IDs in Given/When | Implementation detail | Use business language |
| "Fast", "good", "properly" | Subjective, untestable | Use specific metrics ("< 3s") |
| Multiple behaviors per AC | Hard to isolate failures | Split into separate ACs |
| Imperative style ("Click X, verify Y") | Procedure, not behavior | Declarative ("When X, Then Y") |
| Internal API responses | Technical detail | User-observable effect |
| "AI reasons correctly" | Unobservable | Observable output (file, response) |
| Ephemeral UI (toasts, spinners) | Hard to capture | Reframe to console.log or API response |

### 7. Immediate task description or request
Follow the 7-step I/O pipeline to create ACs for the current DoD/feature. Start at Step 1 (Scout) unless user indicates context is already gathered.

**Multi-Issue Sessions:** When working on multiple issues in one session, YOU MUST restart the full 7-step workflow for EACH issue. Previous workflow execution does NOT carry forward. Each issue gets its own complete pipeline run.

### 8. Thinking step by step
**YOU MUST use `sequential_thinking` at these points:**

- **Step 2 (Analyze):** Reason about DoD item dependencies
- **Step 3 (Enumerate):** Reason about enumeration approach (choices, combinations, outcomes)
- **Step 4 (Format):** Verify business language compliance
- **Step 5 Check 2:** Reason about test data availability for each AC

### 9. Output formatting

AC is presented in conversation using this format:

```gherkin
### AC1: {scenario name}
Given: ...
When: ...
Then: ...

**Testability:**
- Test fixtures: [locations]
- Environment: [URLs needed]
- Setup: [commands if any]
```

**Persistence:**

YOU MUST use `deliverable-tracking` skill to save ACs. NEVER create tracking files manually (no mkdir, no Write tool).

Manual file creation will be rejected. The skill handles file structure, commits, and pushes.

**Correct invocation:**
```
Skill(skill="deliverable-tracking")
# Then follow Step 7 (Create Tracking File) + Step 9 (Save AC)
```
