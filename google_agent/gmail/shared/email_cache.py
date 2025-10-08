import re
from collections import OrderedDict
from typing import Optional

from google_client.services.gmail import EmailMessage


def remove_non_ascii(text):
    return text.encode("ascii", "ignore").decode("ascii")


class EmailCache(OrderedDict):
    def __init__(self, max_size=200):
        super().__init__()
        self.max_size = max_size

    def save(self, email: EmailMessage) -> dict:
        if email.message_id in self:
            self.move_to_end(email.message_id)

        save_format = email.to_dict()
        save_format = {
            "message_id": save_format["message_id"],
            "thread_id": save_format["thread_id"],
            "from": save_format["sender"],
            "to": save_format["recipients"],
            "date_time": save_format["date_time"],
            "subject": save_format["subject"],
            "label_ids": save_format["labels"],
            "snippet": re.sub(r'(\s)\s+', r'\1', save_format["snippet"].encode("ascii", "ignore").decode("ascii")),
            "has_attachments": email.has_attachments(),
            "body": re.sub(r'(\s)\s+', r'\1', save_format["body"].encode("ascii", "ignore").decode("ascii")),
            "attachments": save_format["attachments"],
        }

        self[email.message_id] = save_format

        if len(self) > self.max_size:
            self.popitem(last=False)

        return save_format

    def retrieve(self, message_id: str) -> Optional[dict]:
        if email := self.get(message_id):
            self.move_to_end(message_id)
            return email

        return None
