from typing import Callable, Optional

from src.core.config import REDIS_URL, RQ_JOB_TIMEOUT, RQ_QUEUE_NAME, RQ_RESULT_TTL


class QueueDispatchError(RuntimeError):
    pass


class QueueGateway:
    def enqueue(self, task_id: str) -> str:
        raise NotImplementedError


class InlineQueueGateway(QueueGateway):
    def __init__(self, runner: Callable[[str], None]) -> None:
        self.runner = runner

    def enqueue(self, task_id: str) -> str:
        self.runner(task_id)
        return task_id


class RQQueueGateway(QueueGateway):
    def __init__(
        self,
        redis_url: str = REDIS_URL,
        queue_name: str = RQ_QUEUE_NAME,
        job_timeout: int = RQ_JOB_TIMEOUT,
        result_ttl: int = RQ_RESULT_TTL,
    ) -> None:
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.job_timeout = job_timeout
        self.result_ttl = result_ttl

    def enqueue(self, task_id: str) -> str:
        try:
            from redis import Redis
            from rq import Queue
        except ImportError as exc:
            raise QueueDispatchError("RQ queue dependencies are not installed.") from exc

        from src.api.services.task_dispatcher import process_task_job

        connection = Redis.from_url(self.redis_url)
        queue = Queue(
            name=self.queue_name,
            connection=connection,
            default_timeout=self.job_timeout,
        )
        job = queue.enqueue(
            process_task_job,
            task_id,
            result_ttl=self.result_ttl,
            job_timeout=self.job_timeout,
        )
        return str(job.id)


def create_default_queue() -> QueueGateway:
    return RQQueueGateway()
