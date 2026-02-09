# Claude Code Team Plugin

Team onboarding plugin with clarity workflow commands, worktree skill, and commit guards.

## Dependencies

Install these before using the plugin:

**jq** (JSON processor - required for hooks):
```bash
# Ubuntu/Debian
sudo apt install jq

# Mac
brew install jq
```

**gh** (GitHub CLI):
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
gh auth login
```

**uv** (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**git-worktree-runner** (worktree management):
```bash
git clone https://github.com/coderabbitai/git-worktree-runner.git
cd git-worktree-runner
./install.sh
```

**Homebrew** (package manager for WSL):
```bash
# Install build-essential first (required for WSL)
sudo apt-get update
sudo apt-get install build-essential

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add to PATH
test -d ~/.linuxbrew && eval $(~/.linuxbrew/bin/brew shellenv)
test -d /home/linuxbrew/.linuxbrew && eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
echo "eval \$($(brew --prefix)/bin/brew shellenv)" >> ~/.bashrc
source ~/.bashrc
```

**Supabase CLI** (database operations):
```bash
npm install -g supabase
supabase login
```

**hand-picked-tools MCP** (AI tools):
```bash
claude mcp add hand-picked-tools --transport http --scope user https://metamcp.iitr-cloud.de/metamcp/hand-picked-tools/mcp
```

**Google Chrome** (for Chrome DevTools MCP):
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install
```

**mcp2rest** (MCP gateway - optional):
```bash
npm install -g mcp2rest

# Install as service (use env to preserve PATH for nvm users)
sudo env "PATH=$PATH" npx mcp2rest service install

# Or run in foreground
npx mcp2rest start

# Add Chrome DevTools server
npx mcp2rest add chrome chrome-devtools-mcp@latest

# Verify
curl http://localhost:28888/health
```

## Install

### Public Repository (default)

```
/plugin marketplace add MariusWilsch/claude-code-team-marketplace
/plugin install claude-code-team-plugin@wilsch-ai-plugins
```

### Update

```
/plugin marketplace update wilsch-ai-plugins
/plugin update claude-code-team-plugin@wilsch-ai-plugins
```

Restart Claude Code after updating for changes to take effect.

### Troubleshooting

If `/plugin marketplace add` fails with a clone error:

1. Remove any existing marketplace entry:
   ```
   /plugin marketplace remove wilsch-ai-plugins
   ```

2. Clean up leftover files:
   ```bash
   rm -rf ~/.claude/plugins/marketplaces/MariusWilsch-claude-code-team-marketplace
   ```

3. Retry:
   ```
   /plugin marketplace add MariusWilsch/claude-code-team-marketplace
   ```

### Private Repository Setup

If this repo is made private, each user needs to configure GitHub authentication.

**Step 1: Create a GitHub Fine-Grained Personal Access Token (PAT)**

