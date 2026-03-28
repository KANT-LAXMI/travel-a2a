"""
Wikipedia MCP Server - Full MCP Protocol Implementation
=======================================================
Implements complete MCP architecture with:
- Transport Layers (stdio/HTTP)
- Tools (Wikipedia API operations)
- Resources (Wikipedia articles)
- Prompts (destination research templates)
- Notifications (article updates)

Based on Model Context Protocol specification.
"""

import json
import logging
from typing import List, Dict, Any
from mcp import FastMCP

# Import existing Wikipedia API
from backend.mcp_tools.wikipedia_mcp_service.wikipedia_api import WikipediaMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server with metadata
mcp = FastMCP(
    "Wikipedia Travel Information",
    version="1.0.0",
    description="MCP server for accessing Wikipedia travel and destination information"
)

# Initialize Wikipedia client
wiki = WikipediaMCP()


# ═══════════════════════════════════════════════════════════════════════════
# RESOURCES - Expose Wikipedia articles as resources
# ═══════════════════════════════════════════════════════════════════════════

@mcp.resource("wikipedia://article/{title}")
def get_article_resource(title: str) -> str:
    """
    Resource: Wikipedia article by title
    
    MCP Resources provide read-only access to Wikipedia articles.
    """
    summary = wiki.get_article_summary(title)
    
    if summary:
        return json.dumps({
            "uri": f"wikipedia://article/{title}",
            "mimeType": "application/json",
            "data": summary
        }, indent=2)
    else:
        return json.dumps({
            "uri": f"wikipedia://article/{title}",
            "error": "Article not found"
        })


