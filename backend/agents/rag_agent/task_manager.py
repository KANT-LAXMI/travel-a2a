from backend.server.task_manager import InMemoryTaskManager
from backend.models.request import SendTaskRequest, SendTaskResponse
from backend.models.task import Message, TaskStatus, TaskState, TextPart
from backend.agents.rag_agent.agent import RAGAgent
import logging

logger = logging.getLogger(__name__)


class RAGTaskManager(InMemoryTaskManager):
    def __init__(self):
        super().__init__()
        self.agent = RAGAgent()
        
        # Initialize vector store on startup
        logger.info("🚀 Initializing RAG Agent...")
        try:
            self.agent.initialize()
            stats = self.agent.get_stats()
            logger.info(f"📊 Vector DB Stats: {stats}")
        except Exception as e:
            logger.error(f"⚠️ RAG Agent initialization warning: {e}")

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        logger.info(f"RAGTaskManager received task: {request.params.id}")
        
        logger.info("2️⃣ REQUEST ENTERS RAG AGENT")
        # Upsert task
        task = await self.upsert_task(request.params)
        # Get user query
        logger.info("(1) Exact line where query is extracted")
        query = request.params.message.parts[0].text
        logger.info("------------------------------------Q U E R Y---------------------------------------------")
        logger.info(query)
        logger.info("------------------------------------Q U E R Y---------------------------------------------")


        # Process with RAG agent
        try:
            logger.info("(2) Line where RAG logic is triggered")
            result = self.agent.query(query, top_k=3)
        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            result = f"Sorry, I encountered an error while processing your question: {str(e)}"
        
        # Create reply message
        reply = Message(role="agent", parts=[TextPart(text=result)])
        
        # Update task
        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(reply)
        
        logger.info(f"RAGTaskManager completed task: {request.params.id}")
        return SendTaskResponse(id=request.id, result=task)