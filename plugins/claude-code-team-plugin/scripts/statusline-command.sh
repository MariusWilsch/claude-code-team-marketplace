#!/usr/bin/env bash

# Robbyrussell-inspired status line for Claude Code
# Shows: path + arrow + git + context + model

# Read JSON input
input=$(cat)

# Extract values (use empty string for missing/null values)
current_dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
context_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
model=$(echo "$input" | jq -r '.model.display_name // .model.id // .model // empty')
session_id=$(echo "$input" | jq -r '.session_id // empty')

# Guard: if no current_dir, use pwd
[ -z "$current_dir" ] && current_dir="$(pwd)"

# Full path with ~ shorthand
dir_name="${current_dir/#$HOME/\~}"

# --- Issue info with guard clause ---
get_issue_info() {
    [ -z "$session_id" ] && return
    local state_file="$HOME/.claude/.session-state/$session_id"
    [ ! -f "$state_file" ] && return
    local state_content=$(cat "$state_file" 2>/dev/null)
    [ -z "$state_content" ] && return

    # Parse repo#issue format (e.g., DaveX2001/claude-code-improvements#335)
    local repo=$(echo "$state_content" | cut -d'#' -f1)
    local issue_num=$(echo "$state_content" | cut -d'#' -f2)

    # Shorten repo name (take last part after /)
    local short_repo=$(echo "$repo" | rev | cut -d'/' -f1 | rev)

    # Fallback for old format (just issue number)
    [ -z "$issue_num" ] && { printf "\033[0;36m#%s\033[0m" "$state_content"; return; }

    printf "\033[0;36m%s#%s\033[0m" "$short_repo" "$issue_num"
}

# --- Context info with guard clause ---
get_context_info() {
    [ -z "$context_pct" ] && return

    local color="\033[0;31m"  # red (default: >70%)
    [ "$context_pct" -lt 70 ] && color="\033[0;33m"  # yellow
    [ "$context_pct" -lt 50 ] && color="\033[0;32m"  # green

    printf " | ${color}%d%%\033[0m" "$context_pct"
}

# --- Model info with guard clause ---
get_model_info() {
    [ -z "$model" ] && return

    local short_model="$model"
    case "$model" in
        *opus*|*Opus*) short_model="opus" ;;
        *sonnet*|*Sonnet*) short_model="sonnet" ;;
        *haiku*|*Haiku*) short_model="haiku" ;;
    esac

    printf " | \033[0;35m%s\033[0m" "$short_model"
}

# --- Git info with guard clauses ---
get_git_info() {
    # Guard: no .git directory
    [ ! -d "$current_dir/.git" ] && { printf " \033[0;90mno git\033[0m"; return; }

    local git_branch
    git_branch=$(cd "$current_dir" && git rev-parse --abbrev-ref HEAD 2>/dev/null)

    # Guard: no branch found
    [ -z "$git_branch" ] && return

    # Check dirty state
    local dirty=""
    [ -n "$(cd "$current_dir" && git status --porcelain 2>/dev/null)" ] && dirty=" \033[0;33m✗\033[0m"

    printf " \033[1;34mgit:(\033[0;31m%s\033[1;34m)%b\033[0m" "$git_branch" "$dirty"
}

# Output
# Line 1: directory, Line 2: arrow + git + context + model, Line 3: issue (if set)
issue_line=$(get_issue_info)
printf "\033[0;36m%s\033[0m\n\033[1;32m➜\033[0m%s%s%s" \
    "$dir_name" \
    "$(get_git_info)" \
    "$(get_context_info)" \
    "$(get_model_info)"
[ -n "$issue_line" ] && printf "\n%s" "$issue_line"
exit 0
