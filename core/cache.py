import re
from collections import OrderedDict, defaultdict
from functools import lru_cache
from typing import Optional, DefaultDict

from google_client.services.gmail import EmailMessage
from langchain_core.runnables import RunnableConfig


def remove_non_ascii(text):
    return text.encode("ascii", "ignore").decode("ascii")


class EmailCache:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.max_size = 1000
        self._store: OrderedDict = OrderedDict()

    def get(self, message_id: str) -> Optional[dict]:
        if email := self._store.get(message_id):
            self._store.move_to_end(message_id)
            return email

        return None

    def save(self, email: EmailMessage) -> dict:
        if email.message_id in self._store:
            self._store.move_to_end(email.message_id)
            return self._store.get(email.message_id)

        save_format = email.to_dict()
        save_format = {
            "message_id": save_format["message_id"],
            "thread_id": save_format["thread_id"],
            "from": save_format["sender"],
            "to": save_format["recipients"],
            "date_time": save_format["date_time"],
            "subject": save_format["subject"],
            "label_ids": save_format["labels"],
            "snippet": re.sub(r'(\s)\s+', r'\1', save_format["snippet"]),
            "has_attachments": email.has_attachments(),
            "body": re.sub(r'(\s)\s+', r'\1', save_format["body"]),
            "attachments": save_format["attachments"],
        }

        self._store[email.message_id] = save_format

        if len(self._store) > self.max_size:
            self._store.popitem(last=False)

        return save_format


@lru_cache(maxsize=1000)
def _get_email_cache(user_id: str) -> EmailCache:
    return EmailCache(user_id)

def get_email_cache(config: RunnableConfig) -> EmailCache:
    return _get_email_cache(config['configurable'].get('user_id'))
