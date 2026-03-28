from backend.server.task_manager import InMemoryTaskManager
from backend.models.request import SendTaskRequest, SendTaskResponse
from backend.models.task import Message, TaskStatus, TaskState, TextPart
from backend.agents.places_agent.agent import PlacesAgent
import logging

logger = logging.getLogger(__name__)


class PlacesTaskManager(InMemoryTaskManager):
    def __init__(self):
        super().__init__()
        self.agent = PlacesAgent()

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        logger.info(f"PlacesTaskManager received task: {request.params.id}")
        
        # Upsert task
        task = await self.upsert_task(request.params)
        
        # Get user query
        query = request.params.message.parts[0].text
        
        # Process with agent
        result = self.agent.run(query)
        
        # Create reply message
        reply = Message(role="agent", parts=[TextPart(text=result)])
        
        # Update task
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(reply)
        
        logger.info(f"PlacesTaskManager completed task: {request.params.id}")
        return SendTaskResponse(id=request.id, result=task)