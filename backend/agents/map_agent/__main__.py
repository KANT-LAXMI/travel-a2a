import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.server.server import A2AServer
from backend.models.agent import AgentCard, AgentCapabilities, AgentSkill
from backend.agents.map_agent.task_manager import MapTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    server = A2AServer(
        host="localhost",
        port=10003,
        agent_card=AgentCard(
            name="MapAgent",
            description="Creates interactive maps with itinerary locations and timing using OpenStreetMap",
            url="http://localhost:10003",
            version="1.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text", "html"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[AgentSkill(
                id="map",
                name="Map Visualizer",
                description="Extracts places from itinerary and creates interactive Leaflet maps with markers, routes, and timing (100% FREE - No API Key Required)",
                tags=["travel", "map", "visualization", "places", "leaflet", "openstreetmap"],
                examples=["Create a map for my Varanasi itinerary", "Show all places on a map"]
            )]
        ),
        task_manager=MapTaskManager()
    )
    server.start()


if __name__ == "__main__":
    main()
