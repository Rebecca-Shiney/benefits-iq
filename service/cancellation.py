import asyncio
from contextvars import ContextVar
from threading import Event


class WorkflowCancelled(Exception):
    pass


_cancellation: ContextVar[Event | None] = ContextVar("workflow_cancellation", default=None)


def check_cancelled():
    event = _cancellation.get()
    if event is not None and event.is_set():
        raise WorkflowCancelled("WORKFLOW_CANCELLED")


async def run_blocking(function, *args):
    check_cancelled()
    return await asyncio.to_thread(function, *args)


class WorkflowCancellation:
    def __init__(self):
        self.event = Event()
        self.token = None

    def __enter__(self):
        self.token = _cancellation.set(self.event)
        return self

    def cancel(self):
        self.event.set()

    def __exit__(self, *_):
        self.cancel()
        _cancellation.reset(self.token)
