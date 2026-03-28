import os
import json
import logging
from typing import List
import httpx
from backend.models.agent import AgentCard

logger = logging.getLogger(__name__)


class DiscoveryClient:

    def __init__(self, registry_file: str = None):
        if registry_file:
            self.registry_file = registry_file
        else:
            self.registry_file = os.path.join(
                os.path.dirname(__file__), 'agent_registry.json'
            )
        self.base_urls = self._load_registry()

    def _load_registry(self) -> List[str]:
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError('Registry file must contain a JSON list of URLs.')
            return data
        except FileNotFoundError:
            logger.warning(f'Registry file not found: {self.registry_file}')
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f'Error parsing registry file: {e}')
            return []

    async def list_agent_cards(self) -> List[AgentCard]:
        cards: List[AgentCard] = []
        async with httpx.AsyncClient() as client:
            for base in self.base_urls:
                url = base.rstrip('/') + '/.well-known/agent.json'
                try:
                    response = await client.get(url, timeout=5.0)
                    response.raise_for_status()
                    card = AgentCard.model_validate(response.json())
                    cards.append(card)
                    logger.info(f"Discovered agent: {card.name} at {base}")
                except Exception as e:
                    logger.warning(f'Failed to discover agent at {url}: {e}')
        return cards