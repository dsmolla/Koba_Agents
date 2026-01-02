import time
from google_client.services.tasks import TaskList


class TaskListCache:
    def __init__(self, ttl_second: int = 3600):
        self.cache = list()
        self.ttl_minute = ttl_second
        self.last_refresh = None

    def list_task_lists(self):
        if self.last_refresh and (time.time() - self.last_refresh) > self.ttl_minute:
            self.cache.clear()

        return self.cache

    def update_cache(self, task_lists: list[TaskList]):
        self.cache = [
            {'task_list_id': task_list.task_list_id, 'title': task_list.title}
            for task_list in task_lists
        ]
        self.last_refresh = time.time()

    def add_task_list(self, task_list: TaskList):
        self.cache.append({'task_list_id': task_list.task_list_id, 'title': task_list.title})

