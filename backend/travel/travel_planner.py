"""
Travel Planner API Integration
================================
Integrates with A2A travel planning system
"""

import sys
import os
import asyncio
import logging
import re
from uuid import uuid4
from typing import Dict, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# Add parent directory to path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.client.client import A2AClient
from backend.models.task import Task as A2ATask
from backend.config import Config


class TravelPlannerService:
    """Service to interact with A2A travel planning system"""
    
    def __init__(self):
        self.agent_url = Config.HOST_AGENT_URL
        self.timeout = Config.A2A_TIMEOUT
        self.session_file = '.session_id'
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        if session_id:
            return session_id
            
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                return f.read().strip()
        
        new_session = uuid4().hex
        with open(self.session_file, 'w') as f:
            f.write(new_session)
        return new_session
    
    async def plan_trip(self, user_query: str, session_id: Optional[str] = None) -> Dict:
        """
        Plan a trip based on user query
        
        Args:
            user_query: User's trip planning request
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dictionary with trip plan, itinerary, budget, and map
        """
        try:
            session_id = self.get_or_create_session(session_id)
            client = A2AClient(url=self.agent_url, timeout=self.timeout)
            
            payload = {
                'id': uuid4().hex,
                'sessionId': session_id,
                'message': {
                    'role': 'user',
                    'parts': [{'type': 'text', 'text': user_query}]
                }
            }
            
            logger.info(f"Sending request: {user_query[:100]}...")
            task = await client.send_task(payload)
            
            if not task or not task.history or len(task.history) < 2:
                return {
                    'success': False,
                    'message': 'No response from travel planner'
                }
            
            response_text = task.history[-1].parts[0].text
            parsed_data = self._parse_response(response_text)
            
            # Extract Wikipedia data if available
            wikipedia_data = None
            if hasattr(task, 'metadata') and task.metadata:
                wikipedia_data = task.metadata.get('wikipedia_data')
            
            return {
                'success': True,
                'session_id': session_id,
                'raw_response': response_text,
                'wikipedia': wikipedia_data,  # Add Wikipedia data
                **parsed_data
            }
            
        except Exception as e:
            logger.error(f"Error planning trip: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse the response text to extract structured data including Wikipedia"""
        result = {
            'budget': self._extract_budget(response_text),
            'itinerary': self._extract_itinerary(response_text),
            'map_file': self._extract_map_file(response_text),
            'wikipedia': self._extract_wikipedia(response_text),  # Extract Wikipedia data
            'summary': response_text
        }
        return result
    
    def _extract_wikipedia(self, text: str) -> Optional[Dict]:
        """Extract Wikipedia data from PlacesAgent JSON response"""
        try:
            # Find JSON objects in the response
            import json
            import re
            
            # Look for JSON objects containing wikipedia data
            json_pattern = r'\{[^{}]*"wikipedia"[^{}]*\{[^}]*\}[^}]*\}'
            matches = re.finditer(json_pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    json_str = match.group(0)
                    # Try to parse as JSON
                    data = json.loads(json_str)
                    if 'wikipedia' in data:
                        logger.info(f"✅ Extracted Wikipedia data: {data['wikipedia'].get('title', 'Unknown')}")
                        return data['wikipedia']
                except json.JSONDecodeError:
                    continue
            
            # Alternative: Look for complete StructuredResponse JSON
            start_idx = 0
            while start_idx < len(text):
                open_brace = text.find('{', start_idx)
                if open_brace == -1:
                    break
                
                # Find matching closing brace
                brace_count = 0
                end_idx = open_brace
                for i in range(open_brace, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if brace_count == 0:
                    json_str = text[open_brace:end_idx]
                    try:
                        obj = json.loads(json_str)
                        # Check if this is a StructuredResponse with wikipedia data
                        if 'data' in obj and isinstance(obj['data'], dict):
                            if 'wikipedia' in obj['data']:
                                logger.info(f"✅ Extracted Wikipedia from StructuredResponse")
                                return obj['data']['wikipedia']
                    except json.JSONDecodeError:
                        pass
                
                start_idx = end_idx + 1
            
            logger.info("ℹ️ No Wikipedia data found in response")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting Wikipedia data: {e}")
            return None
    
    def _extract_budget(self, text: str) -> Optional[str]:
        """Extract budget information from response"""
        if '₹' not in text and 'budget' not in text.lower():
            return None
            
        lines = text.split('\n')
        budget_section = []
        in_budget = False
        
        for line in lines:
            if 'budget' in line.lower() or '₹' in line:
                in_budget = True
            if in_budget:
                budget_section.append(line)
                if line.strip() == '' and len(budget_section) > 3:
                    break
        
        return '\n'.join(budget_section) if budget_section else None
    
    def _extract_itinerary(self, text: str) -> List[Dict]:
        """Extract day-by-day itinerary from response"""
        lines = text.split('\n')
        itinerary = []
        current_day = None
        day_activities = []
        
        for line in lines:
            if line.strip().startswith(('Day ', '**Day ')):
                if current_day and day_activities:
                    itinerary.append({
                        'day': current_day,
                        'activities': day_activities
                    })
                current_day = line.strip().replace('**', '').replace(':', '')
                day_activities = []
            elif current_day and line.strip():
                day_activities.append(line.strip())
        
        if current_day and day_activities:
            itinerary.append({
                'day': current_day,
                'activities': day_activities
            })
        
        return itinerary
    
    def _extract_map_file(self, text: str) -> Optional[str]:
        """Extract map filename from response"""
        if 'travel_map' not in text:
            return None
        match = re.search(r'travel_map_\d+_\d+\.html', text)
        return match.group(0) if match else None


# Global service instance
_travel_planner_service = None

def get_travel_planner_service() -> TravelPlannerService:
    """Get or create singleton travel planner service"""
    global _travel_planner_service
    if _travel_planner_service is None:
        _travel_planner_service = TravelPlannerService()
    return _travel_planner_service


def plan_trip_sync(user_query: str, session_id: Optional[str] = None) -> Dict:
    """Synchronous wrapper for plan_trip"""
    service = get_travel_planner_service()
    return asyncio.run(service.plan_trip(user_query, session_id))
