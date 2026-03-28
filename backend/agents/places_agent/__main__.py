import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.server.server import A2AServer
from backend.models.agent import AgentCard, AgentCapabilities, AgentSkill
from backend.agents.places_agent.task_manager import PlacesTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    server = A2AServer(
        host="localhost",
        port=10002,
        agent_card=AgentCard(
            name="PlacesAgent",
            description="Creates detailed travel itineraries with places to visit",
            url="http://localhost:10002",
            version="1.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[AgentSkill(
                id="itinerary",
                name="Itinerary Planner",
                description="Creates day-by-day itineraries with specific places and timing",
                tags=["travel", "itinerary", "places", "planning"],
                examples=["Create an itinerary for 2 days in Goa"]
            )]
        ),
        task_manager=PlacesTaskManager()
    )
    server.start()


if __name__ == "__main__":
    main()