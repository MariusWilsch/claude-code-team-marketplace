"""Message extraction helpers for conversation JSONL files.

Handles parsing, filtering, and collapsing of conversation messages.
"""

import json
import re
import hashlib
from .truncation import truncate_binary_content


def get_message_id(extracted: dict) -> str:
    """Generate stable hash from message content."""
    content = json.dumps({
        'role': extracted.get('role'),
        'text': extracted.get('text', ''),
        'tool_output': extracted.get('tool_output', ''),
        'command_marker': extracted.get('command_marker', {})
    }, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()[:12]


def is_command_marker(text: str) -> bool:
    """Check if message text contains command marker tags."""
    return '<command-message>' in text and '<command-name>' in text


def parse_command_info(text: str):
    """Extract command name and args from marker text."""
    cmd_match = re.search(r'<command-name>(.*?)</command-name>', text)
    if not cmd_match:
        return None
    command_name = cmd_match.group(1)
    args_match = re.search(r'<command-args>(.*?)</command-args>', text, re.DOTALL)
    args = args_match.group(1).strip() if args_match else ''
    return (command_name, args)


def get_message_content(obj: dict):
    """Extract message and content from JSONL object."""
    msg = obj.get('message')
    if not msg:
        return None, None
    content = msg.get('content', [])
    if not isinstance(content, list):
        return msg, []
    return msg, content


def find_tool_use_items(content: list):
    """Find all tool_use items in content list."""
    for item in content:
        if not isinstance(item, dict) or item.get('type') != 'tool_use':
            continue
        tool_use_id = item.get('id')
        full_name = item.get('name', '')
        tool_input = item.get('input', {})

        # Simplify MCP tool names
        if full_name.startswith('mcp__'):
            parts = full_name.split('__')
            tool_name = parts[-1] if parts else full_name
        else:
            tool_name = full_name

        yield tool_use_id, tool_name, tool_input


def find_tool_result_id(content: list):
    """Find tool_use_id from tool_result in content."""
    for item in content:
        if isinstance(item, dict) and item.get('type') == 'tool_result':
            return item.get('tool_use_id')
    return None


def extract_texts_from_content(content: list) -> str:
    """Extract text items from content list."""
    texts = [item['text'] for item in content
             if isinstance(item, dict) and 'text' in item]
    return '\n'.join(texts) if texts else None


def should_include(extracted: dict, include_user=False, include_assistant=False, include_tools=False) -> bool:
    """Filter messages based on composable flags."""
    # Guard: empty dict
    if not extracted:
        return False

    role = extracted.get('role', 'unknown')

    # Guard: tool-related content takes priority
    if include_tools:
        if any(k in extracted for k in ('tool_output', 'tool_name', 'tools', 'tools_collapsed')):
            return True

    # User messages
    if role == 'user' and include_user:
        return 'text' in extracted or 'command_marker' in extracted

    # Assistant messages
    if role == 'assistant' and include_assistant:
        return 'text' in extracted

    return False
