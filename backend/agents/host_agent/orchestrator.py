"""
🧠 INTELLIGENT ORCHESTRATOR WITH SEMANTIC KERNEL AND DATABASE INTEGRATION
=========================================================================

BEFORE (Static Routing):
- User query → QueryRouter → IF trip THEN agents ELSE rag
- Binary classification
- Hardcoded logic
- Can't handle complex queries

AFTER (AI Orchestration):
- User query → SK Planner → Reasoning → Auto-select agents
- Multi-step execution
- Dynamic orchestration
- Handles complex queries like "plan trip AND tell me challenges"

🔥 THIS IS THE MAGIC - SK DECIDES EVERYTHING AUTOMATICALLY
"""

import logging
import json
import time
from typing import Optional
from backend.agents.host_agent.agent_connect import AgentConnector
from backend.agents.host_agent.sk_planner import SKPlanner
from backend.server.task_manager import InMemoryTaskManager
from backend.models.request import SendTaskRequest, SendTaskResponse
from backend.models.task import Message, TaskStatus, TaskState, TextPart
from backend.models.travel_plan import StructuredResponse, DataType, ExecutionMetadata, DisplayFormat, PlanStatus
from backend.database.db_manager import TravelBuddyDB
from backend.mcp_tools.filesystem_mcp_service.filesystem_api import FilesystemAPI

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    🧠 AI-Powered Orchestrator using Semantic Kernel with Database Integration
    
    Replaces static routing with intelligent reasoning:
    - Automatically decides which agents to call
    - Can call multiple agents in sequence
    - Handles complex multi-intent queries
    - Combines results intelligently
    - Saves results to database with conversation history
    """

    def __init__(self, agent_cards, db_path: str = "backend/database/travel_buddy.db"):
        """
        Initialize orchestrator with agent registry, SK Planner, Database, and Filesystem
        
        Args:
            agent_cards: List of discovered agent cards
            db_path: Path to SQLite database
        """
        self.connectors = {}
        
        # Register all available agents
        for card in agent_cards:
            self.connectors[card.name] = AgentConnector(card.name, card.url)
            logger.info(f"✅ Registered agent: {card.name}")
        
        # Verify required agents are present
        required_agents = ["BudgetAgent", "PlacesAgent", "MapAgent", "RAGAgent"]
        missing = [a for a in required_agents if a not in self.connectors]
        
        if missing:
            logger.warning(f"⚠️ Missing agents: {missing}")
            logger.warning("Some functionality may be limited")
        
        # 🔥 INITIALIZE SEMANTIC KERNEL PLANNER
        logger.info("🧠 Initializing SK Planner for AI orchestration...")
        try:
            self.sk_planner = SKPlanner(self.connectors)
            logger.info("✅ SK Planner ready - AI orchestration enabled!")
            
            # Log available functions
            functions = self.sk_planner.get_available_functions()
            logger.info(f"📋 Available SK Functions: {len(functions)}")
            for func in functions:
                logger.info(f"   - {func['plugin']}.{func['function']}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize SK Planner: {e}")
            raise
        
        # Initialize Database
        logger.info("💾 Initializing database...")
        try:
            self.db = TravelBuddyDB(db_path)
            logger.info("✅ Database ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.db = None
        
        # Initialize Filesystem API for PDF generation
        logger.info("📁 Initializing Filesystem API...")
        try:
            self.filesystem = FilesystemAPI()
            logger.info("✅ Filesystem API ready - PDF generation enabled")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Filesystem API: {e}")
            self.filesystem = None

    async def invoke(self, query: str, session_id: str) -> str:
        """
        🎯 MAIN ORCHESTRATION ENTRY POINT WITH DATABASE INTEGRATION
        
        The SK Planner will:
        1. Analyze the user query
        2. Decide which agents to call
        3. Execute them automatically
        4. Combine results
        5. Save to database with conversation history
        
        Examples:
        - "Plan a 2-day Goa trip" → Calls Budget + Places + Map
        - "What challenges exist in travel planning?" → Calls RAG
        - "Plan Varanasi trip and tell me about challenges" → Calls ALL agents
        
        Args:
            query: User's natural language query
            session_id: Session ID for the conversation
            
        Returns:
            Orchestrated response from SK Planner
        """
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info("🎬 ORCHESTRATOR INVOKED")
        logger.info("=" * 80)
        logger.info(f"📝 User Query: {query}")
        logger.info(f"🆔 Session: {session_id}")
        logger.info("=" * 80)
        
        # Save user message to conversation history
        if self.db:
            try:
                self.db.save_conversation_message(session_id, 'user', query)
                logger.info("💬 Saved user message to conversation history")
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")
        else:
            logger.warning("⚠️ Database not initialized - skipping conversation save")
        
        try:
            # 🔥 LET SK PLANNER DO THE MAGIC
            logger.info("🧠 Delegating to SK Planner for AI orchestration...")
            
            response_text = await self.sk_planner.orchestrate(query, session_id)
            
            logger.info("=" * 80)
            logger.info("✅ ORCHESTRATION COMPLETE")
            logger.info("=" * 80)
            
            # Extract Wikipedia data if available for frontend
            wikipedia_data = None
            if self.sk_planner._agent_results.get('wikipedia'):
                try:
                    # Parse Wikipedia context to extract structured data
                    wiki_context = self.sk_planner._agent_results['wikipedia']
                    # The context is formatted text, we need to get the original data
                    # Check if we have the raw Wikipedia data stored
                    if hasattr(self.sk_planner, '_wikipedia_raw_data'):
                        wikipedia_data = self.sk_planner._wikipedia_raw_data
                        logger.info(f"📚 Wikipedia data available for frontend: {wikipedia_data.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not extract Wikipedia data for frontend: {e}")
            
            # Save to database if enabled
            plan_id = None
            if self.db:
                try:
                    logger.info("💾 Starting database save process...")
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    plan_id = self._save_to_database(query, session_id, execution_time_ms)
                    
                    if plan_id:
                        logger.info(f"✅ Travel plan saved with ID: {plan_id}")
                    else:
                        logger.info("ℹ️ No travel plan to save (might be knowledge query or error)")
                    
                    # Save agent response to conversation history
                    self.db.save_conversation_message(
                        session_id, 'agent', response_text, plan_id
                    )
                    logger.info("💬 Saved agent response to conversation history")
                except Exception as e:
                    logger.error(f"❌ Failed to save to database: {e}", exc_info=True)
                    import traceback
                    logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
            else:
                logger.warning("⚠️ Database not initialized - skipping save")
            
            logger.info("=" * 80)
            logger.info(f"🔵 ORCHESTRATOR COMPLETE - Plan ID: {plan_id}")
            logger.info("=" * 80)
            
            return response_text
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ ORCHESTRATION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {e}", exc_info=True)
            
            return self._create_error_response(e)

    def _save_to_database(self, query: str, session_id: str, execution_time_ms: int) -> Optional[str]:
        """
        Extract structured data from agent responses and save to DB
        
        Returns:
            plan_id if travel plan was saved, None otherwise
        """
        logger.info("📊 === DATABASE SAVE DEBUG ===")
        logger.info(f"📊 Session ID: {session_id}")
        logger.info(f"📊 Query: {query}")
        logger.info(f"📊 Execution time: {execution_time_ms}ms")
        
        agent_results = self.sk_planner._agent_results
        
        logger.info(f"📊 Agent results keys: {list(agent_results.keys())}")
        logger.info(f"📊 Budget present: {bool(agent_results.get('budget'))}")
        logger.info(f"📊 Places present: {bool(agent_results.get('places'))}")
        logger.info(f"📊 Map present: {bool(agent_results.get('map'))}")
        logger.info(f"📊 Knowledge present: {bool(agent_results.get('knowledge'))}")
        
        # Parse structured responses
        budget_data = None
        itinerary_data = None
        map_data = None
        knowledge_data = None
        destination = "Unknown"
        agents_called = []
        
        # Parse budget
        if agent_results.get('budget'):
            try:
                budget_response = StructuredResponse.model_validate_json(agent_results['budget'])
                budget_obj = budget_response.data.get('budget')
                # Convert Pydantic model to dict
                if budget_obj:
                    if hasattr(budget_obj, 'model_dump'):
                        budget_data = budget_obj.model_dump()
                    elif hasattr(budget_obj, 'dict'):
                        budget_data = budget_obj.dict()
                    else:
                        budget_data = budget_obj
                else:
                    budget_data = None
                agents_called.append('BudgetAgent')
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse budget: {e}")
        
        # Parse places
        wikipedia_data = None  # Initialize Wikipedia data
        if agent_results.get('places'):
            try:
                logger.info(f"📝 Raw places response length: {len(agent_results['places'])} chars")
                places_response = StructuredResponse.model_validate_json(agent_results['places'])
                
                # Extract Wikipedia data from places response
                if places_response.data.get('wikipedia'):
                    wikipedia_data = places_response.data['wikipedia']
                    logger.info(f"📚 Wikipedia data extracted: {wikipedia_data.get('title', 'Unknown')}")
                
                # Convert Pydantic models to dicts
                itinerary_obj = places_response.data.get('itinerary')
                if itinerary_obj:
                    # If it's a Pydantic model, convert to dict
                    if hasattr(itinerary_obj, 'model_dump'):
                        itinerary_data = itinerary_obj.model_dump()
                    elif hasattr(itinerary_obj, 'dict'):
                        itinerary_data = itinerary_obj.dict()
                    else:
                        itinerary_data = itinerary_obj
                else:
                    itinerary_data = None
                    
                destination = places_response.data.get('destination', 'Unknown')
                agents_called.append('PlacesAgent')
                
                # Debug: Log itinerary data
                if itinerary_data:
                    days_list = itinerary_data.get('days', [])
                    days_count = len(days_list)
                    logger.info(f"📅 Parsed itinerary: {days_count} days for {destination}")
                    logger.info(f"📅 Days structure type: {type(days_list)}")
                    if days_list:
                        logger.info(f"📅 First day keys: {days_list[0].keys() if isinstance(days_list[0], dict) else 'not a dict'}")
                else:
                    logger.warning("⚠️ No itinerary data in places response")
            except Exception as e:
                logger.error(f"❌ Failed to parse places: {e}", exc_info=True)
        
        # Parse map
        map_html = None
        if agent_results.get('map'):
            try:
                map_response = StructuredResponse.model_validate_json(agent_results['map'])
                map_obj = map_response.data.get('map')
                # Convert Pydantic model to dict
                if map_obj:
                    if hasattr(map_obj, 'model_dump'):
                        map_data = map_obj.model_dump()
                    elif hasattr(map_obj, 'dict'):
                        map_data = map_obj.dict()
                    else:
                        map_data = map_obj
                else:
                    map_data = None
                map_html = map_response.data.get('html')  # Extract HTML content
                agents_called.append('MapAgent')
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse map: {e}")
        
        # Parse knowledge
        if agent_results.get('knowledge'):
            try:
                knowledge_response = StructuredResponse.model_validate_json(agent_results['knowledge'])
                knowledge_data = knowledge_response.data
                agents_called.append('RAGAgent')
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse knowledge: {e}")
        
        # Save travel plan if we have trip data
        has_trip_data = any([budget_data, itinerary_data, map_data])
        
        logger.info(f"📊 Has trip data: {has_trip_data}")
        logger.info(f"📊 Budget data: {bool(budget_data)}")
        logger.info(f"📊 Itinerary data: {bool(itinerary_data)}")
        logger.info(f"📊 Map data: {bool(map_data)}")
        
        if has_trip_data:
            import uuid
            
            duration_days = len(itinerary_data.get('days', [])) if itinerary_data else 0
            
            logger.info(f"📊 Creating travel plan response:")
            logger.info(f"📊   - Destination: {destination}")
            logger.info(f"📊   - Duration: {duration_days} days")
            logger.info(f"📊   - Agents called: {agents_called}")
            
            response = StructuredResponse(
                request_id=str(uuid.uuid4()),
                status=PlanStatus.SUCCESS,
                data_type=DataType.TRAVEL_PLAN,
                data={
                    'destination': destination,
                    'duration_days': duration_days,
                    'budget': budget_data,
                    'itinerary': itinerary_data,
                    'map': map_data,
                    'html': map_html,  # Include HTML content
                    'wikipedia': wikipedia_data  # Add Wikipedia data
                },
                display=DisplayFormat(text="", format="markdown"),
                metadata=ExecutionMetadata(
                    agents_called=agents_called,
                    execution_time_ms=execution_time_ms
                )
            )
            
            logger.info("📊 Calling db.save_travel_plan()...")
            try:
                plan_id = self.db.save_travel_plan(response, query, session_id)
                logger.info(f"✅ Successfully saved travel plan to database: {plan_id}")
                logger.info(f"✅ Plan details: {destination}, {duration_days} days, session: {session_id[:16]}...")
                
                # 💾 SAVE PLAN AS PDF (ASYNC - in background thread)
                if self.filesystem:
                    logger.info("📄 Starting PDF generation in background...")
                    
                    # Generate PDF in background thread to avoid blocking
                    import threading
                    
                    def generate_pdf_async():
                        try:
                            logger.info("📄 [ASYNC] Generating PDF with all images...")
                            pdf_result = self.filesystem.save_plan_as_pdf(
                                destination=destination,
                                duration_days=duration_days,
                                plan_data={
                                    'budget': budget_data,
                                    'itinerary': itinerary_data,
                                    'map': map_data,
                                    'wikipedia': itinerary_data.get('wikipedia') if itinerary_data else None
                                },
                                session_id=session_id
                            )
                            
                            if pdf_result.get('success'):
                                logger.info(f"✅ [ASYNC] PDF saved: {pdf_result['filename']} ({pdf_result['size_kb']} KB)")
                                logger.info(f"📂 [ASYNC] Location: {pdf_result['filepath']}")
                            else:
                                logger.error(f"❌ [ASYNC] PDF generation failed: {pdf_result.get('error')}")
                        except Exception as pdf_error:
                            logger.error(f"❌ [ASYNC] Error generating PDF: {pdf_error}", exc_info=True)
                    
                    # Start PDF generation in background
                    pdf_thread = threading.Thread(target=generate_pdf_async, daemon=True)
                    pdf_thread.start()
                    logger.info("✅ PDF generation started in background (non-blocking)")
                else:
                    logger.warning("⚠️ Filesystem API not available - PDF not generated")
                
                return plan_id  # Return plan_id for conversation history
            except Exception as e:
                logger.error(f"❌ Error in db.save_travel_plan(): {e}", exc_info=True)
                raise
        
        # Save knowledge query if present
        if knowledge_data:
            import uuid
            
            logger.info("📊 Saving knowledge query to database...")
            
            response = StructuredResponse(
                request_id=str(uuid.uuid4()),
                status=PlanStatus.SUCCESS,
                data_type=DataType.KNOWLEDGE_ANSWER,
                data=knowledge_data,
                display=DisplayFormat(
                    text=knowledge_data.get('answer', ''),
                    format="markdown"
                ),
                metadata=ExecutionMetadata(
                    agents_called=['RAGAgent'],
                    execution_time_ms=execution_time_ms
                )
            )
            
            query_id = self.db.save_knowledge_query(response, query, session_id)
            logger.info(f"✅ Saved knowledge query to database: {query_id}")
        
        logger.info("📊 === END DATABASE SAVE DEBUG ===")
        return None  # No plan_id for knowledge queries

    def _create_error_response(self, error: Exception) -> str:
        """Create user-friendly error response"""
        return f"""❌ **Orchestration Error**

