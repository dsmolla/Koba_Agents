import re

def telegram_format(text: str) -> str:
    """
    Escapes special characters for Telegram's MarkdownV2 format.

    In MarkdownV2, these characters must be escaped with a backslash:
    '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'

    Args:
        text: The text to escape

    Returns:
        The escaped text safe for MarkdownV2
    """
    # Characters that need to be escaped in MarkdownV2 (without backslash)
    escape_chars = r'([_*\[\]()~`>#+=|{}.!-])'

    # Escape backslash first, then other special characters
    text = text.replace('\\', '\\\\')
    text = re.sub(escape_chars, r'\\\1', text)

    return text
