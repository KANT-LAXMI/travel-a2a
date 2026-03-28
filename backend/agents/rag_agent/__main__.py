import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.server.server import A2AServer
from backend.models.agent import AgentCard, AgentCapabilities, AgentSkill
from backend.agents.rag_agent.task_manager import RAGTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    server = A2AServer(
        host="localhost",
        port=10004,
        agent_card=AgentCard(
            name="RAGAgent",
            description="Question Answering agent using PDF documents and RAG (Retrieval Augmented Generation)",
            url="http://localhost:10004",
            version="1.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=False),
            skills=[AgentSkill(
                id="rag-qa",
                name="Document Q&A",
                description="Answer questions based on PDF documents using RAG with FAISS vector store and SentenceTransformers embeddings",
                tags=["rag", "qa", "pdf", "knowledge-base", "embeddings"],
                examples=[
                    "What information do you have about X?",
                    "Explain the concept of Y from the documents",
                    "What does the document say about Z?"
                ]
            )]
        ),
        task_manager=RAGTaskManager()
    )
    server.start()


if __name__ == "__main__":
    main()