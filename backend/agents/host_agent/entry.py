"""
🚀 HOST AGENT ENTRY POINT
=========================

Starts the Host Agent with SK Planner orchestration
"""

import sys
import os
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.utilities.discovery import DiscoveryClient
from backend.server.server import A2AServer
from backend.models.agent import AgentCard, AgentCapabilities, AgentSkill
from backend.agents.host_agent.orchestrator import OrchestratorAgent, OrchestratorTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for Host Agent
    
    1. Discovers child agents via registry
    2. Initializes SK Planner
    3. Starts A2A server
    """
    
    logger.info("=" * 80)
    logger.info("🚀 STARTING HOST AGENT WITH SK PLANNER")
    logger.info("=" * 80)
    
    # Discover child agents
    logger.info("🔍 Discovering child agents...")
    discovery = DiscoveryClient()
    agent_cards = asyncio.run(discovery.list_agent_cards())
    
    if not agent_cards:
        logger.error("❌ No child agents found!")
        logger.error("")
        logger.error("Please start the required agents:")
        logger.error("  python -m agents.budget_agent")
        logger.error("  python -m agents.places_agent")
        logger.error("  python -m agents.map_agent")
        logger.error("  python -m agents.rag_agent")
        logger.error("")
        return
    
    logger.info(f"✅ Discovered {len(agent_cards)} agents:")
    for card in agent_cards:
        logger.info(f"   - {card.name} at {card.url}")

    # Verify all required agents
    required_agents = ["BudgetAgent", "PlacesAgent", "MapAgent", "RAGAgent"]
    discovered_names = [card.name for card in agent_cards]
    missing = [a for a in required_agents if a not in discovered_names]
    
    if missing:
        logger.warning("")
        logger.warning(f"⚠️ WARNING: Missing agents: {missing}")
        logger.warning("Some functionality will be limited")
        logger.warning("")

    # Create orchestrator with SK Planner
    logger.info("🧠 Initializing Orchestrator with SK Planner...")
    try:
        orchestrator = OrchestratorAgent(agent_cards)
        logger.info("✅ Orchestrator ready with AI orchestration!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}", exc_info=True)
        logger.error("")
        logger.error("Make sure:")
        logger.error("  1. Azure OpenAI credentials are set in .env")
        logger.error("  2. semantic-kernel is installed: pip install semantic-kernel")
        logger.error("")
        return

    # Start A2A server
    logger.info("🌐 Starting A2A Server...")
    server = A2AServer(
        host="localhost",
        port=10000,
        agent_card=AgentCard(
            name="TravelHostAgent",
            description="🧠 AI-Powered Travel Orchestrator using Semantic Kernel - Intelligently coordinates budget, itinerary, maps, and knowledge agents with automatic multi-step reasoning",
            url="http://localhost:10000",
            version="2.0-SK",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[AgentSkill(
                id="travel-orchestration",
                name="AI Travel Orchestrator",
                description="Intelligent orchestration of travel planning using SK Planner. Handles complex queries like 'plan trip AND tell me challenges' by automatically reasoning about which agents to call and in what order.",
                tags=["travel", "orchestration", "planning", "ai", "semantic-kernel"],
                examples=[
                    "Plan a 2-day Goa trip under 15k",
                    "What challenges exist in travel planning?",
                    "Plan a Varanasi trip and tell me about itinerary challenges",
                    "Create budget and itinerary for Mumbai weekend"
                ]
            )]
        ),
        task_manager=OrchestratorTaskManager(agent=orchestrator)
    )
    
    logger.info("=" * 80)
    logger.info("✅ HOST AGENT READY")
    logger.info("=" * 80)
    logger.info("🎯 Features:")
    logger.info("   - AI-powered orchestration via SK Planner")
    logger.info("   - Automatic multi-agent coordination")
    logger.info("   - Handles complex multi-intent queries")
    logger.info("   - Dynamic reasoning about agent selection")
    logger.info("=" * 80)
    
    server.start()


if __name__ == "__main__":
    main()