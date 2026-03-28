"""
Semantic Kernel Plugins for Agent-to-Agent Communication

═══════════════════════════════════════════════════════════════════════════
HOW AGENT SELECTION WORKS - THE PLUGIN LAYER
═══════════════════════════════════════════════════════════════════════════

This file defines SK Plugins that expose our agents as callable functions.
These plugins are THE KEY to how Semantic Kernel decides which agents to call.

ARCHITECTURE:
-------------
1. Each plugin wraps one or more agents
2. Each method is decorated with @kernel_function
3. The decorator includes a "description" - THIS IS CRITICAL!
4. The LLM reads these descriptions to decide which functions to call

HOW THE LLM SEES THIS:
-----------------------
When SK Planner runs, it sends the LLM:
- User query: "Plan 5 day Goa trip"
- Available functions with descriptions:
  * plan_trip_budget: "Create a detailed budget breakdown..."
  * plan_trip_itinerary: "Create a detailed day-by-day itinerary..."
  * create_trip_map: "Create an interactive map visualization..."
  * answer_knowledge_question: "Answer questions using knowledge base..."

The LLM reads the descriptions and thinks:
"User wants to plan a trip. I need budget, itinerary, and map functions!"
→ Calls: plan_trip_budget + plan_trip_itinerary + create_trip_map

FUNCTION DESCRIPTION = AGENT SELECTION CRITERIA
------------------------------------------------
The description in @kernel_function is how the LLM decides to call it!
- Good description = LLM knows when to use it
- Bad description = LLM might not call it when needed

RESULT TRACKING:
----------------
Each function stores its result in planner._agent_results
This allows the planner to format the output beautifully after all agents finish.

═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging
import json
from typing import Annotated, Optional, Any
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)


class TripPlanningPlugin:
    """
    SK Plugin for trip planning operations
    Exposes BudgetAgent, PlacesAgent, and MapAgent as SK functions
    """

    def __init__(self, connectors: dict, planner=None):
        """
        Args:
            connectors: Dict of agent name -> AgentConnector
            planner: Reference to SKPlanner for result tracking
        """
        self.connectors = connectors
        self.planner = planner
        logger.info("✅ TripPlanningPlugin initialized")

    @kernel_function(
        name="plan_trip_budget",
        # ═══════════════════════════════════════════════════════════════════
        # 🎯 FUNCTION DESCRIPTION - THE KEY TO AGENT SELECTION
        # ═══════════════════════════════════════════════════════════════════
        # This description is read by the LLM to decide when to call this function!
        # 
        # WHAT MAKES A GOOD DESCRIPTION:
        # - Clear purpose: "Create a detailed budget breakdown"
        # - What it includes: "transportation, accommodation, food, activities"
        # - When to use it: "when the user needs cost estimates or budget planning"
        # 
        # HOW LLM USES THIS:
        # Query: "Plan 5 day Goa trip"
        # → LLM reads: "needs cost estimates or budget planning for a trip"
        # → LLM thinks: "User wants to plan a trip, they'll need budget!"
        # → LLM decides: CALL THIS FUNCTION
        # 
        # Query: "What are challenges in planning?"
        # → LLM reads: "needs cost estimates or budget planning"
        # → LLM thinks: "User is asking a question, not planning a trip"
        # → LLM decides: DON'T CALL THIS FUNCTION
        # ═══════════════════════════════════════════════════════════════════
        description="Create a detailed budget breakdown for a trip including transportation, accommodation, food, activities, and miscellaneous costs. Use this when the user needs cost estimates or budget planning for a trip."
    )
    async def plan_trip_budget(
        self,
        trip_query: Annotated[str, "The trip planning query including destination, duration, and budget constraints"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Call BudgetAgent to create trip budget
        
        EXECUTION FLOW:
        1. SK Planner decides to call this function (based on description above)
        2. This method is invoked with trip_query and session_id
        3. We call BudgetAgent via connector (HTTP to port 10001)
        4. BudgetAgent processes and returns budget breakdown
        5. We store result in planner._agent_results['budget']
        6. Return result to SK (LLM can see it)
        """
        logger.info(f"🔌 SK Function: plan_trip_budget called")
        
        if "BudgetAgent" not in self.connectors:
            return "❌ BudgetAgent is not available"
        
        try:
            # Call BudgetAgent via A2A protocol (HTTP to port 10001)
            task = await self.connectors["BudgetAgent"].send_task(trip_query, session_id)
            result = task.history[-1].parts[0].text
            
            # ═══════════════════════════════════════════════════════════════
            # 📊 STORE RESULT FOR FORMATTING
            # ═══════════════════════════════════════════════════════════════
            # This is crucial! We store the result so _format_response() knows:
            # 1. That this agent was called
            # 2. What the response was
            # This allows beautiful formatting of the final output
            # ═══════════════════════════════════════════════════════════════
            if self.planner:
                self.planner._agent_results['budget'] = result
            
            logger.info("✅ BudgetAgent completed via SK")
            return result
        except Exception as e:
            logger.error(f"❌ BudgetAgent error: {e}")
            return f"❌ Error getting budget: {str(e)}"

    @kernel_function(
        name="plan_trip_itinerary",
        # ═══════════════════════════════════════════════════════════════════
        # 🎯 ITINERARY FUNCTION DESCRIPTION
        # ═══════════════════════════════════════════════════════════════════
        # LLM uses this to decide when to call PlacesAgent
        # Keywords: "day-by-day", "places to visit", "itinerary"
        # ═══════════════════════════════════════════════════════════════════
        description="Create a detailed day-by-day itinerary with specific places to visit, timing, activities, and must-see attractions. Use this when the user needs an itinerary or wants to know what places to visit."
    )
    async def plan_trip_itinerary(
        self,
        trip_query: Annotated[str, "The trip planning query including destination and duration"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Call PlacesAgent to create trip itinerary
        
        EXECUTION FLOW:
        1. SK Planner calls this based on description
        2. We call PlacesAgent (HTTP to port 10002)
        3. PlacesAgent returns day-by-day itinerary
        4. Store in _agent_results['places']
        5. Return to SK
        """
        logger.info(f"🔌 SK Function: plan_trip_itinerary called")
        
        if "PlacesAgent" not in self.connectors:
            return "❌ PlacesAgent is not available"
        
        try:
            task = await self.connectors["PlacesAgent"].send_task(trip_query, session_id)
            result = task.history[-1].parts[0].text
            
            # Store result for formatting
            if self.planner:
                self.planner._agent_results['places'] = result
            
            logger.info("✅ PlacesAgent completed via SK")
            return result
        except Exception as e:
            logger.error(f"❌ PlacesAgent error: {e}")
            return f"❌ Error getting itinerary: {str(e)}"

    @kernel_function(
        name="create_trip_map",
        # ═══════════════════════════════════════════════════════════════════
        # 🎯 MAP FUNCTION DESCRIPTION
        # ═══════════════════════════════════════════════════════════════════
        # LLM uses this to decide when to call MapAgent
        # Keywords: "interactive map", "visualization", "visual map"
        # IMPORTANT: This should be called AFTER plan_trip_itinerary
        # ═══════════════════════════════════════════════════════════════════
        description="Create an interactive map visualization with markers for all places in the itinerary, including routes and timing. Use this AFTER calling plan_trip_itinerary to visualize the places on a map. This requires the itinerary to be generated first."
    )
    async def create_trip_map(
        self,
        trip_query: Annotated[str, "The trip planning query or itinerary text to visualize"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Call MapAgent to create interactive map
        
        EXECUTION FLOW:
        1. SK Planner calls this based on description (AFTER itinerary is created)
        2. Wait for itinerary to be available in _agent_results['places']
        3. Pass itinerary text to MapAgent (HTTP to port 10003)
        4. MapAgent extracts locations and creates map
        5. Store in _agent_results['map']
        6. _format_trip_plan() will extract HTML and save to file
        """
        logger.info(f"🔌 SK Function: create_trip_map called")
        
        if "MapAgent" not in self.connectors:
            return "❌ MapAgent is not available"
        
        try:
            # 🔥 FIX: Wait for itinerary to be available (with timeout)
            import asyncio
            itinerary_text = trip_query
            max_wait_seconds = 30
            wait_interval = 0.5
            elapsed = 0
            
            logger.info("⏳ Waiting for itinerary to be generated...")
            
            while elapsed < max_wait_seconds:
                if self.planner and self.planner._agent_results.get('places'):
                    # Extract the display text from the structured response
                    import json
                    try:
                        places_data = json.loads(self.planner._agent_results['places'])
                        if 'display' in places_data and 'text' in places_data['display']:
                            itinerary_text = places_data['display']['text']
                            logger.info(f"✅ Itinerary ready after {elapsed:.1f}s - using for map generation")
                            break
                    except Exception as parse_error:
                        logger.warning(f"⚠️ Could not parse places data: {parse_error}")
                        break
                
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
            
            if elapsed >= max_wait_seconds:
                logger.warning(f"⚠️ Timeout waiting for itinerary after {max_wait_seconds}s, using original query")
            
            task = await self.connectors["MapAgent"].send_task(itinerary_text, session_id)
            result = task.history[-1].parts[0].text
            
            # Store result for formatting
            if self.planner:
                self.planner._agent_results['map'] = result
            
            logger.info("✅ MapAgent completed via SK")
            return result
        except Exception as e:
            logger.error(f"❌ MapAgent error: {e}")
            return f"❌ Error creating map: {str(e)}"


class KnowledgeQAPlugin:
    """
    SK Plugin for knowledge base question answering
    Exposes RAGAgent as SK function
    """

    def __init__(self, connectors: dict, planner=None, trip_plugin=None):
        """
        Args:
            connectors: Dict of agent name -> AgentConnector
            planner: Reference to SKPlanner for result tracking
            trip_plugin: Reference to TripPlanningPlugin for modify operations
        """
        self.connectors = connectors
        self.planner = planner
        self.trip_plugin = trip_plugin
        logger.info("✅ KnowledgeQAPlugin initialized")

    @kernel_function(
        name="answer_knowledge_question",
        # ═══════════════════════════════════════════════════════════════════
        # 🎯 KNOWLEDGE Q&A FUNCTION DESCRIPTION
        # ═══════════════════════════════════════════════════════════════════
        # This is THE KEY for RAG-based queries!
        # 
        # LLM uses this to decide when to call RAGAgent
        # Keywords: "questions", "knowledge base", "PDF documents", "RAG"
        # 
        # IMPORTANT EXAMPLES IN DESCRIPTION:
        # - "What is X?" → LLM sees this pattern, calls this function
        # - "Explain Y" → LLM sees this pattern, calls this function
        # - "Tell me about Z" → LLM sees this pattern, calls this function
        # - "What challenges exist" → LLM sees this pattern, calls this function
        # 
        # This is why "Plan trip and tell me about challenges" works:
        # - LLM sees "plan trip" → calls trip functions
        # - LLM sees "tell me about" → calls this function
        # - Both get called! (if system message says to call both)
        # ═══════════════════════════════════════════════════════════════════
        description="Answer questions using the knowledge base (PDF documents) via RAG (Retrieval Augmented Generation). Use this when the user asks for information, explanations, facts, or wants to know about concepts from the documents. Examples: 'What is X?', 'Explain Y', 'Tell me about Z', 'What challenges exist in...'"
    )
    async def answer_knowledge_question(
        self,
        question: Annotated[str, "The question to answer from the knowledge base"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Call RAGAgent to answer questions from documents
        
        EXECUTION FLOW:
        1. SK Planner calls this when user asks a question
        2. We call RAGAgent (HTTP to port 10004)
        3. RAGAgent:
           - Searches vector database for relevant chunks
           - Uses LLM to generate answer from retrieved context
        4. Store in _agent_results['knowledge']
        5. _format_qa_response() will format it beautifully
        """
        logger.info(f"🔌 SK Function: answer_knowledge_question called")
        
        if "RAGAgent" not in self.connectors:
            return "❌ RAGAgent is not available"
        
        try:
            task = await self.connectors["RAGAgent"].send_task(question, session_id)
            result = task.history[-1].parts[0].text
            
            # Store result for formatting
            if self.planner:
                self.planner._agent_results['knowledge'] = result
            
            logger.info("✅ RAGAgent completed via SK")
            return result
        except Exception as e:
            logger.error(f"❌ RAGAgent error: {e}")
            return f"❌ Error answering question: {str(e)}"


    @kernel_function(
        name="modify_existing_plan",
        description="Modify an existing travel plan based on user's follow-up request. Use when user says 'make it cheaper', 'add activities', 'change duration', etc. Requires previous plan context."
    )
    async def modify_existing_plan(
        self,
        modification_request: Annotated[str, "What the user wants to modify (e.g., 'make it cheaper', 'add water sports')"],
        kernel: Optional[Any] = None,
        arguments: Optional[Any] = None
    ) -> str:
        """
        Modify existing travel plan based on user request
        
        This function handles follow-up queries like:
        - "Make it cheaper"
        - "Add water sports"
        - "Change to 3 days"
        
        Note: session_id is retrieved from KernelArguments
        """
        # Get session_id from kernel arguments
        session_id = arguments.get('session_id', 'unknown') if arguments else 'unknown'
        
        logger.info("=" * 80)
        logger.info("🔄 MODIFY EXISTING PLAN CALLED")
        logger.info(f"🔄 Modification request: {modification_request}")
        logger.info(f"🔄 Session ID: {session_id}")
        logger.info("=" * 80)
        
        try:
            # Get previous plan from database
            from database.db_manager import TravelBuddyDB
            db = TravelBuddyDB()
            
            logger.info(f"🔍 Querying database for session: {session_id[:16]}...")
            last_plan = db.get_last_plan(session_id)
            
            logger.info(f"🔍 Last plan retrieved: {bool(last_plan)}")
            if last_plan:
                logger.info(f"✅ Found plan:")
                logger.info(f"   - ID: {last_plan.get('id')}")
                logger.info(f"   - Destination: {last_plan.get('destination')}")
                logger.info(f"   - Duration: {last_plan.get('duration_days')} days")
                logger.info(f"   - Created: {last_plan.get('created_at')}")
            else:
                logger.warning("❌ No previous plan found in database")
                logger.warning(f"❌ Session ID searched: {session_id}")
                
                # Debug: Check if ANY plans exist
                import psycopg2
                from backend.config import Config
                conn = psycopg2.connect(Config.DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM travel_plans")
                total_plans = cursor.fetchone()[0]
                logger.warning(f"❌ Total plans in database: {total_plans}")
                
                cursor.execute("SELECT id, destination, session_id, created_at FROM travel_plans ORDER BY created_at DESC LIMIT 3")
                recent_plans = cursor.fetchall()
                logger.warning(f"❌ Recent plans:")
                for plan in recent_plans:
                    logger.warning(f"   - {plan[0][:8]}... | {plan[1]} | Session: {plan[2][:16]}... | {plan[3]}")
                conn.close()
                
                return "❌ There is no previous plan found for your session. Please create a new travel plan first before requesting changes."
            
            # Extract context from last plan
            destination = last_plan.get('destination', 'Unknown')
            budget_data = last_plan.get('budget', {})
            budget_total = budget_data.get('total', 0) if budget_data else 0
            duration = last_plan.get('duration_days', 0)
            
            logger.info(f"📊 Plan details - Destination: {destination}, Budget: ₹{budget_total}, Duration: {duration} days")
            
            # Build context-aware query
            context_query = f"""
Previous Plan Context:
- Destination: {destination}
- Budget: ₹{budget_total}
- Duration: {duration} days

User's Modification Request: {modification_request}

Please modify the plan according to the user's request while keeping the context in mind.
"""
            
            logger.info(f"📝 Context query built: {context_query[:200]}...")
            
            # Detect modification type and call appropriate agent
            from agents.host_agent.context_detector import ContextDetector
            detector = ContextDetector()
            mod_type = detector.get_modification_type(modification_request)
            
            logger.info(f"🔍 Modification type detected: {mod_type}")
            
            if mod_type == 'budget':
                # Call budget agent with context
                budget_intent = detector.extract_budget_intent(modification_request)
                if budget_intent['action'] == 'reduce':
                    context_query += f"\nReduce budget by 20-30%. Suggest cheaper alternatives."
                else:
                    context_query += f"\nIncrease budget. Suggest premium options."
                
                result = await self.trip_plugin.plan_trip_budget(context_query, session_id)
                
            elif mod_type == 'activity':
                # Call places agent with activity modification
                activity_intent = detector.extract_activities(modification_request)
                context_query += f"\n{activity_intent['action'].title()} these activities: {', '.join(activity_intent['activities'])}"
                result = await self.trip_plugin.plan_trip_itinerary(context_query, session_id)
                
            elif mod_type == 'duration':
                # Call both budget and places for duration change
                new_duration = detector.extract_duration(modification_request)
                context_query += f"\nChange duration to {new_duration} days."
                budget_result = await self.trip_plugin.plan_trip_budget(context_query, session_id)
                places_result = await self.trip_plugin.plan_trip_itinerary(context_query, session_id)
                map_result = await self.trip_plugin.create_trip_map(context_query, session_id)
                result = f"{budget_result}\n\n{places_result}\n\n{map_result}"
                
            else:
                # General modification - call all agents
                budget_result = await self.trip_plugin.plan_trip_budget(context_query, session_id)
                places_result = await self.trip_plugin.plan_trip_itinerary(context_query, session_id)
                map_result = await self.trip_plugin.create_trip_map(context_query, session_id)
                result = f"{budget_result}\n\n{places_result}\n\n{map_result}"
            
            logger.info("✅ Plan modification complete")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error modifying plan: {e}", exc_info=True)
            return f"❌ Error modifying plan: {str(e)}"
    
    @kernel_function(
        name="get_destination_info_wikipedia",
        description="Get detailed destination information from Wikipedia including history, culture, geography, and tourist attractions. Use this when planning a trip to provide rich context about the destination. Examples: 'Tell me about Goa', 'What is special about Paris', 'Give me background on Tokyo'."
    )
    async def get_destination_info_wikipedia(
        self,
        destination: Annotated[str, "The destination name to get information about (e.g., 'Goa', 'Paris', 'Tokyo')"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Get destination information from Wikipedia via MCP Server
        
        This function enriches trip planning with:
        - Historical and cultural context
        - Geographic information
        - Tourist attractions overview
        - Related topics and articles
        
        EXECUTION FLOW:
        1. SK Planner calls this when user asks about a destination
        2. Calls Wikipedia MCP Server (get_destination_info tool)
        3. MCP Server searches Wikipedia and retrieves comprehensive article summary
        4. Formats context for LLM consumption
        5. Returns formatted information
        
        INTEGRATION WITH TRIP PLANNING:
        - Called BEFORE or ALONGSIDE trip planning agents
        - Provides context that helps other agents make better recommendations
        - Can be combined with RAG agent for even richer information
        """
        logger.info(f"🔌 SK Function: get_destination_info_wikipedia called for: {destination}")
        
        # Check if Wikipedia MCP connector is available
        if "WikipediaMCP" not in self.connectors:
            logger.warning("⚠️ Wikipedia MCP Server not available, skipping Wikipedia integration")
            return f"ℹ️ Wikipedia information not available (MCP server not connected)"
        
        try:
            # Call Wikipedia MCP Server via connector
            # The MCP server exposes get_destination_info as a tool
            task = await self.connectors["WikipediaMCP"].send_task(
                f"get_destination_info: {destination}",
                session_id
            )
            result = task.history[-1].parts[0].text
            
            # Parse the JSON response from MCP server
            try:
                response_data = json.loads(result)
                
                if response_data.get('success') and response_data.get('info', {}).get('found'):
                    info = response_data['info']
                    
                    # Format context for LLM
                    context = f"""
═══════════════════════════════════════════════════════════════════════════
WIKIPEDIA DESTINATION CONTEXT
═══════════════════════════════════════════════════════════════════════════

DESTINATION: {info['title']}
DESCRIPTION: {info['summary']}

OVERVIEW:
{info['extract']}

"""
                    
                    # Add coordinates if available
                    if info.get('coordinates'):
                        context += f"COORDINATES: {info['coordinates']['lat']}° N, {info['coordinates']['lon']}° E\n\n"
                    
                    # Add related articles
                    if info.get('related_articles'):
                        context += "RELATED TOPICS:\n"
                        for article in info['related_articles']:
                            context += f"- {article}\n"
                        context += "\n"
                    
                    # Add Wikipedia URL
                    context += f"SOURCE: {info['url']}\n"
                    context += "═══════════════════════════════════════════════════════════════════════════\n"
                    
                    # Store result for formatting
                    if self.planner:
                        self.planner._agent_results['wikipedia'] = context
                        self.planner._wikipedia_raw_data = info
                    
                    logger.info(f"✅ Wikipedia info retrieved for: {destination}")
                    return context
                else:
                    error_msg = response_data.get('info', {}).get('message', 'No information found')
                    logger.warning(f"⚠️ Wikipedia: {error_msg}")
                    return f"ℹ️ {error_msg}"
                    
            except json.JSONDecodeError:
                # If not JSON, return as-is (might be formatted text)
                if self.planner:
                    self.planner._agent_results['wikipedia'] = result
                return result
            
        except Exception as e:
            logger.error(f"❌ Wikipedia MCP error: {e}")
            return f"❌ Error getting Wikipedia information: {str(e)}"
    
    @kernel_function(
        name="search_wikipedia",
        description="Search Wikipedia for articles related to travel, destinations, or topics. Use this to find relevant information when the exact destination name is unclear or to explore related topics. Returns a list of article titles and snippets."
    )
    async def search_wikipedia(
        self,
        query: Annotated[str, "Search query (e.g., 'beaches in India', 'European castles', 'Japanese temples')"],
        session_id: Annotated[str, "Session ID for the conversation"]
    ) -> str:
        """
        Search Wikipedia articles via MCP Server
        
        This function helps with:
        - Finding relevant articles when destination is unclear
        - Exploring related topics
        - Discovering alternative destinations
        - Getting multiple perspectives on a topic
        
        EXECUTION FLOW:
        1. SK Planner calls this for exploratory queries
        2. Calls Wikipedia MCP Server (search_wikipedia tool)
        3. MCP Server searches Wikipedia and returns top 5 results
        4. Returns formatted results with titles and snippets
        5. LLM can then call get_destination_info_wikipedia for details
        """
        logger.info(f"🔌 SK Function: search_wikipedia called for: {query}")
        
        # Check if Wikipedia MCP connector is available
        if "WikipediaMCP" not in self.connectors:
            logger.warning("⚠️ Wikipedia MCP Server not available, skipping Wikipedia search")
            return f"ℹ️ Wikipedia search not available (MCP server not connected)"
        
        try:
            # Call Wikipedia MCP Server via connector
            task = await self.connectors["WikipediaMCP"].send_task(
                f"search_wikipedia: {query}",
                session_id
            )
            result = task.history[-1].parts[0].text
            
            # Parse the JSON response from MCP server
            try:
                response_data = json.loads(result)
                
                if response_data.get('success'):
                    results = response_data.get('results', [])
                    
                    if not results:
                        return f"⚠️ No Wikipedia articles found for: {query}"
                    
                    # Format results
                    formatted_results = f"📚 Wikipedia Search Results for '{query}':\n\n"
                    for i, result_item in enumerate(results, 1):
                        formatted_results += f"{i}. **{result_item['title']}**\n"
                        formatted_results += f"   {result_item['snippet']}\n"
                        formatted_results += f"   (Page ID: {result_item['page_id']}, Words: {result_item['word_count']})\n\n"
                    
                    # Store result for formatting
                    if self.planner:
                        self.planner._agent_results['wikipedia_search'] = formatted_results
                    
                    logger.info(f"✅ Wikipedia search completed: {len(results)} results")
                    return formatted_results
                else:
                    error_msg = response_data.get('error', 'Search failed')
                    logger.warning(f"⚠️ Wikipedia search error: {error_msg}")
                    return f"❌ {error_msg}"
                    
            except json.JSONDecodeError:
                # If not JSON, return as-is
                if self.planner:
                    self.planner._agent_results['wikipedia_search'] = result
                return result
            
        except Exception as e:
            logger.error(f"❌ Wikipedia search error: {e}")
            return f"❌ Error searching Wikipedia: {str(e)}"
