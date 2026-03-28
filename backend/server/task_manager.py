from abc import ABC, abstractmethod
from typing import Dict
import asyncio
from backend.models.request import SendTaskRequest, SendTaskResponse, GetTaskRequest, GetTaskResponse
from backend.models.task import Task, TaskSendParams, TaskQueryParams, TaskStatus, TaskState


class TaskManager(ABC):

    @abstractmethod
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        pass

    @abstractmethod
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        pass


class InMemoryTaskManager(TaskManager):

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = asyncio.Lock()

    async def upsert_task(self, params: TaskSendParams) -> Task:
        async with self.lock:
            task = self.tasks.get(params.id)
            if task is None:
                task = Task(
                    id=params.id,
                    status=TaskStatus(state=TaskState.SUBMITTED),
                    history=[params.message]
                )
                self.tasks[params.id] = task
            else:
                task.history.append(params.message)
            return task

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        raise NotImplementedError('on_send_task() must be implemented in subclass')

    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        async with self.lock:
            query: TaskQueryParams = request.params
            task = self.tasks.get(query.id)
            if not task:
                return GetTaskResponse(
                    id=request.id,
                    error={'message': 'Task not found'}
                )
            task_copy = task.model_copy()
            if query.historyLength is not None:
                task_copy.history = task_copy.history[-query.historyLength:]
            else:
                task_copy.history = task_copy.history
            return GetTaskResponse(id=request.id, result=task_copy)