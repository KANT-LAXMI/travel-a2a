"""
Semantic Kernel Planner Integration

Replaces static QueryRouter with AI-powered orchestration.
The planner can reason about complex queries and decide which
agents to call, in what order, and how to combine results.
"""

import logging
import os
from typing import Dict
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments

from backend.agents.host_agent.sk_plugins import TripPlanningPlugin, KnowledgeQAPlugin
from backend.agents.host_agent.context_detector import ContextDetector

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SKPlanner:
    """
    Semantic Kernel Planner for intelligent agent orchestration
    
    This replaces the static QueryRouter with a reasoning-based system
    that can handle complex, multi-step queries automatically.
    """

    def __init__(self, connectors: Dict):
        """
        Initialize SK Planner with agent connectors
        
        Args:
            connectors: Dict of agent name -> AgentConnector instances
        """
        self.connectors = connectors
        self.kernel = None
        self.chat_service = None
        self.context_detector = ContextDetector()  # NEW: Context detection
        
        # Initialize Semantic Kernel
        self._initialize_kernel()
        
        logger.info("✅ SK Planner initialized with AI orchestration")

    def _initialize_kernel(self):
        """Initialize Semantic Kernel with Azure OpenAI and plugins"""
        
        # Get Azure OpenAI configuration
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        if not all([api_key, endpoint, deployment]):
            raise ValueError(
                "Azure OpenAI credentials not found. "
                "Check AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
                "and AZURE_OPENAI_DEPLOYMENT in .env"
            )
        
        # Create kernel
        self.kernel = Kernel()
        
        # Add Azure OpenAI chat completion service
        self.chat_service = AzureChatCompletion(
            service_id="chat",
            deployment_name=deployment,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.kernel.add_service(self.chat_service)
        
        # Add plugins
        self._register_plugins()
        
        logger.info("🧠 Semantic Kernel initialized with Azure OpenAI")

    def _register_plugins(self):
        """Register agent plugins with Semantic Kernel"""
        
        # Trip Planning Plugin (pass self for result tracking)
        self.trip_plugin = TripPlanningPlugin(self.connectors, planner=self)
        self.kernel.add_plugin(
            self.trip_plugin,
            plugin_name="TripPlanning"
        )
        logger.info("✅ Registered TripPlanning plugin")
        
        # Knowledge Q&A Plugin (pass self for result tracking and trip_plugin for modify operations)
        self.knowledge_plugin = KnowledgeQAPlugin(self.connectors, planner=self, trip_plugin=self.trip_plugin)
        self.kernel.add_plugin(
            self.knowledge_plugin,
            plugin_name="Knowledge"
        )
        logger.info("✅ Registered Knowledge plugin")

    async def orchestrate(self, user_query: str, session_id: str) -> str:
        """
        🧠 INTELLIGENT AGENT ORCHESTRATION WITH CONTEXT AWARENESS
        =========================================================
        
        Now supports conversation memory and follow-up queries!
        
        Examples:
        - "Plan Goa trip" → Creates new plan
        - "Make it cheaper" → Modifies previous plan
        - "Add water sports" → Updates existing itinerary
        
        Args:
            user_query: User's natural language query
            session_id: Session ID for conversation context
            
        Returns:
            Orchestrated response combining all agent results
        """
        logger.info("🎯 SK Planner orchestrating query")
        logger.info(f"📝 Query: {user_query}")
        logger.info(f"🆔 Session: {session_id}")
        
        # NEW: Detect if this is a follow-up query
        is_followup = self.context_detector.is_followup(user_query)
        logger.info(f"🔍 Follow-up query: {is_followup}")
        
        # NEW: Get conversation context if follow-up
        context_info = ""
        if is_followup:
            context_info = self._get_context_info(session_id)
            logger.info(f"📚 Retrieved context: {bool(context_info)}")
            logger.info(f"📚 Context length: {len(context_info)} chars")
            if context_info:
                logger.info(f"📚 Context preview: {context_info[:300]}")
            else:
                logger.warning("⚠️ Follow-up detected but NO context found!")
                logger.warning(f"⚠️ Session ID: {session_id}")
                logger.warning("⚠️ This means no previous plan exists for this session")
        
        # Track which agents were called for formatting
        self._agent_results = {
            'budget': None,
            'places': None,
            'map': None,
            'knowledge': None
        }
        
        # Create chat history
        chat_history = ChatHistory()
        
        # Build context-aware system message
        system_message = self._build_system_message(is_followup, context_info)
        
        chat_history.add_system_message(system_message)
        chat_history.add_user_message(user_query)
        
        # ═══════════════════════════════════════════════════════════════════
        # 🤖 FUNCTION CALLING CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════
        # This is where we enable AI-powered function calling:
        # 
        # FunctionChoiceBehavior.Auto means:
        # - The LLM can see all available functions (from plugins)
        # - It can decide which ones to call based on the query
        # - auto_invoke=True means it will call them automatically
        # - No manual routing logic needed - AI decides everything!
        # 
        # HOW IT WORKS UNDER THE HOOD:
        # 1. SK sends the LLM:
        #    - User query
        #    - System message (rules above)
        #    - List of available functions with descriptions
        # 2. LLM responds with: "I need to call these functions: [X, Y, Z]"
        # 3. SK automatically invokes those functions
        # 4. Results come back and LLM can use them to form final response
        # 
        # This is the MAGIC that replaces the old QueryRouter's hardcoded logic!
        # ═══════════════════════════════════════════════════════════════════
        
        # Configure function calling behavior - let SK decide automatically
        execution_settings = self.kernel.get_prompt_execution_settings_from_service_id("chat")
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
            auto_invoke=True,        # Automatically call the functions LLM selects
            filters={"excluded_plugins": []}  # Include all plugins (no exclusions)
        )
        
        # Create kernel arguments with session_id
        arguments = KernelArguments(
            settings=execution_settings,
            session_id=session_id,
            trip_query=user_query,
            question=user_query
        )
        
        try:
            # ═══════════════════════════════════════════════════════════════════
            # 🚀 INVOKE THE AI ORCHESTRATOR
            # ═══════════════════════════════════════════════════════════════════
            # This is where the magic happens!
            # 
            # EXECUTION FLOW:
            # 1. Send query + system message + available functions to LLM
            # 2. LLM analyzes and decides: "I need to call function X, Y, Z"
            # 3. SK automatically invokes those functions (auto_invoke=True)
            # 4. Each function calls its respective agent:
            #    - plan_trip_budget → BudgetAgent (port 10001)
            #    - plan_trip_itinerary → PlacesAgent (port 10002)
            #    - create_trip_map → MapAgent (port 10003)
            #    - answer_knowledge_question → RAGAgent (port 10004)
            # 5. Results are stored in _agent_results by the plugins
            # 6. LLM gets the results and can form a response
            # 7. We post-process with _format_response() for beautiful output
            # 
            # EXAMPLE TRACE:
            # Query: "Plan 5 day Goa trip"
            # → LLM decides: Call budget + itinerary + map
            # → SK invokes: plan_trip_budget(query, session_id)
            # → Plugin calls: BudgetAgent.send_task()
            # → Plugin stores: _agent_results['budget'] = result
            # → (Repeat for itinerary and map)
            # → _format_response() sees all 3 results → formats as trip plan
            # ═══════════════════════════════════════════════════════════════════
            
            logger.info("🤖 SK Planner reasoning about query...")
            
            result = await self.chat_service.get_chat_message_contents(
                chat_history=chat_history,
                settings=execution_settings,
                kernel=self.kernel,
                arguments=arguments
            )
            
            # Extract response
            if result and len(result) > 0:
                response = str(result[0].content)
                logger.info("✅ SK Planner completed orchestration")
                logger.info(f"📊 Functions called: {self._get_function_calls(result)}")
                
                # 🔥 POST-PROCESS: Format response like the old orchestrator
                formatted_response = self._format_response(response)
                return formatted_response
            else:
                logger.warning("⚠️ No response from SK Planner")
                return "Sorry, I couldn't process your request."
                
        except Exception as e:
            logger.error(f"❌ SK Planner error: {e}", exc_info=True)
            return f"Sorry, I encountered an error while orchestrating your request: {str(e)}"

    def _get_function_calls(self, result) -> str:
        """Extract which functions were called for logging"""
        try:
            if hasattr(result[0], 'metadata') and result[0].metadata:
                metadata = result[0].metadata
                if 'function_calls' in metadata:
                    return str(metadata['function_calls'])
            return "N/A"
        except:
            return "N/A"

    def get_available_functions(self) -> list:
        """Get list of available functions for debugging"""
        functions = []
        for plugin_name, plugin in self.kernel.plugins.items():
            for function_name, function in plugin.functions.items():
                functions.append({
                    "plugin": plugin_name,
                    "function": function_name,
                    "description": function.description if hasattr(function, 'description') else "N/A"
                })
        return functions

    def _format_response(self, raw_response: str) -> str:
        """
        🎨 FORMAT RESPONSE BASED ON WHICH AGENTS WERE CALLED
        =====================================================
        
        HOW FORMATTING DECISION WORKS:
        -------------------------------
        After SK Planner finishes calling agents, we need to format the output.
        This method checks which agents were called and formats accordingly.
        
        DECISION LOGIC:
        1. Check _agent_results dict to see which agents responded
        2. Detect the scenario:
           - Scenario 1: Only trip agents (budget/places/map) → Trip format
           - Scenario 2: Only knowledge agent → Q&A format
           - Scenario 3: Both trip + knowledge → Combined format
        3. Apply the appropriate formatting method
        
        WHY THIS IS NEEDED:
        - SK Planner returns raw LLM text
        - We want beautiful structured output like the old orchestrator
        - This maintains backward compatibility while keeping AI orchestration
        
        EXAMPLE FLOWS:
        
        Query: "Plan 5 day Goa trip"
        → _agent_results = {budget: "...", places: "...", map: "...", knowledge: None}
        → has_trip_data=True, has_knowledge=False
        → Returns: _format_trip_plan() with sections
        
        Query: "What are challenges?"
        → _agent_results = {budget: None, places: None, map: None, knowledge: "..."}
        → has_trip_data=False, has_knowledge=True
        → Returns: _format_qa_response() with Q&A format
        
        Query: "Plan trip and tell me challenges"
        → _agent_results = {budget: "...", places: "...", map: "...", knowledge: "..."}
        → has_trip_data=True, has_knowledge=True
        → Returns: Both formats combined!
        
        This maintains the beautiful formatting from the old orchestrator
        while keeping SK's intelligent orchestration
        """
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: DETECT WHICH AGENTS WERE CALLED
        # ═══════════════════════════════════════════════════════════════════
        # Check if any trip planning agents responded
        # (Budget, Places, or Map agents)
        has_trip_data = (
            self._agent_results['budget'] or 
            self._agent_results['places'] or 
            self._agent_results['map']
        )
        
        # Check if knowledge agent responded
        # (RAG agent for Q&A)
        has_knowledge = self._agent_results['knowledge']
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: APPLY FORMATTING BASED ON SCENARIO
        # ═══════════════════════════════════════════════════════════════════
        
        # SCENARIO 3: BOTH trip planning AND knowledge Q&A
        # This handles complex queries like "plan trip AND tell me about X"
        if has_trip_data and has_knowledge:
            logger.info("📊 Formatting: COMBINED (Trip + Knowledge)")
            
            # Format trip section
            trip_section = self._format_trip_plan(
                self._agent_results['budget'] or "⚠️ Budget information unavailable.",
                self._agent_results['places'] or "⚠️ Itinerary information unavailable.",
                self._agent_results['map'] or "⚠️ Map unavailable."
            )
            
            # Format knowledge section
            knowledge_section = self._format_qa_response(self._agent_results['knowledge'])
            
            # Combine both sections with separator
            return f"""{trip_section}

{'=' * 70}

{knowledge_section}"""
        
        # SCENARIO 1: Trip planning ONLY
        # This handles queries like "plan 5 day trip to Goa"
        elif has_trip_data:
            logger.info("📊 Formatting: TRIP PLAN ONLY")
            
            # Format as trip plan with Budget + Itinerary + Map sections
            return self._format_trip_plan(
                self._agent_results['budget'] or "⚠️ Budget information unavailable.",
                self._agent_results['places'] or "⚠️ Itinerary information unavailable.",
                self._agent_results['map'] or "⚠️ Map unavailable."
            )
        
        # SCENARIO 2: Knowledge Q&A ONLY
        # This handles queries like "what are challenges in planning?"
        elif has_knowledge:
            logger.info("📊 Formatting: KNOWLEDGE Q&A ONLY")
            
            # Format as Q&A response from RAG
            return self._format_qa_response(self._agent_results['knowledge'])
        
        # FALLBACK: No specific formatting needed
        # (Shouldn't happen if SK Planner works correctly)
        else:
            logger.warning("⚠️ No agent results found, returning raw response")
            return raw_response

    def _format_trip_plan(self, budget: str, places: str, map_data: str) -> str:
        """Format trip planning response (same as old orchestrator)"""
        
        # Extract map HTML if present
        map_html = ""
        map_summary = map_data
        
        if "[MAP_HTML_START]" in map_data and "[MAP_HTML_END]" in map_data:
            try:
                start_idx = map_data.index("[MAP_HTML_START]") + len("[MAP_HTML_START]")
                end_idx = map_data.index("[MAP_HTML_END]")
                map_html = map_data[start_idx:end_idx].strip()
                map_summary = map_data[:map_data.index("[MAP_HTML_START]")].strip()
                logger.info("📍 Map HTML extracted")
            except Exception as e:
                logger.error(f"⚠️ Failed to extract map HTML: {e}")
        
        response = f"""✈️ **COMPLETE TRAVEL PLAN**

{'=' * 70}

🧾 **BUDGET BREAKDOWN**
{'=' * 70}

{budget}

{'=' * 70}

📍 **PLACES & ITINERARY**
{'=' * 70}

{places}

{'=' * 70}

{map_summary}

{'=' * 70}

✨ **Your trip is all planned! Have a great time!**
"""
        
        # Save map if available
        if map_html:
            import os
            from datetime import datetime
            
            try:
                maps_dir = os.path.join(os.path.dirname(__file__), '../../maps')
                os.makedirs(maps_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename = f"travel_map_{timestamp}.html"
                map_filepath = os.path.join(maps_dir, map_filename)
                
                with open(map_filepath, 'w', encoding='utf-8') as f:
                    f.write(map_html)
                
                logger.info(f"💾 Map saved to: {map_filepath}")
                
                response += f"\n\n{'=' * 70}\n"
                response += f"🗺️ **INTERACTIVE MAP SAVED**\n"
                response += f"📥 Download: `{map_filepath}`\n"
                
            except Exception as e:
                logger.error(f"⚠️ Failed to save map: {e}")
        
        return response

    def _format_qa_response(self, answer: str) -> str:
        """Format Q&A response (same as old orchestrator)"""
        
        response = f"""📚 **KNOWLEDGE BASE ANSWER**

{'=' * 70}

{answer}

{'=' * 70}

💡 This answer is based on the PDF documents in the knowledge base.
"""
        return response

    
    def _get_context_info(self, session_id: str) -> str:
        """
        Get conversation context for follow-up queries
        
        Args:
            session_id: Session identifier
            
        Returns:
            Formatted context string
        """
        try:
            from database.db_manager import TravelBuddyDB
            db = TravelBuddyDB()
            
            # Get last plan
            logger.info(f"🔍 Looking for last plan with session_id: {session_id}")
            last_plan = db.get_last_plan(session_id)
            
            if not last_plan:
                logger.warning(f"⚠️ No last plan found for session: {session_id}")
                return ""
            
            logger.info(f"✅ Found last plan: {last_plan.get('id')}")
            
            # Extract key information
            destination = last_plan.get('destination', 'Unknown')
            duration = last_plan.get('duration_days', 0)
            
            budget_info = ""
            if last_plan.get('budget'):
                budget = last_plan['budget']
                budget_info = f"Budget: ₹{budget.get('total', 0)} ({budget.get('currency', 'INR')})"
            
            activities_count = 0
            if last_plan.get('itinerary_days'):
                for day in last_plan['itinerary_days']:
                    activities_count += len(day.get('activities', []))
            
            context = f"""
PREVIOUS PLAN CONTEXT:
- Destination: {destination}
- Duration: {duration} days
- {budget_info}
- Activities: {activities_count} planned
- Plan ID: {last_plan.get('id')}
"""
            logger.info(f"📋 Context built successfully: {len(context)} chars")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error getting context: {e}", exc_info=True)
            return ""
    
    def _build_system_message(self, is_followup: bool, context_info: str) -> str:
        """
        Build context-aware system message
        
        Args:
            is_followup: Whether this is a follow-up query
            context_info: Previous plan context
            
        Returns:
            System message string
        """
        base_message = """You are an intelligent travel planning orchestrator with access to specialized agents.

Your job is to understand user queries and orchestrate the right agents to fulfill them completely.

Available agents:
1. **TripPlanning.plan_trip_budget** - Creates budget breakdowns
2. **TripPlanning.plan_trip_itinerary** - Creates day-by-day itineraries
3. **TripPlanning.create_trip_map** - Creates interactive maps (MUST be called AFTER itinerary)
4. **TripPlanning.modify_existing_plan** - Modifies previous travel plans (for follow-up queries)
5. **Knowledge.answer_knowledge_question** - Answers questions from documents

CRITICAL RULES:
- For NEW trip planning queries: ALWAYS call ALL THREE agents in this EXACT ORDER:
  1. FIRST: Call plan_trip_budget and plan_trip_itinerary (can be parallel)
  2. SECOND: WAIT for itinerary to complete, THEN call create_trip_map
  3. The map agent REQUIRES the itinerary to be generated first
- For FOLLOW-UP queries (like "make it cheaper", "add activities"): Call modify_existing_plan
- For knowledge questions ONLY: Call the knowledge agent
- For queries with BOTH trip planning AND questions: Call BOTH sets of agents

⚠️ SEQUENTIAL EXECUTION REQUIREMENT:
The create_trip_map function MUST be called AFTER plan_trip_itinerary completes.
The map agent needs the itinerary text to extract locations.
DO NOT call all three functions simultaneously.

EXAMPLES:
- "Plan 5 day Goa trip" → Call: budget + itinerary (parallel), THEN map (after itinerary)
- "Make it cheaper" → Call: modify_existing_plan
- "Add water sports" → Call: modify_existing_plan
- "What are challenges?" → Call: knowledge
- "Plan trip and explain challenges" → Call: budget + itinerary + map (sequential) + knowledge
"""
        
        if is_followup and context_info:
            base_message += f"""

{context_info}

🚨 CRITICAL: This is a FOLLOW-UP query to modify the existing plan above.
You MUST call the TripPlanning.modify_existing_plan function.

REQUIRED FUNCTION CALL:
- Function: TripPlanning.modify_existing_plan
- Parameter modification_request: The user's modification request from the query
- Parameter session_id: Use the session_id from arguments

DO NOT respond with text.
DO NOT create a new plan.
DO NOT call budget/itinerary/map functions directly.
ONLY call modify_existing_plan function.
"""
        
        return base_message
