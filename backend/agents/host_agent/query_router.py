import logging
from backend.agents.common.azure_llm import ask_llm

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes user queries to appropriate agents:
    - Trip planning → BudgetAgent + PlacesAgent + MapAgent
    - Knowledge/Q&A → RAGAgent
    """

    def classify_query(self, query: str) -> str:
        """
        Classify user query into 'trip_planning' or 'knowledge_qa'
        
        Args:
            query: User's input query
            
        Returns:
            'trip_planning' or 'knowledge_qa'
        """
        logger.info(f"🔍 Classifying query: {query[:100]}...")

        # Use LLM to classify
        classification = self._llm_classify(query)
        
        logger.info(f"✅ Classification: {classification}")
        return classification

    def _llm_classify(self, query: str) -> str:
        """Use Azure OpenAI to classify the query"""
        
        system_prompt = """You are a query classification system. Your job is to determine if a user query is about:

1. TRIP PLANNING: Queries about planning trips, travel itineraries, budgets, destinations, places to visit, travel recommendations
   Examples:
   - "Plan a trip to Goa"
   - "3-day Kerala tour under 15k"
   - "Where should I go in Mumbai?"
   - "Create an itinerary for Varanasi"
   - "Budget for Rajasthan trip"
   
2. KNOWLEDGE Q&A: Questions seeking information, explanations, or facts from documents
   Examples:
   - "What is X?"
   - "Explain the concept of Y"
   - "What information do you have about Z?"
   - "What does the document say about...?"
   - "Tell me about..."

Respond with ONLY ONE WORD:
- "trip_planning" for travel planning queries
- "knowledge_qa" for information/question queries

CRITICAL: Respond with ONLY the classification word, nothing else."""

        user_prompt = f"Classify this query:\n\n{query}"

        try:
            response = ask_llm(system_prompt, user_prompt).strip().lower()
            
            # Ensure valid response
            if 'trip' in response or 'travel' in response or 'planning' in response:
                return 'trip_planning'
            elif 'knowledge' in response or 'qa' in response or 'question' in response:
                return 'knowledge_qa'
            else:
                # Fallback: use keyword matching
                return self._keyword_classify(query)
                
        except Exception as e:
            logger.error(f"❌ LLM classification failed: {e}")
            # Fallback to keyword-based classification
            return self._keyword_classify(query)

    def _keyword_classify(self, query: str) -> str:
        """Fallback: Simple keyword-based classification"""
        query_lower = query.lower()

        # Trip planning keywords
        trip_keywords = [
            'trip', 'travel', 'visit', 'tour', 'itinerary', 'plan',
            'budget', 'destination', 'places', 'hotel', 'flight',
            'vacation', 'holiday', 'weekend', 'day', 'stay',
            'explore', 'sightseeing', 'accommodation', 'booking'
        ]

        # Q&A keywords
        qa_keywords = [
            'what', 'how', 'why', 'when', 'where', 'who',
            'explain', 'define', 'tell me', 'information',
            'describe', 'meaning', 'concept', 'details',
            'document', 'says', 'about', 'regarding'
        ]

        # Count matches
        trip_score = sum(1 for kw in trip_keywords if kw in query_lower)
        qa_score = sum(1 for kw in qa_keywords if kw in query_lower)

        # Special case: questions about travel are still trip planning
        if any(word in query_lower for word in ['where should i', 'where to', 'which place']):
            return 'trip_planning'

        # Decide based on scores
        if trip_score > qa_score:
            logger.info(f"📊 Keyword classification: trip_planning (score: {trip_score} vs {qa_score})")
            return 'trip_planning'
        else:
            logger.info(f"📊 Keyword classification: knowledge_qa (score: {qa_score} vs {trip_score})")
            return 'knowledge_qa'