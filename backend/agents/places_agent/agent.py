"""
Places Agent with Structured Output + Wikipedia Service Integration
Returns itinerary + Wikipedia destination info in single JSON response
"""
from backend.agents.common.azure_llm import ask_llm
from backend.mcp_tools.wikipedia_mcp_service.wikipedia_api import WikipediaMCP
from backend.models.travel_plan import (
    Itinerary, ItineraryDay, Activity, Location,
    PlacesAgentResponse, StructuredResponse, DataType,
    DisplayFormat, ExecutionMetadata, PlanStatus
)
import logging
import json
import uuid
import re

logger = logging.getLogger(__name__)


class PlacesAgent:
    """Creates travel itineraries with Wikipedia destination context"""
    
    def __init__(self):
        """Initialize PlacesAgent with Wikipedia Service"""
        self.wikipedia = WikipediaMCP()
        logger.info("✅ PlacesAgent initialized with Wikipedia Service")
    
    def run(self, query: str) -> str:
        """
        Main entry point - returns structured response with itinerary + Wikipedia info
        
        Flow:
        1. Get itinerary from LLM (simple query, no Wikipedia context)
        2. Extract destination from query
        3. Fetch Wikipedia info for destination
        4. Combine both in JSON response
        
        Args:
            query: User query about itinerary
            
        Returns:
            JSON string with structured response including:
            - Itinerary (days, activities, locations)
            - Wikipedia destination info (context, coordinates, related articles)
        """
        logger.info(f"PlacesAgent processing: {query}")
        
        try:
            # Step 1: Extract destination FIRST
            destination = self._extract_destination(query)
            logger.info(f"📍 Destination: {destination}")
            
            # Step 2: Get LLM response (simple query, NO Wikipedia context)
            logger.info("🤖 Getting itinerary from LLM...")
            display_text = self._get_llm_response(query)
            
            # Step 3: Parse itinerary data from LLM response
            logger.info("📊 Parsing itinerary data...")
            itinerary_data = self._parse_itinerary_data(display_text, query)
            
            # Step 3.5: Generate city summary and tips
            logger.info("📝 Generating city summary and tips...")
            city_summary, travel_tips = self._generate_summary_and_tips(destination, query)
            
            # Add summary and tips to itinerary
            itinerary_data.tips = travel_tips
            
            # Step 4: Fetch Wikipedia info AFTER getting itinerary
            logger.info(f"🌐 Fetching Wikipedia info for: {destination}")
            wikipedia_info = self._get_wikipedia_info(destination)
            
            # Step 5: Create structured response with both itinerary and Wikipedia
            structured_response = self._create_structured_response(
                display_text, itinerary_data, query, wikipedia_info, city_summary
            )
            print("--------------------------STRUCTURED RESPONSE---------------------------")
            print(structured_response)
            print("--------------------------STRUCTURED RESPONSE---------------------------")

            # Return as JSON string
            return structured_response.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Error in PlacesAgent: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _get_wikipedia_info(self, destination: str) -> dict:
        """
        Get Wikipedia information for destination
        
        Returns:
            Dictionary with Wikipedia data or empty dict if not found
        """
        logger.info(f"🌐 Fetching Wikipedia info for: {destination}")
        
        try:
            info = self.wikipedia.get_destination_info(destination)
            
            if info.get('found'):
                logger.info(f"✅ Wikipedia info retrieved for {destination}")
                return {
                    'found': True,
                    'title': info.get('title', ''),
                    'summary': info.get('summary', ''),
                    'extract': info.get('extract', ''),
                    'coordinates': info.get('coordinates'),
                    'url': info.get('url', ''),
                    'related_articles': info.get('related_articles', [])
                }
            else:
                logger.warning(f"⚠️ No Wikipedia info found for {destination}")
                return {'found': False}
                
        except Exception as e:
            logger.error(f"❌ Error fetching Wikipedia info: {e}")
            return {'found': False, 'error': str(e)}
    
    def _get_llm_response(self, query: str) -> str:
        """Get human-readable itinerary response from LLM (simple query, no Wikipedia context)"""
        
        system = (
            "You are a travel itinerary expert. "
            "Create detailed day-by-day itineraries with specific places to visit. "
            "\n\n"
            "CRITICAL FORMAT REQUIREMENTS:\n"
            "1. Use clear day headers: 'DAY 1', 'DAY 2', etc.\n"
            "2. Each activity MUST start with time in format: 'HH:MM AM/PM - Activity description'\n"
            "3. Example format:\n"
            "   DAY 1\n"
            "   9:00 AM - Visit Gateway of India and take photos\n"
            "   11:30 AM - Explore Colaba Causeway for shopping\n"
            "   1:00 PM - Lunch at Leopold Cafe\n"
            "\n"
            "Include timing (e.g., 9:00 AM), activities, and must-see attractions. "
            "Be specific about locations and give insider tips. "
            "ALWAYS use the format 'HH:MM AM/PM - Activity at Location'"
        )
        
        return ask_llm(system, query)
    
    def _generate_summary_and_tips(self, destination: str, query: str) -> tuple:
        """
        Generate city summary (one-liner) and travel tips
        
        Returns:
            Tuple of (summary: str, tips: list)
        """
        system = (
            "You are a travel expert. Generate a catchy one-liner summary "
            "and 4 practical travel tips for the destination."
        )
        
        prompt = f"""For {destination}, provide:
1. A catchy one-liner summary (max 80 characters) that captures the essence of the city
2. Four practical travel tips

Format your response as:
SUMMARY: [one-liner here]
TIPS:
- [tip 1]
- [tip 2]
- [tip 3]
- [tip 4]
"""
        
        response = ask_llm(system, prompt)
        
        # Parse response
        summary = "Explore the beauty and culture"
        tips = []
        
        try:
            lines = response.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('SUMMARY:'):
                    summary = line.replace('SUMMARY:', '').strip()
                elif line.strip().startswith('-') or line.strip().startswith('•'):
                    tip = line.strip().lstrip('-•').strip()
                    if tip:
                        tips.append(tip)
            
            # Fallback tips if parsing failed
            if len(tips) < 4:
                tips = [
                    f"📅 Best time to visit: October to March",
                    f"🚗 {destination} is easily accessible by train and flight",
                    f"🏨 Book accommodation in advance during peak season",
                    f"📸 Don't forget your camera for stunning photos",
                ]
        except Exception as e:
            logger.warning(f"Could not parse summary/tips: {e}")
            tips = [
                f"📅 Best time to visit: October to March",
                f"🚗 {destination} is easily accessible by train and flight",
                f"🏨 Book accommodation in advance during peak season",
                f"📸 Don't forget your camera for stunning photos",
            ]
        
        return summary, tips
    
    def _parse_itinerary_data(self, llm_response: str, query: str) -> Itinerary:
        """
        Parse structured itinerary data from LLM response
        Extracts days, times, activities, and locations
        """
        logger.info("=" * 80)
        logger.info("🔍 PARSING ITINERARY DATA")
        logger.info(f"📄 LLM Response length: {len(llm_response)} chars")
        logger.info(f"📄 First 1000 chars:\n{llm_response[:1000]}")
        logger.info("=" * 80)
        
        days = []
        current_day = None
        current_day_num = 0
        
        lines = llm_response.split('\n')
        logger.info(f"📝 Total lines to process: {len(lines)}")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect day headers (e.g., "DAY 1", "Day 2:", "## DAY 1", "### **Day 1:")
            # Updated regex to handle: ### **Day 1:, ## Day 2, DAY 3, # Day 4, etc.
            day_match = re.search(r'(?:^|\#+\s*)\*{0,2}\s*DAY\s+(\d+)[\s:*]*', line, re.IGNORECASE)
            if day_match:
                # Save previous day
                if current_day:
                    logger.info(f"✅ Completed Day {current_day.day} with {len(current_day.activities)} activities")
                    days.append(current_day)
                
                # Start new day
                current_day_num = int(day_match.group(1))
                logger.info(f"🆕 Starting Day {current_day_num} (matched line: '{line}')")
                current_day = ItineraryDay(
                    day=current_day_num,
                    activities=[]
                )
                continue
            
            # Detect activities with time - multiple patterns
            # Pattern 1: "9:00 AM - Visit Gateway"
            # Pattern 2: "9:00 AM: Visit Gateway"
            # Pattern 3: "- 9:00 AM - Visit Gateway"
            # Pattern 4: "* 9:00 AM - Visit Gateway"
            time_match = re.search(
                r'(?:^[-*•]\s*)?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))[\s:]*[-–—:]\s*(.+)',
                line
            )
            
            if time_match and current_day:
                time_str = time_match.group(1).strip()
                activity_text = time_match.group(2).strip()
                
                logger.info(f"   📍 Line {line_num}: Found activity at {time_str}: {activity_text[:50]}...")
                
                # Extract location name (usually after "at", "to", or first noun phrase)
                location_name = self._extract_location_name(activity_text)
                
                activity = Activity(
                    time=time_str,
                    title=activity_text[:100],  # Limit title length
                    location=Location(name=location_name),
                    description=activity_text
                )
                
                current_day.activities.append(activity)
            elif current_day and line and not line.startswith('#'):
                # Log lines that might be activities but didn't match
                if any(char.isdigit() for char in line[:20]):
                    logger.debug(f"   ⚠️ Line {line_num} might be activity but didn't match: {line[:80]}")
        
        # Add last day
        if current_day:
            logger.info(f"✅ Completed Day {current_day.day} with {len(current_day.activities)} activities")
            days.append(current_day)
        
        # If no days detected, create a single day with all activities
        if not days:
            logger.warning("⚠️ No days detected in response, creating default single day")
            days = [ItineraryDay(day=1, activities=[])]
        
        logger.info("=" * 80)
        logger.info(f"📊 PARSING COMPLETE: Detected {len(days)} days")
        for day in days:
            logger.info(f"   Day {day.day}: {len(day.activities)} activities")
        logger.info("=" * 80)
        
        return Itinerary(
            days=days,
            total_days=len(days)
        )
    
    def _extract_location_name(self, activity_text: str) -> str:
        """Extract location name from activity description"""
        # Look for patterns like "at Location", "to Location", "visit Location"
        patterns = [
            r'(?:at|to|visit|explore)\s+([A-Z][A-Za-z\s]+?)(?:\s*[-,.]|$)',
            r'([A-Z][A-Za-z\s]+?)\s*(?:Beach|Fort|Temple|Museum|Market|Ghat|Palace)',
            r'^([A-Z][A-Za-z\s]+)',  # First capitalized phrase
        ]
        
        for pattern in patterns:
            match = re.search(pattern, activity_text)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first 50 chars
        return activity_text[:50].strip()
    
    def _extract_destination(self, query: str) -> str:
        """Extract destination from query"""
        # Common patterns
        patterns = [
            r'(?:trip to|visit|plan|travel to)\s+([A-Z][A-Za-z\s]+?)(?:\s|$)',
            r'(?:in|at)\s+([A-Z][A-Za-z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        return "Unknown Destination"
    
    def _create_structured_response(
        self,
        display_text: str,
        itinerary_data: Itinerary,
        query: str,
        wikipedia_info: dict = None,
        city_summary: str = None
    ) -> StructuredResponse:
        """Create complete structured response with itinerary + Wikipedia info + summary"""
        
        destination = self._extract_destination(query)
        
        # Build data with itinerary, summary, and Wikipedia info
        response_data = {
            "itinerary": itinerary_data.model_dump(),
            "destination": destination,
            "summary": city_summary or f"Explore {destination}"
        }
        
        # Add Wikipedia info if available
        if wikipedia_info and wikipedia_info.get('found'):
            response_data["wikipedia"] = {
                "title": wikipedia_info.get('title', ''),
                "summary": wikipedia_info.get('summary', ''),
                "extract": wikipedia_info.get('extract', ''),
                "thumbnail": wikipedia_info.get('thumbnail'),  # For DestinationCard
                "image": wikipedia_info.get('thumbnail'),  # For hero section
                "coordinates": wikipedia_info.get('coordinates'),
                "url": wikipedia_info.get('url', ''),
                "related_articles": wikipedia_info.get('related_articles', [])
            }
            logger.info("✅ Added Wikipedia info to response")
        
        return StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.SUCCESS,
            data_type=DataType.ITINERARY,
            data=response_data,
            display=DisplayFormat(
                text=display_text,
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["PlacesAgent", "WikipediaService"] if wikipedia_info and wikipedia_info.get('found') else ["PlacesAgent"]
            )
        )
    
    def _create_error_response(self, error_msg: str) -> str:
        """Create error response"""
        response = StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.ERROR,
            data_type=DataType.ITINERARY,
            data={},
            display=DisplayFormat(
                text=f"❌ Error generating itinerary: {error_msg}",
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["PlacesAgent"]
            ),
            error=error_msg
        )
        return response.model_dump_json(indent=2)
