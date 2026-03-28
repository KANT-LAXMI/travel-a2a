import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.server.server import A2AServer
from backend.models.agent import AgentCard, AgentCapabilities, AgentSkill
from backend.agents.budget_agent.task_manager import BudgetTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    server = A2AServer(
        host="localhost",
        port=10001,
        agent_card=AgentCard(
            name="BudgetAgent",
            description="Creates detailed travel budget breakdowns",
            url="http://localhost:10001",
            version="1.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[AgentSkill(
                id="budget",
                name="Budget Planner",
                description="Creates detailed trip cost breakdowns with realistic estimates",
                tags=["travel", "budget", "planning"],
                examples=["Create a budget for 2-day Goa trip under 15k"]
            )]
        ),
        task_manager=BudgetTaskManager()
    )
    server.start()


if __name__ == "__main__":
    main()