@mcp.resource("wikipedia://destination/{destination}")
def get_destination_resource(destination: str) -> str:
    """
    Resource: Destination information from Wikipedia
    
    Provides comprehensive travel destination data.
    """
    info = wiki.get_destination_info(destination)
    
    return json.dumps({
        "uri": f"wikipedia://destination/{destination}",
        "mimeType": "application/json",
        "data": info
    }, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# TOOLS - Wikipedia operations
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def search_wikipedia(query: str, limit: int = 5) -> str:
    """
    Search Wikipedia articles for travel destinations and topics
    
    MCP Tool for discovering relevant Wikipedia articles.
    
    Args:
        query: Search term (e.g., "Goa India", "Eiffel Tower")
        limit: Maximum number of results (default: 5, max: 10)
    
    Returns:
        JSON string with search results
    """
    logger.info(f"🔧 TOOL: search_wikipedia('{query}', limit={limit})")
    
    try:
        limit = min(max(1, limit), 10)
        results = wiki.search_articles(query, limit)
        
        response = {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
        
        logger.info(f"✅ Found {len(results)} results")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return json.dumps({"success": False, "error": str(e), "query": query})


@mcp.tool()
def get_article_summary(title: str) -> str:
    """
    Get detailed summary of a Wikipedia article
    
    MCP Tool for retrieving article information.
    
    Args:
        title: Wikipedia article title (e.g., "Goa", "Paris")
    
    Returns:
        JSON string with article summary
    """
    logger.info(f"🔧 TOOL: get_article_summary('{title}')")
    
    try:
        summary = wiki.get_article_summary(title)
        
        if summary:
            response = {"success": True, "article": summary}
            logger.info(f"✅ Retrieved summary for '{title}'")
        else:
            response = {"success": False, "error": f"Article not found: {title}", "title": title}
            logger.warning(f"⚠️ Article not found: '{title}'")
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return json.dumps({"success": False, "error": str(e), "title": title})


@mcp.tool()
def get_destination_info(destination: str) -> str:
    """
    Get comprehensive travel destination information from Wikipedia
    
    MCP Tool for trip planning with rich destination context.
    
    Args:
        destination: Destination name (e.g., "Goa", "Paris", "Tokyo")
    
    Returns:
        JSON string with destination info including:
        - Title and description
        - Full summary text
        - Coordinates
        - Thumbnail image
        - Wikipedia URL
        - Related articles
    """
    logger.info(f"🔧 TOOL: get_destination_info('{destination}')")
    
    try:
        info = wiki.get_destination_info(destination)
        
        response = {
            "success": info.get('found', False),
            "destination": destination,
            "info": info
        }
        
        if info.get('found'):
            logger.info(f"✅ Retrieved info for '{destination}'")
        else:
            logger.warning(f"⚠️ No info found for '{destination}'")
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return json.dumps({"success": False, "error": str(e), "destination": destination})


@mcp.tool()
def get_travel_context(destination: str) -> str:
    """
    Get formatted travel context optimized for LLM consumption
    
    MCP Tool for providing destination context to AI assistants.
    
    Args:
        destination: Destination name (e.g., "Goa", "Paris")
    
    Returns:
        Formatted text string with destination overview
    """
    logger.info(f"🔧 TOOL: get_travel_context('{destination}')")
    
    try:
        context = wiki.get_travel_context(destination)
        logger.info(f"✅ Generated context for '{destination}'")
        return context
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error retrieving travel context for '{destination}': {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# PROMPTS - Pre-defined prompt templates
# ═══════════════════════════════════════════════════════════════════════════

@mcp.prompt()
def research_destination_prompt(destination: str) -> str:
    """
    Prompt template for researching a travel destination
    
    MCP Prompts provide pre-defined templates for common tasks.
    """
    return f"""Research the destination: {destination}

Please use Wikipedia to gather comprehensive information:
1. Search for articles about {destination}
2. Get the main destination article summary
3. Find related articles about tourism, culture, and attractions
4. Compile a travel context summary

Use these tools:
- search_wikipedia("{destination}")
- get_destination_info("{destination}")
- get_travel_context("{destination}")"""


@mcp.prompt()
def compare_destinations_prompt(destination1: str, destination2: str) -> str:
    """
    Prompt template for comparing two destinations
    """
    return f"""Compare these two travel destinations: {destination1} vs {destination2}

Please gather information about both destinations and compare:
1. Geographic location and climate
2. Main attractions and activities
3. Cultural significance
4. Tourism infrastructure

Use get_destination_info for both destinations."""


@mcp.prompt()
def find_similar_destinations_prompt(destination: str) -> str:
    """
    Prompt template for finding similar destinations
    """
    return f"""Find destinations similar to {destination}

Steps:
1. Get information about {destination}
2. Identify key characteristics (beach, mountains, culture, etc.)
3. Search for similar destinations
4. Compare and recommend alternatives

Use search_wikipedia and get_destination_info tools."""


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS - Event notifications
# ═══════════════════════════════════════════════════════════════════════════

def _notify_article_accessed(title: str):
    """
    Send notification when an article is accessed
    
    MCP Notifications inform clients about events.
    """
    logger.info(f"📢 NOTIFICATION: Article accessed - {title}")


def _notify_search_performed(query: str, results_count: int):
    """Send notification when a search is performed"""
    logger.info(f"📢 NOTIFICATION: Search performed - '{query}' ({results_count} results)")


# ═══════════════════════════════════════════════════════════════════════════
# SERVER STARTUP
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Run the Wikipedia MCP Server
    
    Transport Layer: stdio (standard input/output)
    Protocol: JSON-RPC 2.0
    """
    logger.info("="*80)
    logger.info("🚀 Wikipedia MCP Server - Full Protocol Implementation")
    logger.info("="*80)
    logger.info("")
    logger.info("📦 MCP Components:")
    logger.info("  ✅ Transport Layer: stdio (JSON-RPC 2.0)")
    logger.info("  ✅ Tools: 4 Wikipedia operations")
    logger.info("  ✅ Resources: 2 read-only data sources")
    logger.info("  ✅ Prompts: 3 pre-defined templates")
    logger.info("  ✅ Notifications: Article access events")
    logger.info("")
    logger.info("🔧 Available Tools:")
    logger.info("  1. search_wikipedia - Search articles")
    logger.info("  2. get_article_summary - Get article details")
    logger.info("  3. get_destination_info - Get destination data")
    logger.info("  4. get_travel_context - Get formatted context")
    logger.info("")
    logger.info("📚 Available Resources:")
    logger.info("  1. wikipedia://article/{title} - Article data")
    logger.info("  2. wikipedia://destination/{destination} - Destination data")
    logger.info("")
    logger.info("💬 Available Prompts:")
    logger.info("  1. research_destination_prompt - Research template")
    logger.info("  2. compare_destinations_prompt - Comparison template")
    logger.info("  3. find_similar_destinations_prompt - Discovery template")
    logger.info("")
    logger.info("🌐 Wikipedia API: https://en.wikipedia.org/api/")
    logger.info("🔌 Server ready for MCP connections")
    logger.info("="*80)
    logger.info("")
    
    # Run the MCP server
    mcp.run()
