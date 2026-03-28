"""
Place Recommendation API Endpoint (Optimized)
==============================================
Features:
- Caching for Wikipedia and Overpass API calls
- Connection pooling with requests.Session
- Better error handling
- Reduced API calls
"""

import re
import requests
import logging
import time
from typing import List, Dict, Optional, Tuple
from functools import lru_cache
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaceRecommendationService:
    """Optimized service for place recommendations"""
    
    # API Configuration
    WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1/page/summary"
    OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
    NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
    
    # Configuration
    SEARCH_RADIUS = 100000  # 100km
    REQUEST_TIMEOUT = 30
    OVERPASS_TIMEOUT = 25
    MAX_PLACES_FROM_OVERPASS = 100
    MAX_RESULTS = 100
    WIKIPEDIA_DELAY = 0.1
    
    # Cache settings
    CACHE_DURATION = timedelta(hours=24)
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "travel-recommendation-api/2.0"
        })
        self._coordinate_cache = {}
        self._wikipedia_cache = {}
    
    @lru_cache(maxsize=128)
    def _get_cached_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """Get coordinates with caching"""
        return self._get_place_coordinates(place_name)
    
    def get_place_recommendations(self, place_name: str) -> Dict:
        """Get recommendations with caching and optimization"""
        try:
            logger.info(f"Getting recommendations for: {place_name}")
            
            # Get coordinates (cached)
            coordinates = self._get_cached_coordinates(place_name)
            if not coordinates:
                return {
                    "success": False,
                    "message": f"Could not find coordinates for '{place_name}'",
                    "results": []
                }
            
            lat, lon = coordinates
            logger.info(f"Found coordinates: lat={lat}, lon={lon}")
            
            # Get nearby places
            places = self._get_nearby_places(lat, lon)
            logger.info(f"Found {len(places)} places from Overpass API")
            
            # Enrich with Wikipedia data (with caching)
            enriched_places = self._enrich_places_with_wikipedia(places)
            logger.info(f"Enriched {len(enriched_places)} places")
            
            return {
                "success": True,
                "message": f"Found {len(enriched_places)} recommendations near {place_name}",
                "search_location": {
                    "name": place_name,
                    "lat": lat,
                    "lon": lon
                },
                "results": enriched_places
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return {
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "results": []
            }
    
    def _get_place_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """Fetch place coordinates from Wikipedia or Nominatim"""
        # Try Wikipedia first
        try:
            place_name_formatted = place_name.strip().replace(" ", "_")
            url = f"{self.WIKIPEDIA_API_BASE}/{place_name_formatted}"
            
            response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if "coordinates" in data:
                return (data["coordinates"]["lat"], data["coordinates"]["lon"])
        except Exception as e:
            logger.debug(f"Wikipedia coordinates failed: {e}")
        
        # Fallback to Nominatim
        try:
            params = {
                "q": place_name,
                "format": "json",
                "limit": 1
            }
            response = self.session.get(
                self.NOMINATIM_API_URL,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            if data:
                return (float(data[0]["lat"]), float(data[0]["lon"]))
        except Exception as e:
            logger.error(f"Nominatim coordinates failed: {e}")
        
        return None
    
    def _get_nearby_places(self, lat: float, lon: float) -> List[Dict]:
        """Query Overpass API for nearby places"""
        try:
            query = f"""
            [out:json][timeout:{self.OVERPASS_TIMEOUT}];
            (
              node["tourism"="attraction"](around:{self.SEARCH_RADIUS},{lat},{lon});
              node["historic"="monument"](around:{self.SEARCH_RADIUS},{lat},{lon});
              node["tourism"="hotel"](around:{self.SEARCH_RADIUS},{lat},{lon});
              way["tourism"="attraction"](around:{self.SEARCH_RADIUS},{lat},{lon});
              way["historic"="monument"](around:{self.SEARCH_RADIUS},{lat},{lon});
            );
            out center body {self.MAX_PLACES_FROM_OVERPASS};
            """
            
            response = self.session.get(
                self.OVERPASS_API_URL,
                params={"data": query},
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract and deduplicate places
            places_dict = {}
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name")
                
                if name and name not in places_dict:
                    if element.get("type") == "node":
                        place_lat = element.get("lat")
                        place_lon = element.get("lon")
                    elif element.get("type") == "way" and "center" in element:
                        place_lat = element["center"].get("lat")
                        place_lon = element["center"].get("lon")
                    else:
                        continue
                    
                    places_dict[name] = {
                        "name": name,
                        "lat": place_lat,
                        "lon": place_lon,
                        "type": self._determine_place_type(tags)
                    }
            
            return list(places_dict.values())
            
        except requests.exceptions.Timeout:
            logger.warning("Overpass API timeout, using fallback")
            return self._get_nearby_places_fallback(lat, lon)
        except Exception as e:
            logger.error(f"Error querying Overpass API: {e}")
            return []
    
    def _get_nearby_places_fallback(self, lat: float, lon: float) -> List[Dict]:
        """Fallback with smaller radius"""
        try:
            smaller_radius = 10000
            query = f"""
            [out:json][timeout:15];
            (
              node["tourism"="attraction"](around:{smaller_radius},{lat},{lon});
              node["historic"="monument"](around:{smaller_radius},{lat},{lon});
            );
            out body 50;
            """
            
            response = self.session.get(
                self.OVERPASS_API_URL,
                params={"data": query},
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            
            places = []
            for element in data.get("elements", []):
                if element.get("type") == "node":
                    tags = element.get("tags", {})
                    name = tags.get("name")
                    if name:
                        places.append({
                            "name": name,
                            "lat": element.get("lat"),
                            "lon": element.get("lon"),
                            "type": self._determine_place_type(tags)
                        })
            return places
        except Exception as e:
            logger.error(f"Fallback query failed: {e}")
            return []
    
    def _determine_place_type(self, tags: Dict) -> str:
        """Determine place type from OSM tags"""
        if tags.get("tourism") == "hotel":
            return "hotel"
        elif tags.get("historic") == "monument":
            return "monument"
        elif tags.get("tourism") == "attraction":
            return "attraction"
        return "other"
    
    def _enrich_places_with_wikipedia(self, places: List[Dict]) -> List[Dict]:
        """Enrich places with Wikipedia data (with caching)"""
        enriched_places = []
        seen_images = set()
        
        for place in places[:self.MAX_RESULTS]:
            if len(enriched_places) >= self.MAX_RESULTS:
                break
            
            name = place.get("name")
            if not name:
                continue
            
            # Get Wikipedia data (cached)
            image_url, extract = self._get_wikipedia_image_cached(name)
            
            if image_url and image_url not in seen_images:
                seen_images.add(image_url)
                enriched_places.append({
                    **place,
                    "image": image_url,
                    "extract": extract
                })
            
            time.sleep(self.WIKIPEDIA_DELAY)
        
        return enriched_places
    
    @lru_cache(maxsize=512)
    def _get_wikipedia_image_cached(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Get Wikipedia image with caching"""
        try:
            title = re.split(r'[,(]', place_name)[0].strip()
            title_encoded = title.replace(" ", "_")
            url = f"{self.WIKIPEDIA_API_BASE}/{title_encoded}"
            
            response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            image_url = None
            if "originalimage" in data and data["originalimage"]:
                image_url = data["originalimage"]["source"]
            elif "thumbnail" in data and data["thumbnail"]:
                image_url = data["thumbnail"]["source"]
            
            extract = data.get("extract", None)
            return (image_url, extract)
            
        except Exception as e:
            logger.debug(f"Wikipedia fetch failed for {place_name}: {e}")
            return (None, None)


# Global service instance
recommendation_service = PlaceRecommendationService()


def get_place_recommendations(place_name: str) -> Dict:
    """Public function to get place recommendations"""
    return recommendation_service.get_place_recommendations(place_name)
