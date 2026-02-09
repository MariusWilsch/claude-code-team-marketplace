"""Truncation logic for conversation extraction.

Handles binary content detection and tool-based output truncation.
"""

# Tools to truncate vs keep full
TRUNCATE_TOOLS = {'Read', 'Grep', 'Write'}  # Verbose output tools
FULL_OUTPUT_TOOLS = {'Bash', 'Glob', 'Task', 'AskUserQuestion', 'sequentialthinking'}  # High-value tools
SUMMARIZE_TOOLS = {'Edit'}  # Just show file:line
TRUNCATE_THRESHOLD = 1000  # Characters


def is_base64_content(text: str, min_length: int = 1000) -> bool:
    """Detect if text is likely base64-encoded binary content."""
    if len(text) < min_length:
        return False

    if text.startswith('data:'):
        return True

    first_chunk = text[:1000]
    if 'JVBERi' in first_chunk:  # PDF
        return True
    if 'iVBORw' in first_chunk:  # PNG
        return True
    if '/9j/' in first_chunk:  # JPEG
        return True
    if '"base64"' in text[:500] and len(text) > 10000:
        return True

    # Generic base64 detection for large text
    if len(text) > 50000:
        mid = len(text) // 2
        sample = text[mid:mid+500]
        base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if all(c in base64_chars for c in sample.replace(' ', '').replace('\n', '')):
            return True

    return False


def truncate_binary_content(text: str, tool_name: str = None) -> str:
    """Replace base64 binary content with a size marker."""
    if not is_base64_content(text):
        return text

    encoded_size = len(text)
    original_size = int(encoded_size * 0.75)

    if original_size > 1_000_000:
        size_str = f"{original_size / 1_000_000:.1f}MB"
    elif original_size > 1_000:
        size_str = f"{original_size / 1_000:.1f}KB"
    else:
        size_str = f"{original_size}B"

    first_chunk = text[:1000]
    content_type = "binary"
    if 'JVBERi' in first_chunk:
        content_type = "PDF"
    elif 'iVBORw' in first_chunk:
        content_type = "PNG"
    elif '/9j/' in first_chunk:
        content_type = "JPEG"
    elif 'data:image/' in first_chunk or '"type": "image"' in first_chunk:
        content_type = "image"
    elif 'data:application/pdf' in first_chunk:
        content_type = "PDF"

    tool_prefix = f"{tool_name}: " if tool_name else ""
    return f"[{tool_prefix}{content_type} {size_str}]"


def truncate_by_tool_type(text: str, tool_name: str = None) -> str:
    """Truncate output based on tool type.

    - TRUNCATE_TOOLS: Truncate if >1000 chars
    - FULL_OUTPUT_TOOLS: Always keep full
    - Unknown tools: Truncate if >1000 chars
    """
    if not text or len(text) <= TRUNCATE_THRESHOLD:
        return text

    if tool_name and tool_name in FULL_OUTPUT_TOOLS:
        return text

    size_kb = len(text) / 1000
    return f"{text[:TRUNCATE_THRESHOLD]}...\n[...truncated, {size_kb:.1f}KB total]"