{'=' * 70}

Sorry, I encountered an error while processing your request.

**Error Details:**
{str(error)}

{'=' * 70}

**Troubleshooting:**
1. Check that all required agents are running:
   - BudgetAgent (port 10001)
   - PlacesAgent (port 10002)
   - MapAgent (port 10003)
   - RAGAgent (port 10004)

2. Verify Azure OpenAI credentials in .env file

3. Check agent logs for more details

{'=' * 70}
"""


class OrchestratorTaskManager(InMemoryTaskManager):
    """
    A2A TaskManager for Host Agent with SK Planner and Database Integration
    """

    def __init__(self, agent: OrchestratorAgent):
        super().__init__()
        self.agent = agent

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Handle incoming A2A task requests
        
        Delegates to OrchestratorAgent which uses SK Planner
        """
        logger.info(f"🎬 Host received task {request.params.id}")

        # Upsert task
        task = await self.upsert_task(request.params)
        
        # Get user query
        user_text = request.params.message.parts[0].text

        # Set status to working
        async with self.lock:
            task.status = TaskStatus(state=TaskState.WORKING)

        # 🔥 PROCESS THROUGH SK PLANNER ORCHESTRATION
        response_text = await self.agent.invoke(
            user_text,
            request.params.sessionId
        )

        # Create reply
        reply = Message(
            role="agent",
            parts=[TextPart(text=response_text)]
        )

        # Update task as completed
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(reply)

        logger.info(f"✅ Host completed task {request.params.id}")
        return SendTaskResponse(id=request.id, result=task)


