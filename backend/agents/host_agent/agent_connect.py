import uuid
import logging
from backend.client.client import A2AClient
from backend.models.task import Task

logger = logging.getLogger(__name__)


class AgentConnector:
    """Helper to connect and communicate with child agents"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        # Increase timeout for agent-to-agent calls (some agents like RAG may take longer)
        self.client = A2AClient(url=base_url, timeout=120.0)  # 2 minutes per agent
        logger.info(f'AgentConnector initialized for {name} at {base_url}')

    async def send_task(self, message: str, session_id: str) -> Task:
        """Send a task to the connected agent"""
        payload = {
            'id': uuid.uuid4().hex,
            'sessionId': session_id,
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': message}]
            }
        }
        
        logger.info(f"Sending task to {self.name}: {message[:50]}...")
        result = await self.client.send_task(payload)
        logger.info(f"Received response from {self.name}")
        return result