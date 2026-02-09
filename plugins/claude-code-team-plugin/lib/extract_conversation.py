#!/usr/bin/env python3
"""
Extract and format Claude conversation JSONL files.

ORCHESTRATION SCRIPT - delegates to helpers/ for implementation details.

OUTPUT FORMATS:
  Default (XML):  Semantic XML tags with indices for AI consumption
                  <user_1>message</user_1>
                  <bash_2>command</bash_2>

  --json:         JSONL format (one JSON per line) for backwards compat

COMPOSABLE FLAGS:
  --user       Include user messages
  --assistant  Include assistant messages
  --tools      Include tool calls and results

CHUNKING:
  - Auto-chunks into ~20K token files
  - Read each chunk in its entirety (that's the purpose of chunking)

See helpers/ for: truncation.py, extraction.py, formatters.py
"""

import json
import sys
import argparse
from pathlib import Path

from helpers import (
    truncate_binary_content,
    get_message_id,
    is_command_marker,
    parse_command_info,
    get_message_content,
    find_tool_use_items,
    find_tool_result_id,
    extract_texts_from_content,
    should_include,
    format_items_to_xml,
    format_items_to_jsonl,
)

# Constants
TOKEN_CHUNK_SIZE = 20000
DEFAULT_OUTPUT_DIR = '/tmp'


def extract_essentials(jsonl_path, include_user=False, include_assistant=False, include_tools=False):
    """Extract fields from conversation JSONL based on composable filters.

    Returns list of extracted message dicts.
    """
    output_lines = []
    pending_marker = None
    tool_marker_buffer = []
    pending_tool_names = {}
    pending_tool_inputs = {}

    with open(jsonl_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line)

                # Guard: skip summary lines
                if obj.get('type') == 'summary':
                    continue

                # Extract tool info
                tool_name = None
                tool_input = None
                if include_tools:
                    msg, content = get_message_content(obj)
                    for tool_use_id, name, input_data in find_tool_use_items(content or []):
                        if tool_use_id:
                            pending_tool_names[tool_use_id] = name
                            pending_tool_inputs[tool_use_id] = input_data
                            tool_name = name
                            tool_input = input_data

                    result_id = find_tool_result_id(content or [])
                    if result_id and result_id in pending_tool_names:
                        tool_name = pending_tool_names[result_id]

                # Build extracted dict
                extracted = {}

                if not include_tools:
                    msg, content = get_message_content(obj)

                # Guard: skip if no message
                if not msg:
                    continue

                extracted['role'] = msg.get('role', 'unknown')

                # Extract text
                raw_content = msg.get('content')
                if isinstance(raw_content, str):
                    extracted['text'] = raw_content
                elif content:
                    text = extract_texts_from_content(content)
                    if text:
                        extracted['text'] = text

                if 'timestamp' in obj:
                    extracted['timestamp'] = obj['timestamp']

                # Tool results
                tool_result = obj.get('toolUseResult')
                if 'toolUseResult' not in obj:
                    pass
                elif tool_result is None:
                    extracted['tools'] = 'executed'
                elif isinstance(tool_result, str):
                    extracted['tool_output'] = truncate_binary_content(tool_result, tool_name)
                elif isinstance(tool_result, dict):
                    result_str = json.dumps(tool_result, indent=2)
                    extracted['tool_output'] = truncate_binary_content(result_str, tool_name)
                elif isinstance(tool_result, list):
                    text = extract_texts_from_content(tool_result)
                    if text:
                        extracted['tool_output'] = truncate_binary_content(text, tool_name)
                    else:
                        extracted['tools'] = 'executed'
                else:
                    extracted['tools'] = 'executed'

                if tool_name:
                    extracted['tool_name'] = tool_name
                if tool_input:
                    extracted['tool_input'] = tool_input

                extracted['_id'] = get_message_id(extracted)

                # Tool marker collapsing
                if extracted.get('tools') == 'executed':
                    tool_marker_buffer.append(extracted)
                    continue

                # Flush tool marker buffer
                if tool_marker_buffer:
                    if len(tool_marker_buffer) == 1:
                        if should_include(tool_marker_buffer[0], include_user, include_assistant, include_tools):
                            output_lines.append(tool_marker_buffer[0])
                    else:
                        collapsed = tool_marker_buffer[0].copy()
                        collapsed['tools_collapsed'] = len(tool_marker_buffer)
                        del collapsed['tools']
                        if should_include(collapsed, include_user, include_assistant, include_tools):
                            output_lines.append(collapsed)
                    tool_marker_buffer = []

                # Command marker collapsing
                if 'text' in extracted and is_command_marker(extracted['text']):
                    cmd_info = parse_command_info(extracted['text'])
                    if cmd_info:
                        pending_marker = {
                            'extracted': extracted,
                            'command_name': cmd_info[0],
                            'command_args': cmd_info[1],
                            'timestamp': extracted.get('timestamp')
                        }
                        continue

                # Template following command marker
                if pending_marker and 'text' in extracted:
                    collapsed = pending_marker['extracted'].copy()
                    collapsed['command_marker'] = {
                        'name': pending_marker['command_name'],
                        'args': pending_marker['command_args'],
                        'template': extracted['text']
                    }
                    del collapsed['text']
                    if should_include(collapsed, include_user, include_assistant, include_tools):
                        output_lines.append(collapsed)
                    pending_marker = None
                    continue

                # Output if meaningful content
                if 'text' in extracted or 'tool_output' in extracted or 'tool_name' in extracted:
                    if should_include(extracted, include_user, include_assistant, include_tools):
                        output_lines.append(extracted)

            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON at line {line_num}", file=sys.stderr)
                continue

    # Flush remaining tool markers
    if tool_marker_buffer:
        if len(tool_marker_buffer) == 1:
            if should_include(tool_marker_buffer[0], include_user, include_assistant, include_tools):
                output_lines.append(tool_marker_buffer[0])
        else:
            collapsed = tool_marker_buffer[0].copy()
            collapsed['tools_collapsed'] = len(tool_marker_buffer)
            del collapsed['tools']
            if should_include(collapsed, include_user, include_assistant, include_tools):
                output_lines.append(collapsed)

    return output_lines


