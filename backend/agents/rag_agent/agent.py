"""
RAG Agent with Structured Output
Returns both human-readable display and structured JSON data
"""
import logging
import uuid
from typing import List, Dict
from backend.agents.rag_agent.pdf_processor import PDFProcessor
from backend.agents.rag_agent.vector_store import VectorStore
from backend.agents.common.azure_llm import ask_llm
from backend.models.travel_plan import (
    RAGAgentResponse, StructuredResponse, DataType,
    DisplayFormat, ExecutionMetadata, PlanStatus
)

logger = logging.getLogger(__name__)


class RAGAgent:
    """
    RAG Agent for PDF-based Question Answering with Structured Output
    """

    def __init__(self, pdf_dir: str = "backend/data/pdfs", db_path: str = "backend/data/vector_db"):
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore(db_path)
        self.pdf_dir = pdf_dir
        self.initialized = False
        
        logger.info("RAGAgent initialized")

    def initialize(self):
        """Load or create vector database from PDFs"""
        if self.initialized:
            return

        try:
            if self.vector_store.load():
                logger.info("✅ Loaded existing vector database")
                self.initialized = True
                return

            logger.info("🔄 No existing database found. Processing PDFs...")
            self._process_pdfs()
            self.initialized = True

        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Agent: {e}")
            raise

    def _process_pdfs(self):
        """Process all PDFs in the directory and create embeddings"""
        import os

        if not os.path.exists(self.pdf_dir):
            logger.warning(f"📁 PDF directory not found: {self.pdf_dir}")
            os.makedirs(self.pdf_dir, exist_ok=True)
            logger.info(f"✅ Created directory: {self.pdf_dir}")
            return

        pdf_files = [f for f in os.listdir(self.pdf_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"⚠️ No PDF files found in {self.pdf_dir}")
            return

        logger.info(f"📄 Found {len(pdf_files)} PDF files")

        all_chunks = []
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_dir, pdf_file)
            logger.info(f"Processing: {pdf_file}")
            
            try:
                chunks = self.pdf_processor.process_pdf(pdf_path)
                all_chunks.extend(chunks)
                logger.info(f"✅ Extracted {len(chunks)} chunks from {pdf_file}")
            except Exception as e:
                logger.error(f"❌ Failed to process {pdf_file}: {e}")

        if all_chunks:
            logger.info(f"📊 Creating embeddings for {len(all_chunks)} text chunks...")
            self.vector_store.add_documents(all_chunks)
            self.vector_store.save()
            logger.info("✅ Vector database created and saved")
    
    def query(self, question: str, top_k: int = 3) -> str:
        """
        Answer a question using RAG with structured output
        
        Args:
            question: User question
            top_k: Number of relevant documents to retrieve
            
        Returns:
            JSON string with structured response
        """
        logger.info(f"🔍 RAG Query: {question}")
        
        try:
            if not self.initialized:
                self.initialize()
            
            # Retrieve relevant context
            relevant_docs = self.vector_store.search(question, top_k=top_k)

            if not relevant_docs:
                logger.warning("⚠️ No relevant documents found")
                return self._create_no_data_response()

            # Build context
            context = self._build_context(relevant_docs)
            
            # Generate answer
            answer = self._generate_answer(question, context)
            
            # Guardrail check
            if self._contains_out_of_context_info(answer, context):
                logger.warning("⚠️ Answer contained out-of-context information")
                answer = (
                    "I don't have enough information in the provided documents "
                    "to answer this question completely."
                )
            
            # Extract sources
            sources = [
                f"{doc['metadata'].get('source', 'Unknown')} (Page {doc['metadata'].get('page', 'N/A')})"
                for doc in relevant_docs
            ]
            
            # Create structured response
            structured_response = self._create_structured_response(
                answer, sources, relevant_docs
            )
            
            logger.info("✅ Answer generated")
            return structured_response.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Error in RAGAgent: {e}", exc_info=True)
            return self._create_error_response(str(e))

    def _contains_out_of_context_info(self, answer: str, context: str) -> bool:
        """Check if answer introduces concepts not in context"""
        answer_terms = set(answer.lower().split())
        context_terms = set(context.lower().split())
        extra_terms = answer_terms - context_terms
        return len(extra_terms) > 40

    def _build_context(self, docs: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            text = doc['text']
            source = doc['metadata'].get('source', 'Unknown')
            page = doc['metadata'].get('page', 'Unknown')
            score = doc.get('score', 0.0)
            
            context_parts.append(
                f"[Source {i}: {source}, Page {page}, Relevance: {score:.2f}]\n{text}"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate context-grounded answer"""
        system_prompt = """
You are a document-grounded assistant.

CRITICAL RULES:
- Use ONLY the information explicitly stated in the provided context.
- Do NOT add new points, examples, or categories.
- If a point is not in the context, DO NOT include it.
- Cite sources using [Source X].
- If the answer is not available, say: "I don't have enough information in the provided documents to answer this question."
"""

        user_prompt = f"""
CONTEXT:

{context}

---

QUESTION:
{question}

ANSWER:
"""

        try:
            return ask_llm(system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return "Sorry, I encountered an error while generating the answer."
    
    def _create_structured_response(
        self,
        answer: str,
        sources: List[str],
        relevant_docs: List[Dict]
    ) -> StructuredResponse:
        """Create complete structured response"""
        
        # Calculate confidence based on relevance scores
        avg_score = sum(doc.get('score', 0.0) for doc in relevant_docs) / len(relevant_docs)
        confidence = min(avg_score / 1.0, 1.0)  # Normalize to 0-1
        
        return StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.SUCCESS,
            data_type=DataType.KNOWLEDGE_ANSWER,
            data={
                "answer": answer,
                "sources": sources,
                "confidence": round(confidence, 2),
                "num_sources": len(sources)
            },
            display=DisplayFormat(
                text=answer,
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["RAGAgent"]
            )
        )
    
    def _create_no_data_response(self) -> str:
        """Create response when no relevant documents found"""
        response = StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.PARTIAL,
            data_type=DataType.KNOWLEDGE_ANSWER,
            data={
                "answer": "I don't have enough information in my knowledge base to answer this question.",
                "sources": [],
                "confidence": 0.0
            },
            display=DisplayFormat(
                text="I don't have enough information in my knowledge base to answer this question. Please make sure relevant PDF documents are loaded.",
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["RAGAgent"]
            )
        )
        return response.model_dump_json(indent=2)
    
    def _create_error_response(self, error_msg: str) -> str:
        """Create error response"""
        response = StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.ERROR,
            data_type=DataType.KNOWLEDGE_ANSWER,
            data={},
            display=DisplayFormat(
                text=f"❌ Error processing query: {error_msg}",
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["RAGAgent"]
            ),
            error=error_msg
        )
        return response.model_dump_json(indent=2)
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector database"""
        if not self.initialized:
            self.initialize()
        
        return {
            "total_documents": self.vector_store.get_count(),
            "database_path": self.vector_store.db_path,
            "initialized": self.initialized
        }