1. Go to [GitHub Settings > Developer Settings > Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Configure the token:
   - **Token name**: `claude-code-team-marketplace`
   - **Repository access**: "Only select repositories" > `MariusWilsch/claude-code-team-marketplace`
   - **Permissions**: Contents > Read-only
   - **Expiration**: choose based on your security policy
3. Click "Generate token" and copy it (`github_pat_...`)

**Step 2: Set the token in your shell environment**

Add to `~/.zshrc` (Mac) or `~/.bashrc` (Linux):

```bash
export GITHUB_TOKEN=github_pat_xxxxxxxxxxxx
```

Then reload:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

**Step 3: Add marketplace and install**

```
/plugin marketplace add MariusWilsch/claude-code-team-marketplace
/plugin install claude-code-team-plugin@wilsch-ai-plugins
```

> **Note:** The `GITHUB_TOKEN` env var is required for both initial clone and background auto-updates. Without it, Claude Code cannot authenticate against private repos because it runs git with terminal prompts disabled. See [Claude Code docs on private repositories](https://code.claude.com/docs/en/plugin-marketplaces#private-repositories) for details.

## Contents

### Commands

| Command | Purpose |
|---------|---------|
| `/onboarding` | Start session, link issue, bootstrap context |
| `/requirements-clarity` | Disambiguate WHAT to build |
| `/implementation-clarity` | Plan HOW to build |
| `/evaluation-clarity` | Define success criteria |
| `/ac-verify` | Verify acceptance criteria (separate session) |
| `/rubber-duck` | Thinking partner (Stage 2.7 with execution gate) |
| `/merge` | Safe PR merge workflow with verification |
| `/flag-for-improvement` | Capture system issues |
| `/issue-comment` | Post GitHub issue comments |

### Skills

**Note:** Plugin skills require full qualified name: `claude-code-team-plugin:skill-name`

| Skill | Invocation | Purpose |
|-------|------------|---------|
| `worktree` | `claude-code-team-plugin:worktree` | Create isolated git worktrees for issue work |
| `conversation-reader` | `claude-code-team-plugin:conversation-reader` | Extract and read Claude conversation JSONL files |
| `deliverable-tracking` | `claude-code-team-plugin:deliverable-tracking` | Create GitHub Issues for client deliverables |

### Hooks

| Hook Type | Trigger | Script |
|-----------|---------|--------|
| SessionStart | Session begins | Export `CLAUDE_CONVERSATION_PATH` |
| PreToolUse (Bash) | Before Bash | jsonl-blocker, pip-blocker, gh-api-guard, git-commit-guard, gh-issue-create-blocker |
| PreToolUse (Read) | Before Read | jsonl-blocker |
| PostToolUse (Bash) | After git push | context-check |
| SessionEnd | Session terminates | session-upload (conversation upload) |

### Lib Scripts

- `onboarding_bootstrap.py` - Session context capture
- `fetch_issue_context.py` - GitHub issue fetcher
- `list_skills_by_discovery.py` - Skill discovery helper

### Skill Discovery

The `list_skills_by_discovery.py` script discovers skills by discovery phase (e.g., `rubber-duck`, `implementation-clarity`).

**Discovery sources (checked in order):**
1. **Local skills:** `~/.claude/skills/*/SKILL.md`
2. **Plugin skills:** Enabled plugins → `installed_plugins.json` → `{installPath}/skills/*/SKILL.md`
3. **Local commands:** `~/.claude/commands/*.md`

**How it works:**
```
settings.json (enabled plugins) → installed_plugins.json (install paths) → skill files
```

**Adding discovery tags to your skills:**
```yaml
---
name: my-skill
description: "My skill description (discovery: rubber-duck)"
---
```

The `(discovery: phase)` pattern in the description field determines when the skill is suggested during onboarding.

## StatusLine Setup

The plugin includes a statusline script that displays the linked issue number from `/onboarding`.

**Display format:**
```
~/path/to/project
➜ git:(main) ✗ | 45% | opus
deliverable-tracking#335
```

**Setup:**

1. Copy the script:
```bash
cp ~/.claude/plugins/cache/*/claude-code-team-plugin/*/scripts/statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh
```

2. Create the session state directory and add to .gitignore:
```bash
mkdir -p ~/.claude/.session-state
echo ".session-state/" >> ~/.claude/.gitignore
```

3. Add to `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh",
    "padding": 0
  }
}
```

**How it works:**
- `/onboarding` writes `repo#issue` to `~/.claude/.session-state/{session_id}`
- Statusline reads `session_id` from Claude Code's JSON input
- Displays shortened repo name + issue number on 3rd line

**Requirements:** `jq` must be installed (`brew install jq` or `apt install jq`)

## Recommended Settings

Plugins can't include permissions. Add these to your `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(gh:*)", "Bash(git:*)", "Bash(uv:*)",
      "mcp__hand-picked-tools__**",
      "Skill(worktree)", "Skill(hippocampus)",
      "SlashCommand(/rubber-duck:*)"
    ],
    "deny": [
      "Bash(git push origin --delete:*)",
      "Bash(git branch -D:*)"
    ],
    "ask": [
      "Bash(rm:*)", "Bash(gh pr create:*)",
      "Bash(gh issue create:*)"
    ]
  }
}
```

See full recommended settings: [settings-template.md](docs/settings-template.md)

## Protocol

Includes `CLAUDE.md` with:
- Task lifecycle (clarity phases)
- Confidence gating (✗/✓)
- Authority model (investigation vs execution)
- JIT knowledge retrieval
