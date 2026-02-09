"""Output formatters for conversation extraction.

Provides XML (default) and JSONL output formats.
"""

import json
from .truncation import truncate_by_tool_type


def format_item_to_xml(item: dict, index: int) -> str:
    """Format a single extracted item to semantic XML format.

    Format: <type_N>content</type_N>
    Types: user, assistant, bash, read, edit, etc.
    Multiline output uses indented block format.
    """
    role = item.get('role', 'unknown')

    # Determine tag name and content
    if 'command_marker' in item:
        cmd = item['command_marker']
        tag = 'command'
        args = f" {cmd.get('args', '')}" if cmd.get('args') else ""
        content = f"/{cmd.get('name', 'unknown')}{args}"

    elif 'tool_name' in item:
        tool_name = item['tool_name']
        tag = tool_name.lower()

        # Tool call (has input)
        if 'tool_input' in item and 'tool_output' not in item:
            tool_input = item['tool_input']
            if tool_name == 'Bash':
                content = tool_input.get('command', str(tool_input))
            elif tool_name == 'Read':
                content = tool_input.get('file_path', str(tool_input))
            elif tool_name == 'Edit':
                fp = tool_input.get('file_path', '')
                old = tool_input.get('old_string', '')[:50]
                new = tool_input.get('new_string', '')[:50]
                content = f"{fp}\n  {old!r} → {new!r}"
            elif tool_name == 'Write':
                fp = tool_input.get('file_path', '')
                content_len = len(tool_input.get('content', ''))
                content = f"{fp} ({content_len} chars)"
            elif tool_name == 'Grep':
                pattern = tool_input.get('pattern', '')
                path = tool_input.get('path', '.')
                content = f"{pattern!r} in {path}"
            elif tool_name == 'Glob':
                pattern = tool_input.get('pattern', '')
                content = pattern
            elif tool_name == 'sequentialthinking':
                thought = tool_input.get('thought', str(tool_input))
                content = thought
                tag = 'thinking'
            elif tool_name == 'AskUserQuestion':
                # Extract questions from the input
                questions = tool_input.get('questions', [])
                if questions:
                    q_texts = [q.get('question', '') for q in questions if isinstance(q, dict)]
                    content = '\n'.join(f"Q: {q}" for q in q_texts)
                else:
                    content = str(tool_input)[:500]
                tag = 'question'
            else:
                content = str(tool_input)[:500]

        # Tool result (has output)
        elif 'tool_output' in item:
            output = item['tool_output']

            # Special handling for AskUserQuestion answers
            if tool_name == 'AskUserQuestion':
                tag = 'answer'
                content = output  # User's answer - keep full, don't truncate
            else:
                output = truncate_by_tool_type(output, tool_name)
                if '\n' in output:
                    indented = '\n'.join('    ' + line for line in output.split('\n'))
                    content = f"→\n{indented}"
                else:
                    content = f"→ {output}"

        else:
            content = "[executed]"

    elif 'tools_collapsed' in item:
        tag = 'tools'
        content = f"[{item['tools_collapsed']} tools executed]"

    elif 'text' in item:
        tag = role
        content = item['text']

    else:
        tag = role
        content = "[empty]"

    return f"<{tag}_{index}>\n{content}\n</{tag}_{index}>"


def format_items_to_xml(items: list) -> str:
    """Format all items to XML format."""
    return '\n\n'.join(format_item_to_xml(item, i+1) for i, item in enumerate(items))


def format_items_to_jsonl(items: list) -> str:
    """Format all items to JSONL format (one JSON per line)."""
    return '\n'.join(json.dumps(item) for item in items)