# 📝 USAGE COMPARISON
# ===================
# 
# BEFORE (Query Router):
# ----------------------
# User: "Plan trip to Goa"
# → QueryRouter classifies as "trip_planning"
# → Hardcoded: call Budget + Places + Map in parallel
# → Response: Budget + Itinerary + Map
# 
# User: "What are challenges in planning?"
# → QueryRouter classifies as "knowledge_qa"
# → Hardcoded: call RAG only
# → Response: RAG answer
# 
# User: "Plan Goa trip AND tell me challenges"
# → QueryRouter BREAKS (can only pick one)
# → Either trip OR knowledge, not both
# 
# 
# AFTER (SK Planner):
# -------------------
# User: "Plan trip to Goa"
# → SK Planner reasons: "Need budget, itinerary, map"
# → Automatically calls: plan_trip_budget + plan_trip_itinerary + create_trip_map
# → Response: Complete trip plan
# 
# User: "What are challenges in planning?"
# → SK Planner reasons: "This is a knowledge question"
# → Automatically calls: answer_knowledge_question
# → Response: RAG answer from documents
# 
# User: "Plan Goa trip AND tell me challenges"
# → SK Planner reasons: "Need BOTH trip planning AND knowledge"
# → Step 1: Calls plan_trip_budget + plan_trip_itinerary + create_trip_map
# → Step 2: Calls answer_knowledge_question about challenges
# → Response: Complete trip plan + challenges from documents
# 
# 🔥 THIS IS THE POWER OF AI ORCHESTRATION!
