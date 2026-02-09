#!/usr/bin/env python3
"""
List skills and commands by discovery phase.

Usage:
    list_skills_by_discovery.py <phase>
    list_skills_by_discovery.py requirements-clarity

Searches all skills and commands for (discovery: <phase>) in their descriptions.
Scans both local skills (~/.claude/skills/) and plugin-provided skills.
"""

import sys
import json
from pathlib import Path

def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown file."""
    if not content.startswith('---'):
        return {}

    # Find closing ---
    end_idx = content.find('---', 3)
    if end_idx == -1:
        return {}

    frontmatter = content[3:end_idx].strip()
    result = {}

    for line in frontmatter.split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            result[key.strip()] = value.strip()

    return result


def find_skills_by_discovery(phase: str) -> list[tuple[str, str]]:
    """Find all skills with (discovery: phase) in description."""
    results = []
    skills_dir = Path.home() / '.claude' / 'skills'

    if not skills_dir.exists():
        return results

    pattern = f'(discovery: {phase})'

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / 'SKILL.md'
        if not skill_file.exists():
            continue

        content = skill_file.read_text()
        fm = extract_frontmatter(content)

        desc = fm.get('description', '')
        if pattern in desc:
            name = skill_dir.name
            results.append((name, desc))

    return results


def find_commands_by_discovery(phase: str) -> list[tuple[str, str]]:
    """Find all commands with (discovery: phase) in description."""
    results = []
    commands_dir = Path.home() / '.claude' / 'commands'

    if not commands_dir.exists():
        return results

    pattern = f'(discovery: {phase})'

    for cmd_file in commands_dir.glob('*.md'):
        content = cmd_file.read_text()
        fm = extract_frontmatter(content)

        desc = fm.get('description', '')
        if pattern in desc:
            name = cmd_file.stem
            results.append((f'/{name}', desc))

    return results


def find_plugin_skills_by_discovery(phase: str) -> list[tuple[str, str]]:
    """Find all plugin-provided skills with (discovery: phase) in description.

    Chains: settings.json (enabled plugins) → installed_plugins.json (paths) → skill files.
    """
    results = []
    claude_dir = Path.home() / '.claude'
    settings_file = claude_dir / 'settings.json'
    installed_file = claude_dir / 'plugins' / 'installed_plugins.json'

    if not settings_file.exists() or not installed_file.exists():
        return results

    # Get enabled plugins from settings
    try:
        settings = json.loads(settings_file.read_text())
        enabled_plugins = settings.get('enabledPlugins', {})
    except (json.JSONDecodeError, IOError):
        return results

    # Get install paths from installed_plugins.json
    try:
        installed = json.loads(installed_file.read_text())
        plugins_map = installed.get('plugins', {})
    except (json.JSONDecodeError, IOError):
        return results

    pattern = f'(discovery: {phase})'

    # For each enabled plugin, look up install path and scan skills
    for plugin_key, is_enabled in enabled_plugins.items():
        if not is_enabled:
            continue

        if plugin_key not in plugins_map:
            continue

        # Get latest install path (last entry in array)
        installs = plugins_map[plugin_key]
        if not installs:
            continue

        install_path = Path(installs[-1].get('installPath', ''))
        if not install_path.exists():
            continue

        # Scan skills directory
        skills_dir = install_path / 'skills'
        if not skills_dir.exists():
            continue

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / 'SKILL.md'
            if not skill_file.exists():
                continue

            try:
                content = skill_file.read_text()
                fm = extract_frontmatter(content)

                desc = fm.get('description', '')
                if pattern in desc:
                    name = skill_dir.name
                    # Prefix with plugin name for clarity
                    plugin_name = plugin_key.split('@')[0]
                    results.append((f'{plugin_name}:{name}', desc))
            except IOError:
                continue

    return results


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    phase = sys.argv[1]

    print(f"Skills with (discovery: {phase}):")
    print("=" * 40)

    local_skills = find_skills_by_discovery(phase)
    plugin_skills = find_plugin_skills_by_discovery(phase)
    commands = find_commands_by_discovery(phase)

    all_matches = local_skills + plugin_skills + commands

    if not all_matches:
        print(f"No skills/commands found with (discovery: {phase})")
    else:
        for name, desc in all_matches:
            print(f"- **{name}**: {desc}")
            print()

    print()
    print("In Thought 1, reason about which of these skills apply to the current task.")


if __name__ == '__main__':
    main()
