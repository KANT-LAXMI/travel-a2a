from typing import Annotated, Union, Literal
from pydantic import Field
from pydantic.type_adapter import TypeAdapter
from backend.models.json_rpc import JSONRPCRequest, JSONRPCResponse
from backend.models.task import Task, TaskSendParams, TaskQueryParams


class SendTaskRequest(JSONRPCRequest):
    method: Literal['tasks/send'] = 'tasks/send'
    params: TaskSendParams


class GetTaskRequest(JSONRPCRequest):
    method: Literal['tasks/get'] = 'tasks/get'
    params: TaskQueryParams


A2ARequestAdapter = TypeAdapter(
    Annotated[Union[SendTaskRequest, GetTaskRequest], Field(discriminator='method')]
)


class SendTaskResponse(JSONRPCResponse):
    result: Task | None = None


class GetTaskResponse(JSONRPCResponse):
    result: Task | None = None