def count_tokens(text: str) -> int:
    """Count tokens with tiktoken, fallback to char estimate."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return len(text) // 4


def chunk_by_tokens(items: list, max_tokens: int = TOKEN_CHUNK_SIZE) -> list:
    """Split items into chunks of approximately max_tokens each."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        def get_tokens(text):
            return len(encoding.encode(text))
    except ImportError:
        def get_tokens(text):
            return len(text) // 4

    chunks = []
    current_chunk = []
    current_tokens = 0

    for item in items:
        item_text = json.dumps(item)
        item_tokens = get_tokens(item_text)

        if current_tokens + item_tokens > max_tokens and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [item]
            current_tokens = item_tokens
        else:
            current_chunk.append(item)
            current_tokens += item_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def write_chunks(chunks: list, base_path: Path, output_format: str = 'xml') -> list:
    """Write chunks to numbered files in specified format."""
    chunk_files = []
    formatter = format_items_to_xml if output_format == 'xml' else format_items_to_jsonl

    if len(chunks) == 1:
        content = formatter(chunks[0])
        with open(base_path, 'w') as f:
            f.write(content + '\n')
        tokens = count_tokens(content)
        chunk_files.append((base_path, tokens))
    else:
        stem = base_path.stem
        suffix = base_path.suffix or '.txt'
        parent = base_path.parent

        for i, chunk in enumerate(chunks, 1):
            chunk_path = parent / f"{stem}_chunk{i}{suffix}"
            content = formatter(chunk)
            with open(chunk_path, 'w') as f:
                f.write(content + '\n')
            tokens = count_tokens(content)
            chunk_files.append((chunk_path, tokens))

    return chunk_files


def main():
    parser = argparse.ArgumentParser(
        description='Extract and format Claude conversation JSONL files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Output formats:
  Default: Semantic XML (<user_1>, <bash_2>, etc.) - optimized for AI
  --json:  JSONL (one JSON per line) - backwards compatible

Examples:
  %(prog)s conversation.jsonl --user --assistant
  %(prog)s conversation.jsonl --tools --json
  %(prog)s conversation.jsonl --user --assistant --tools --last 50
'''
    )
    parser.add_argument('input_path', type=str, help='Path to conversation JSONL')
    parser.add_argument('--user', action='store_true', help='Include user messages')
    parser.add_argument('--assistant', action='store_true', help='Include assistant messages')
    parser.add_argument('--tools', action='store_true', help='Include tool calls and results')
    parser.add_argument('--last', type=int, metavar='N', help='Limit to last N items')
    parser.add_argument('--output', '-o', type=str, metavar='FILE',
                       help='Output file (default: /tmp/{conversation_uid}.txt)')
    parser.add_argument('--json', action='store_true', help='Output JSONL instead of XML')

    args = parser.parse_args()

    # Guard: require at least one content flag
    if not (args.user or args.assistant or args.tools):
        parser.print_help(sys.stderr)
        print("\nError: At least one of --user, --assistant, or --tools required.", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input_path).resolve()

    # Guard: file must exist
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Status
    flags = [f for f in ['user', 'assistant', 'tools'] if getattr(args, f)]
    output_format = 'json' if args.json else 'xml'
    print(f"📂 Processing: {input_path.name}", file=sys.stderr)
    print(f"🎯 Flags: {' '.join(['--' + f for f in flags])}", file=sys.stderr)
    print(f"📄 Format: {output_format.upper()}", file=sys.stderr)

    # Extract
    extracted = extract_essentials(
        input_path,
        include_user=args.user,
        include_assistant=args.assistant,
        include_tools=args.tools
    )

    if args.last and args.last > 0:
        extracted = extracted[-args.last:]

    print(f"✅ Extracted: {len(extracted)} messages", file=sys.stderr)

    # Chunk and write - use conversation UID for output to avoid race conditions
    if args.output:
        output_path = Path(args.output)
    else:
        conversation_uid = input_path.stem  # e.g., f3954903-eea0-47d1-a064-de139d7d18a1
        output_path = Path(DEFAULT_OUTPUT_DIR) / f"{conversation_uid}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chunks = chunk_by_tokens(extracted)
    chunk_files = write_chunks(chunks, output_path, output_format)

    # Summary
    total_tokens = sum(tokens for _, tokens in chunk_files)
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"📊 Total tokens: {total_tokens:,}", file=sys.stderr)
    print(f"📦 Chunks: {len(chunk_files)} file(s)", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    for path, tokens in chunk_files:
        print(f"  {path} ({tokens:,} tokens)", file=sys.stderr)

    print(f"{'='*50}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
