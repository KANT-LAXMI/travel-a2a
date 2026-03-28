"""
Map Agent with Structured Output
Returns both human-readable display and structured JSON data
"""
import re
import json
import logging
import time
import requests
import uuid
from typing import Optional
from backend.agents.common.azure_llm import ask_llm
from backend.models.travel_plan import (
    MapData, MapLocation, MapAgentResponse,
    StructuredResponse, DataType, DisplayFormat,
    ExecutionMetadata, PlanStatus
)
from dotenv import load_dotenv
# ✅ LOAD .env FIRST
load_dotenv()

logger = logging.getLogger(__name__)


class MapAgent:
    """Extracts places from itinerary and creates interactive maps with structured output"""
    
    def run(self, itinerary_text: str) -> str:
        """
        Main entry point - returns structured response
        
        Args:
            itinerary_text: Itinerary text to extract places from
            
        Returns:
            JSON string with structured response
        """
        logger.info("MapAgent processing itinerary for map creation")
        self.itinerary_text = itinerary_text

        try:
            # Step 1: Extract places
            places_data = self._extract_places_with_llm(itinerary_text)

            # Step 2: Geocode missing lat/lng
            if places_data:
                places_data = self._geocode_places(places_data)

            # Step 3: Create structured response (NO HTML GENERATION)
            display_text = self._create_display_text(places_data, None)
            map_data = self._create_map_data(places_data, None)
            
            structured_response = self._create_structured_response(
                display_text, map_data, None
            )

            return structured_response.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Error in MapAgent: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _extract_places_with_llm(self, itinerary_text: str) -> list:
        """Use LLM to extract places with timing and approximate coordinates"""
        system = """You are a travel data extraction expert specializing in Indian destinations.

Extract all places mentioned in the travel itinerary with the following details:
1. name: Place/location name (be specific)
2. time: Timing mentioned (e.g., "9:00 AM")
3. day: Which day (e.g., "Day 1", "Day 2")
4. description: Brief activity description
5. duration: Duration in minutes (estimate if not mentioned)
6. lat: Approximate latitude (estimate based on city/location knowledge)
7. lng: Approximate longitude (estimate based on city/location knowledge)

For common Indian tourist destinations, use your knowledge to provide realistic coordinates.

Return ONLY a valid JSON array. Example:
[
  {
    "name": "Gateway of India",
    "time": "9:30 AM",
    "day": "Day 1",
    "description": "Exploring the monument",
    "duration": 60,
    "lat": 18.921,
    "lng": 72.834
  }
]

CRITICAL: Return ONLY the JSON array, no markdown, no explanations, no extra text."""

        user = f"Extract all places with coordinates from this itinerary:\n\n{itinerary_text}"
        
        try:
            response = ask_llm(system, user)
            response = response.strip()
            
            # Clean markdown code blocks if present
            response = re.sub(r'^```json\s*', '', response)
            response = re.sub(r'^```\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
            
            places = json.loads(response)
            logger.info(f"✅ Extracted {len(places)} places with coordinates")
            
            # Validate places
            valid_places = []
            for p in places:
                if 'name' not in p:
                    continue
                p.setdefault('day', 'Day 1')
                p.setdefault('time', 'N/A')
                p.setdefault('description', p['name'])
                p.setdefault('duration', 60)
                valid_places.append(p)
            
            return valid_places
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            return self._fallback_extraction(itinerary_text)
        except Exception as e:
            logger.error(f"❌ Error extracting places: {e}")
            return []
    
    def _fallback_extraction(self, itinerary_text: str) -> list:
        """Fallback: extract basic info with default coordinates"""
        logger.warning("⚠️ Using fallback extraction method")
        places = []
        
        pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*[–-]\s*([^\n]+)'
        matches = re.findall(pattern, itinerary_text)
        
        base_lat, base_lng = 20.5937, 78.9629  # India center
        
        for i, (time, description) in enumerate(matches[:20]):
            places.append({
                "name": description[:60].strip(),
                "time": time,
                "day": f"Day {(i // 8) + 1}",
                "description": description.strip(),
                "duration": 60,
                "lat": base_lat + (i * 0.01) - 0.05,
                "lng": base_lng + (i * 0.008) - 0.04
            })
        
        return places
    
    def _geocode_places(self, places: list) -> list:
        """Geocode places without coordinates using OSM Nominatim and fetch Wikipedia images"""
        logger.info("🌍 Geocoding places and fetching images")

        for place in places:
            # Geocode if needed
            if 'lat' not in place or 'lng' not in place:
                try:
                    query = place['name']
                    url = "https://nominatim.openstreetmap.org/search"
                    params = {"q": query, "format": "json", "limit": 1}
                    headers = {"User-Agent": "travel-a2a-map-agent/1.0"}

                    r = requests.get(url, params=params, headers=headers, timeout=10)
                    r.raise_for_status()
                    data = r.json()

                    if data:
                        place['lat'] = float(data[0]['lat'])
                        place['lng'] = float(data[0]['lon'])
                        logger.info(f"📍 Geocoded: {place['name']}")

                    time.sleep(1)  # Be polite to OSM

                except Exception as e:
                    logger.error(f"Geocoding failed for {place['name']}: {e}")
            
            # Fetch Wikipedia image and extract
            if 'image' not in place or 'extract' not in place:
                image_url, extract = self._get_wikipedia_image(place['name'])
                
                if image_url:
                    place['image'] = image_url
                    logger.info(f"🖼️ Found image for: {place['name']}")
                else:
                    place['image'] = None
                
                if extract:
                    place['extract'] = extract
                    logger.info(f"📝 Found extract for: {place['name']}")
                else:
                    place['extract'] = None
                
                time.sleep(0.5)  # Be polite to Wikipedia

        return places
    
    def _get_wikipedia_image(self, place_name: str) -> tuple:
        """Fetch image and extract from Wikipedia API, fallback to Pixabay if not found"""
        try:
            title = re.split(r'[,(]', place_name)[0].strip()
            title_encoded = title.replace(" ", "_")
            
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
            headers = {"User-Agent": "travel-a2a-map-agent/1.0"}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            image_url = None
            if "originalimage" in data and data["originalimage"]:
                image_url = data["originalimage"]["source"]
            elif "thumbnail" in data and data["thumbnail"]:
                image_url = data["thumbnail"]["source"]
            
            extract = data.get("extract", None)
            
            # If no image found in Wikipedia, try Pixabay
            if not image_url:
                logger.info(f"📸 No Wikipedia image for {place_name}, trying Pixabay...")
                image_url = self._get_pixabay_image(place_name)
            
            return (image_url, extract)
            
        except Exception as e:
            logger.debug(f"Wikipedia fetch failed for {place_name}: {e}")
            # Try Pixabay as fallback
            try:
                image_url = self._get_pixabay_image(place_name)
                return (image_url, None)
            except:
                return (None, None)
    
    def _get_pixabay_image(self, place_name: str) -> Optional[str]:
        """Fetch image from Pixabay API"""
        try:
            import os
            api_key = os.getenv('PIXABAY_API')
            
            if not api_key:
                logger.warning("⚠️ PIXABAY_API key not found in .env")
                print("⚠️ PIXABAY_API key not found in .env")
                return None
            
            # Clean place name for search
            search_query = place_name.strip()
            
            url = "https://pixabay.com/api/"
            params = {
                'key': api_key,
                'q': search_query,
                'image_type': 'photo',
                'category': 'places',
                'orientation': 'horizontal',
                'safesearch': 'true',
                'per_page': 3
            }
            
            print(f"🔍 [PIXABAY] Searching for: {search_query}")
            print(f"🔍 [PIXABAY] API URL: {url}")
            
            headers = {"User-Agent": "travel-a2a-map-agent/1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"📊 [PIXABAY] Response status: {response.status_code}")
            print(f"📊 [PIXABAY] Total hits: {data.get('totalHits', 0)}")
            
            if data.get('hits') and len(data['hits']) > 0:
                # Get the first high-quality image
                image_url = data['hits'][0].get('largeImageURL') or data['hits'][0].get('webformatURL')
                logger.info(f"✅ Found Pixabay image for {place_name}")
                print(f"✅ [PIXABAY] Found image for {place_name}")
                print(f"🖼️ [PIXABAY] Image URL: {image_url[:80]}...")
                return image_url
            else:
                logger.info(f"ℹ️ No Pixabay images found for {place_name}")
                print(f"ℹ️ [PIXABAY] No images found for {place_name}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Pixabay fetch failed for {place_name}: {e}")
            print(f"❌ [PIXABAY] Error fetching image for {place_name}: {e}")
            return None
    
    
    def _create_display_text(self, places_data: list, map_path: str = None) -> str:
        """Create human-readable display text"""
        if not places_data:
            return "⚠️ Map could not be generated automatically for this itinerary."
        
        # Group by day
        by_day = {}
        for place in places_data:
            day = place.get('day', 'Day 1')
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(place)
        
        summary = f"""
🗺️ **INTERACTIVE MAP DATA READY**

✅ Successfully extracted **{len(places_data)} locations** from your itinerary!

**Map Features:**
• 📍 Color-coded markers by day
• 🖱️ Click markers for timing & details  
• 📋 Interactive navigation
• **100% FREE** - No API keys needed!
• Powered by OpenStreetMap & Leaflet.js

**Places Overview:**
"""
        
        # Sort days - handle None values properly
        sorted_days = sorted(by_day.keys(), key=lambda x: (x is None, x if x is not None else ''))
        
        for day in sorted_days:
            day_label = day if day else "Unscheduled"
            summary += f"\n**{day_label}:** {len(by_day[day])} stops\n"
            for place in by_day[day][:3]:
                summary += f"• {place.get('time', 'N/A')} - {place['name']}\n"
            if len(by_day[day]) > 3:
                summary += f"• ... +{len(by_day[day]) - 3} more\n"
        
        summary += f"\n💡 **Tip:** Map will be displayed in the web interface.\n"
        
        return summary
    
    def _create_map_data(self, places_data: list, map_path: str = None) -> MapData:
        """Create structured map data"""
        locations = []
        
        for place in places_data:
            # Extract day number
            day_str = place.get('day', 'Day 1')
            day_num = int(re.search(r'\d+', day_str).group()) if re.search(r'\d+', day_str) else 1
            
            locations.append(MapLocation(
                name=place['name'],
                latitude=place.get('lat', 0.0),
                longitude=place.get('lng', 0.0),
                day=day_num,
                time=place.get('time', 'N/A'),
                description=place.get('description'),
                duration=place.get('duration'),  # Add duration field
                image=place.get('image'),  # Add Wikipedia image URL
                extract=place.get('extract')  # Add Wikipedia extract
            ))
        
        return MapData(
            url=map_path or "",  # Empty string if no HTML file
            locations=locations,
            total_locations=len(locations)
        )
    
    def _create_structured_response(
        self,
        display_text: str,
        map_data: MapData,
        map_html: str = None
    ) -> StructuredResponse:
        """Create complete structured response"""
        
        return StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.SUCCESS,
            data_type=DataType.MAP,
            data={
                "map": map_data.model_dump()
                # No HTML included - frontend will render the map
            },
            display=DisplayFormat(
                text=display_text,
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["MapAgent"]
            )
        )
    
    def _create_error_response(self, error_msg: str) -> str:
        """Create error response"""
        response = StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.ERROR,
            data_type=DataType.MAP,
            data={},
            display=DisplayFormat(
                text=f"❌ Error generating map: {error_msg}",
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["MapAgent"]
            ),
            error=error_msg
        )
        return response.model_dump_json(indent=2)
