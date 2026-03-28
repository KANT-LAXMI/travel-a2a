"""
A2A Client
==========
Client for communicating with A2A agents
"""

import httpx
import logging
from typing import Dict, Any
from backend.models.task import Task

logger = logging.getLogger(__name__)


class A2AClient:
    """Client for A2A agent communication"""
    
    def __init__(self, url: str, timeout: float = 30.0):
        self.url = url.rstrip('/')
        self.timeout = timeout
        self._client = None

    async def send_task(self, payload: Dict[str, Any]) -> Task:
        """
        Send a task to an A2A agent
        
        Args:
            payload: Task payload with id, sessionId, and message
            
        Returns:
            Task object with response
            
        Raises:
            Exception: If request fails or response is invalid
        """
        request_data = {
            "jsonrpc": "2.0",
            "id": payload.get('id'),
            "method": "tasks/send",
            "params": {
                "id": payload.get('id'),
                "sessionId": payload.get('sessionId'),
                "message": payload.get('message')
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.url, json=request_data)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data and data['error']:
                    error_msg = data['error'].get('message', str(data['error']))
                    raise Exception(f"Agent error: {error_msg}")
                
                if 'result' not in data:
                    raise Exception("No result in response")
                
                return Task.model_validate(data['result'])
                
            except httpx.TimeoutException:
                logger.error(f"Timeout calling {self.url}")
                raise Exception(f"Request timeout after {self.timeout}s")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP {e.response.status_code} from {self.url}")
                raise Exception(f"HTTP error: {e.response.status_code}")
            except httpx.HTTPError as e:
                logger.error(f"HTTP error calling {self.url}: {e}")
                raise Exception(f"Connection error: {str(e)}")
            except Exception as e:
                logger.error(f"Error calling agent: {e}")
                raise
