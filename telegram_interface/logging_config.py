"""
Centralized logging configuration for the Google Agent Bot.

Provides:
- Dual output: Human-readable console logs + structured JSON file logs
- Log rotation (10MB files, keep 5 backups)
- Sensitive data redaction (tokens, API keys, email content)
- Contextual logging with user_id and session_id tracking
"""

import logging
import logging.handlers
import re
from pathlib import Path
from typing import Optional, Dict, Any

from pythonjsonlogger import json

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "bot.log"


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from log records."""

    # Patterns for sensitive data
    REDACTION_PATTERNS = [
        # OAuth tokens
        (re.compile(r'"access_token"\s*:\s*"[^"]*"'), '"access_token": "[REDACTED]"'),
        (re.compile(r'"refresh_token"\s*:\s*"[^"]*"'), '"refresh_token": "[REDACTED]"'),
        (re.compile(r'access_token[=:]\s*[\w\-\.]+'), 'access_token=[REDACTED]'),
        (re.compile(r'refresh_token[=:]\s*[\w\-\.]+'), 'refresh_token=[REDACTED]'),

        # API keys and secrets
        (re.compile(r'(api[_-]?key|apikey)\s*[=:]\s*[\w\-]+', re.IGNORECASE), r'\1=[REDACTED]'),
        (re.compile(r'(secret|password|passwd|pwd)\s*[=:]\s*\S+', re.IGNORECASE), r'\1=[REDACTED]'),

        # Bearer tokens
        (re.compile(r'Bearer\s+[\w\-\.]+', re.IGNORECASE), 'Bearer [REDACTED]'),

        # Email addresses (partial redaction - keep domain)
        (re.compile(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'), r'***@\2'),

        # Long base64-like strings (likely tokens)
        (re.compile(r'\b[A-Za-z0-9+/]{40,}={0,2}\b'), '[REDACTED_TOKEN]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log record."""
        # Redact from message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in self.REDACTION_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)

        # Redact from args if present
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self._redact_dict(arg) if isinstance(arg, dict)
                    else self._redact_string(arg) if isinstance(arg, str)
                    else arg
                    for arg in record.args
                )

        return True

    def _redact_string(self, text: str) -> str:
        """Apply redaction patterns to a string."""
        for pattern, replacement in self.REDACTION_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive keys in dictionaries."""
        SENSITIVE_KEYS = {
            'access_token', 'refresh_token', 'token', 'api_key', 'apikey',
            'secret', 'password', 'passwd', 'pwd', 'credentials', 'auth'
        }

        redacted = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, str):
                redacted[key] = self._redact_string(value)
            else:
                redacted[key] = value
        return redacted


class CustomJsonFormatter(json.JsonFormatter):
    """Custom JSON formatter with additional context fields."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to JSON log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = self.formatTime(record, self.datefmt)

        # Add level name
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add contextual information if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        if hasattr(record, 'agent_name'):
            log_record['agent_name'] = record.agent_name
        if hasattr(record, 'tool_name'):
            log_record['tool_name'] = record.tool_name
        if hasattr(record, 'execution_time'):
            log_record['execution_time'] = record.execution_time


class ConsoleColorFormatter(logging.Formatter):
    """Formatter with colors for console output."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname to original
        record.levelname = levelname

        return formatted


def setup_logging(log_level: int = logging.DEBUG) -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level: The minimum log level to capture (default: DEBUG)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # Console Handler (human-readable with colors)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = ConsoleColorFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # File Handler (JSON with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    json_formatter = CustomJsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(sensitive_filter)
    root_logger.addHandler(file_handler)

    # Reduce noise from some libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.INFO)

    root_logger.info("Logging system initialized", extra={
        'log_level': logging.getLevelName(log_level),
        'log_file': str(LOG_FILE),
        'console_output': True,
        'json_output': True
    })


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (typically __name__)
        **context: Additional context to include in all log messages
                  (e.g., user_id, session_id, agent_name)

    Returns:
        LoggerAdapter with context
    """
    logger = logging.getLogger(name)

    if context:
        return logging.LoggerAdapter(logger, context)

    return logging.LoggerAdapter(logger, {})


# Convenience functions for adding context to existing loggers
def add_user_context(logger: logging.Logger, user_id: int, username: Optional[str] = None) -> logging.LoggerAdapter:
    """Add user context to logger."""
    context = {'user_id': user_id}
    if username:
        context['username'] = username
    return logging.LoggerAdapter(logger, context)


def add_agent_context(logger: logging.Logger, agent_name: str) -> logging.LoggerAdapter:
    """Add agent context to logger."""
    return logging.LoggerAdapter(logger, {'agent_name': agent_name})


def add_tool_context(logger: logging.Logger, tool_name: str) -> logging.LoggerAdapter:
    """Add tool context to logger."""
    return logging.LoggerAdapter(logger, {'tool_name': tool_name})
