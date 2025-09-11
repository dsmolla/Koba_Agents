""" Handles email operations like sending, creating drafts, replying, forwarding, deleting and downloading attachments """

from .agent import (
    EmailAgent,
)

from .tools import (
    SendEmailTool,
    DraftEmailTool,
    ReplyEmailTool,
    ForwardEmailTool,
    DeleteEmailTool,
    DownloadAttachmentTool
)

__all__ = [
    "EmailAgent",
    "SendEmailTool",
    "DraftEmailTool",
    "ReplyEmailTool",
    "ForwardEmailTool",
    "DeleteEmailTool",
    "DownloadAttachmentTool"
]