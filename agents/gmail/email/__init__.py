""" Handles email operations like sending, creating drafts, replying, forwarding, deleting and downloading attachments """

from .agent import (
    EmailAgent,
)

from .tools import (
    SendEmailTool,
    CreateDraftTool,
    ReplyEmailTool,
    ForwardEmailTool,
    DeleteEmailTool,
    DownloadAttachmentTool
)

__all__ = [
    "EmailAgent",
    "SendEmailTool",
    "CreateDraftTool",
    "ReplyEmailTool",
    "ForwardEmailTool",
    "DeleteEmailTool",
    "DownloadAttachmentTool"
]