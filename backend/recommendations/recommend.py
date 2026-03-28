"""
Place Recommendation API Endpoint
==================================

This module provides functionality to recommend tourist attractions and hotels
near a given place by integrating Wikipedia and OpenStreetMap Overpass APIs.

Features:
- Fetches place coordinates from Wikipedia
- Queries nearby attractions and hotels from Overpass API
- Enriches results with Wikipedia images and descriptions

Author: Travel Recommendation System
Date: 2024
"""

import re
import requests
import logging
import time
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaceRecommendationService:
    """Service class for place recommendations using Wikipedia and Overpass APIs"""
    
    # API Configuration
    WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1/page/summary"
    WIKIPEDIA_GEOSEARCH_API = "https://en.wikipedia.org/w/api.php"
    OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
    
    # Search radius in meters (50km - reduced for faster queries)
    SEARCH_RADIUS = 50000
    
    # Request timeout in seconds (reduced for Vercel)
    REQUEST_TIMEOUT = 10
    
    # Overpass API timeout for query execution (reduced for Vercel)
    OVERPASS_TIMEOUT = 15
    
    # Maximum number of places to fetch from Overpass (reduced for faster processing)
    MAX_PLACES_FROM_OVERPASS = 30
    
    # Maximum number of places to fetch from Wikipedia Geosearch (reduced for faster processing)
    MAX_PLACES_FROM_WIKIPEDIA = 20
    
    # Geosearch radius in meters (10km for Wikipedia API)
    GEOSEARCH_RADIUS = 10000
    
    # Maximum number of enriched results to return
    MAX_RESULTS = 100
    
    # Delay between Wikipedia API calls (seconds)
    WIKIPEDIA_DELAY = 0.1
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "travel-recommendation-api/1.0"
        })
    
    def get_place_recommendations(self, place_name: str) -> Dict:
        """
        Get recommendations for tourist attractions and hotels near a place.
        
        Args:
            place_name: Name of the place to search around
            
        Returns:
            Dictionary with status and results
        """
        try:
            logger.info(f"Getting recommendations for: {place_name}")
            
            # Step 1: Get place coordinates from Wikipedia
            coordinates = self._get_place_coordinates(place_name)
            if not coordinates:
                return {
                    "success": False,
                    "message": f"Could not find coordinates for '{place_name}'",
                    "results": []
                }
            
            lat, lon = coordinates
            logger.info(f"Found coordinates: lat={lat}, lon={lon}")
            
            # Step 2: Get places from both Wikipedia Geosearch and Overpass API
            wikipedia_places = self._get_wikipedia_geosearch_places(lat, lon, place_name)
            logger.info(f"Found {len(wikipedia_places)} places from Wikipedia Geosearch")
            print("----------------------------wikipedia_places LIST----------------------------")
            logger.info(f"Total {len(wikipedia_places)} unique places after merging")
            print(wikipedia_places)
            print("----------------------------wikipedia_places LIST----------------------------")
            overpass_places = self._get_nearby_places(lat, lon)
            logger.info(f"Found {len(overpass_places)} places from Overpass API")
            
            # Combine and deduplicate places
            all_places = self._merge_place_lists(wikipedia_places, overpass_places, place_name)
            print("----------------------------RECOMMEND LIST----------------------------")
            logger.info(f"Total {len(all_places)} unique places after merging")
            print(all_places)
            print("----------------------------RECOMMEND LIST----------------------------")

            
            # Step 3: Enrich each place with Wikipedia data
            enriched_places = self._enrich_places_with_wikipedia(all_places)
            logger.info(f"Enriched {len(enriched_places)} places with Wikipedia data")
            
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
        """
        Fetch place coordinates from Wikipedia API, with Nominatim fallback.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Try Wikipedia first
        try:
            # Convert spaces to underscores for Wikipedia URL
            place_name_formatted = place_name.strip().replace(" ", "_")
            
            url = f"{self.WIKIPEDIA_API_BASE}/{place_name_formatted}"
            logger.debug(f"Fetching Wikipedia data from: {url}")
            
            response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract coordinates
            if "coordinates" in data:
                lat = data["coordinates"]["lat"]
                lon = data["coordinates"]["lon"]
                logger.info(f"Found coordinates from Wikipedia: {lat}, {lon}")
                return (lat, lon)
            else:
                logger.warning(f"No coordinates in Wikipedia for: {place_name}")
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Wikipedia page not found for: {place_name}")
            else:
                logger.error(f"Wikipedia API error: {e}")
        except Exception as e:
            logger.error(f"Error fetching coordinates from Wikipedia: {e}")
        
        # Fallback to Nominatim (OpenStreetMap)
        logger.info(f"Trying Nominatim geocoding for: {place_name}")
        return self._get_coordinates_from_nominatim(place_name)
    
    def _get_coordinates_from_nominatim(self, place_name: str) -> Optional[Tuple[float, float]]:
        """
        Fetch place coordinates from Nominatim (OpenStreetMap) API.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": place_name,
                "format": "json",
                "limit": 1
            }
            
            headers = {
                "User-Agent": "travel-recommendation-api/1.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(f"Found coordinates from Nominatim: {lat}, {lon}")
                return (lat, lon)
            else:
                logger.warning(f"No coordinates found in Nominatim for: {place_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching coordinates from Nominatim: {e}")
            return None
    
    def _get_wikipedia_geosearch_places(self, lat: float, lon: float, search_place_name: str = "") -> List[Dict]:
        """
        Get places from Wikipedia Geosearch API.
        Excludes metro stations and other unwanted places.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            search_place_name: Name of the place being searched (to exclude from results)
            
        Returns:
            List of places from Wikipedia
        """
        try:
            params = {
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{lat}|{lon}",
                "gsradius": self.GEOSEARCH_RADIUS,
                "gslimit": self.MAX_PLACES_FROM_WIKIPEDIA,
                "format": "json"
            }
            
            logger.debug(f"Querying Wikipedia Geosearch API around: {lat}, {lon}")
            logger.info(f"Wikipedia Geosearch radius: {self.GEOSEARCH_RADIUS} meters ({self.GEOSEARCH_RADIUS/1000}km)")
            
            response = self.session.get(
                self.WIKIPEDIA_GEOSEARCH_API,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            places = []
            
            # Exclusion keywords
            exclude_keywords = [
                "metro station",
                "railway station",
                "bus station",
                "assembly constituency",
                "airport",
                "junction",
                "school",
                "institute",
                "college",
                "university",
                "galaxy",
                "diamond",
                "atlantic",
                # Continents
                "africa",
                "antarctica",
                "asia",
                "europe",
                "north america",
                "south america",
                "oceania",
                "australia",
                search_place_name.lower()  # Exclude the search place itself
            ]
            
            for item in data.get("query", {}).get("geosearch", []):
                title = item.get("title", "")
                
                # Skip if title contains excluded keywords
                if any(keyword in title.lower() for keyword in exclude_keywords if keyword):
                    logger.debug(f"Excluding: {title}")
                    continue
                
                place = {
                    "name": title,
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "type": "attraction",  # Default type, will be refined later
                    "source": "wikipedia"
                }
                places.append(place)
            
            logger.info(f"Wikipedia Geosearch returned {len(places)} valid places")
            return places
            
        except Exception as e:
            logger.error(f"Error querying Wikipedia Geosearch API: {e}")
            return []
    
    def _merge_place_lists(self, wikipedia_places: List[Dict], overpass_places: List[Dict], search_place_name: str = "") -> List[Dict]:
        """
        Merge places from Wikipedia and Overpass, removing duplicates by name.
        Also filters out unwanted places from both sources.
        
        Args:
            wikipedia_places: Places from Wikipedia Geosearch
            overpass_places: Places from Overpass API
            search_place_name: Name of the place being searched (to exclude from results)
            
        Returns:
            Merged list of unique places
        """
        # Exclusion keywords (same as Wikipedia Geosearch)
        exclude_keywords = [
            "metro station",
            "railway station",
            "bus station",
            "assembly constituency",
            "airport",
            "junction",
            "school",
            "institute",
            "college",
            "university",
            "galaxy",
            "diamond",
            "atlantic",
            # Continents
            "africa",
            "antarctica",
            "asia",
            "europe",
            "north america",
            "south america",
            "oceania",
            "australia",
            search_place_name.lower()
        ]
        
        places_dict = {}
        
        # Add Wikipedia places first (they tend to be more notable)
        for place in wikipedia_places:
            name = place.get("name")
            if name:
                places_dict[name.lower()] = place
        
        # Add Overpass places (skip if name already exists or contains excluded keywords)
        for place in overpass_places:
            name = place.get("name")
            if name and name.lower() not in places_dict:
                # Check if name contains any excluded keywords
                if not any(keyword in name.lower() for keyword in exclude_keywords if keyword):
                    places_dict[name.lower()] = place
                else:
                    logger.debug(f"Excluding from Overpass: {name}")
        
        merged_places = list(places_dict.values())
        logger.info(f"Merged {len(wikipedia_places)} Wikipedia + {len(overpass_places)} Overpass = {len(merged_places)} unique places")
        return merged_places
    
    def _get_nearby_places(self, lat: float, lon: float) -> List[Dict]:
        """
        Query Overpass API for nearby tourist attractions and hotels.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            List of places with basic information (limited and deduplicated)
        """
        try:
            # Build Overpass query with limit
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
            
            logger.debug(f"Querying Overpass API around: {lat}, {lon}")
            logger.info(f"Overpass search radius: {self.SEARCH_RADIUS} meters ({self.SEARCH_RADIUS/1000}km)")
            
            response = self.session.get(
                self.OVERPASS_API_URL,
                params={"data": query},
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant places and remove duplicates
            places_dict = {}  # Use dict to remove duplicates by name
            
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name")
                
                # Only include places with names
                if name:
                    # Skip if already added (remove duplicates)
                    if name in places_dict:
                        continue
                    
                    # Get coordinates (handle both nodes and ways)
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
            
            places = list(places_dict.values())
            logger.info(f"Found {len(places)} unique places after deduplication")
            return places
            
        except requests.exceptions.Timeout:
            logger.error(f"Overpass API timeout - trying alternative approach")
            # Try with smaller radius as fallback
            return self._get_nearby_places_fallback(lat, lon)
        except Exception as e:
            logger.error(f"Error querying Overpass API: {e}")
            return []
    
    def _get_nearby_places_fallback(self, lat: float, lon: float) -> List[Dict]:
        """
        Fallback method with smaller radius when main query times out.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            List of places with basic information
        """
        try:
            # Use smaller radius (10km) for faster query
            smaller_radius = 10000
            
            query = f"""
            [out:json][timeout:15];
            (
              node["tourism"="attraction"](around:{smaller_radius},{lat},{lon});
              node["historic"="monument"](around:{smaller_radius},{lat},{lon});
            );
            out body 50;
            """
            
            logger.info(f"Using fallback query with {smaller_radius}m radius")
            
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
                        place = {
                            "name": name,
                            "lat": element.get("lat"),
                            "lon": element.get("lon"),
                            "type": self._determine_place_type(tags)
                        }
                        places.append(place)
            
            return places
            
        except Exception as e:
            logger.error(f"Fallback query also failed: {e}")
            return []
    
    def _determine_place_type(self, tags: Dict) -> str:
        """
        Determine the type of place based on OSM tags.
        
        Args:
            tags: Dictionary of OSM tags
            
        Returns:
            Place type string
        """
        if tags.get("tourism") == "hotel":
            return "hotel"
        elif tags.get("historic") == "monument":
            return "monument"
        elif tags.get("tourism") == "attraction":
            return "attraction"
        else:
            return "other"
    
    def _enrich_places_with_wikipedia(self, places: List[Dict]) -> List[Dict]:
        """
        Enrich places with Wikipedia images and descriptions in batches.
        Only includes places that have images available.
        Processes in batches to avoid rate limiting.
        Removes duplicates based on image URL.
        
        Args:
            places: List of places with basic information
            
        Returns:
            List of enriched places with images and descriptions (filtered to only include places with images)
        """
        enriched_places = []
        seen_images = set()  # Track image URLs to avoid duplicates
        batch_size = 100
        total_places = len(places)
        
        logger.info(f"Processing {total_places} places in batches of {batch_size}")
        
        for batch_start in range(0, total_places, batch_size):
            batch_end = min(batch_start + batch_size, total_places)
            batch = places[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: places {batch_start+1} to {batch_end}")
            
            for idx, place in enumerate(batch):
                # Stop if we've reached the maximum results
                if len(enriched_places) >= self.MAX_RESULTS:
                    logger.info(f"Reached maximum results limit ({self.MAX_RESULTS})")
                    return enriched_places
                
                name = place.get("name")
                if not name:
                    continue
                
                # Add small delay to avoid rate limiting
                if idx > 0:
                    time.sleep(self.WIKIPEDIA_DELAY)
                
                # Fetch Wikipedia data
                image_url, extract = self._get_wikipedia_image(name)
                
                # Only include places that have images
                if not image_url:
                    logger.debug(f"Skipping {name} - no image available")
                    continue
                
                # Skip if we've already seen this image (duplicate place)
                if image_url in seen_images:
                    logger.debug(f"Skipping {name} - duplicate image")
                    continue
                
                seen_images.add(image_url)
                
                # Create enriched place object
                enriched_place = {
                    "name": name,
                    "lat": place.get("lat"),
                    "lon": place.get("lon"),
                    "type": place.get("type"),
                    "image": image_url,
                    "extract": extract
                }
                
                enriched_places.append(enriched_place)
            
            # Add delay between batches
            if batch_end < total_places and len(enriched_places) < self.MAX_RESULTS:
                logger.info(f"Batch complete. Waiting before next batch...")
                time.sleep(2)  # 2 second delay between batches
        
        logger.info(f"Successfully enriched {len(enriched_places)} unique places with images")
        return enriched_places
    
    def _get_wikipedia_image(self, place_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch high-quality image and extract from Wikipedia API.
        
        Args:
            place_name: Name of the place
            
        Returns:
            Tuple of (image_url, extract) or (None, None)
        """
        try:
            # Clean and format place name for Wikipedia
            # Keep only text before "(" or ","
            title = re.split(r'[,(]', place_name)[0].strip()
            # Replace spaces with underscores for URL
            title_encoded = title.replace(" ", "_")
            
            url = f"{self.WIKIPEDIA_API_BASE}/{title_encoded}"
            
            response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Get image URL (prefer original, fallback to thumbnail)
            image_url = None
            if "originalimage" in data and data["originalimage"]:
                image_url = data["originalimage"]["source"]
            elif "thumbnail" in data and data["thumbnail"]:
                image_url = data["thumbnail"]["source"]
            
            # Get extract (description)
            extract = data.get("extract", None)
            
            return (image_url, extract)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"Wikipedia page not found for: {place_name}")
            elif e.response.status_code == 429:
                logger.warning(f"Rate limited by Wikipedia API for: {place_name}")
                # Add longer delay on rate limit
                time.sleep(1)
            else:
                logger.warning(f"Wikipedia API error for {place_name}: {e}")
            return (None, None)
        except Exception as e:
            logger.warning(f"Failed to fetch Wikipedia data for {place_name}: {e}")
            return (None, None)


# Global service instance
recommendation_service = PlaceRecommendationService()


def get_place_recommendations(place_name: str) -> Dict:
    """
    Public function to get place recommendations.
    
    Args:
        place_name: Name of the place to search around
        
    Returns:
        Dictionary with recommendations
    """
    return recommendation_service.get_place_recommendations(place_name)