from fastapi.encoders import jsonable_encoder
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from backend.models.agent import AgentCard
from backend.models.request import A2ARequestAdapter, SendTaskRequest
from backend.models.json_rpc import JSONRPCResponse, InternalError
from backend.server.task_manager import TaskManager
import json
import logging

logger = logging.getLogger(__name__)


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)} not serializable')


class A2AServer:

    def __init__(
        self,
        host='0.0.0.0',
        port=5000,
        agent_card: AgentCard = None,
        task_manager: TaskManager = None
    ):
        self.host = host
        self.port = port
        self.agent_card = agent_card
        self.task_manager = task_manager
        self.app = Starlette()
        self.app.add_route('/', self._handle_request, methods=['POST'])
        self.app.add_route(
            '/.well-known/agent.json',
            self._get_agent_card,
            methods=['GET']
        )

    def start(self):
        if not self.agent_card or not self.task_manager:
            raise ValueError('Agent card and task manager are required')
        import uvicorn
        logger.info(f"🚀 Starting {self.agent_card.name} on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    async def _handle_request(self, request: Request):
        try:
            body = await request.json()
            logger.debug(f'Incoming request: {json.dumps(body, indent=2)}')
            
            json_rpc = A2ARequestAdapter.validate_python(body)
            
            if isinstance(json_rpc, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc)
            else:
                raise ValueError(f'Unsupported A2A method: {type(json_rpc)}')
            
            return self._create_response(result)
        except Exception as e:
            logger.error(f'Exception in request handler: {e}', exc_info=True)
            return JSONResponse(
                JSONRPCResponse(
                    id=None,
                    error=InternalError(message=str(e))
                ).model_dump(),
                status_code=400
            )

    def _create_response(self, result):
        if isinstance(result, JSONRPCResponse):
            return JSONResponse(
                content=jsonable_encoder(result.model_dump(exclude_none=True))
            )
        else:
            raise ValueError('Invalid response type')