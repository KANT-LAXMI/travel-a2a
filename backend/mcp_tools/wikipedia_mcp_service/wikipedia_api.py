"""
Wikipedia API Service
=====================
Provides Wikipedia search and article retrieval functionality.

This service integrates Wikipedia API to enhance the Travel Buddy
system with rich destination information, historical context, and cultural details.

Features:
- Search Wikipedia articles
- Get article summaries
- Extract destination information
- Provide cultural and historical context

Integration with Travel Buddy:
- Places Agent: Get destination background information
- Can be used by any agent needing Wikipedia data
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


class WikipediaMCP:
    """
    Wikipedia API Client
    
    Provides methods to interact with Wikipedia API for travel-related information.
    Uses the free Wikipedia API - no authentication required.
    """
    
    def __init__(self):
        """Initialize Wikipedia API client"""
        self.base_url = "https://en.wikipedia.org/api/rest_v1"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.user_agent = "TravelBuddy/1.0 (Educational Project)"
        logger.info("✅ Wikipedia API Service initialized")
    
    def search_articles(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search Wikipedia articles
        
        Args:
            query: Search query (e.g., "Goa India", "Eiffel Tower")
            limit: Maximum number of results (default: 5)
        
        Returns:
            List of article dictionaries with title, description, and page_id
        
        Example:
            >>> wiki = WikipediaMCP()
            >>> results = wiki.search_articles("Goa India")
            >>> print(results[0]['title'])
            'Goa'
        """
        logger.info(f"🔍 Searching Wikipedia for: {query}")
        
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': limit,
                'srprop': 'snippet'
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'query' not in data or 'search' not in data['query']:
                logger.warning(f"⚠️ No search results found for: {query}")
                return []
            
            results = []
            for item in data['query']['search']:
                # Clean HTML tags from snippet
                snippet = item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
                
                results.append({
                    'title': item.get('title', ''),
                    'page_id': item.get('pageid', 0),
                    'snippet': snippet,
                    'word_count': item.get('wordcount', 0)
                })
            
            logger.info(f"✅ Found {len(results)} Wikipedia articles")
            return results
            
        except Exception as e:
            logger.error(f"❌ Wikipedia search error: {e}")
            return []
    
    def get_article_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get Wikipedia article summary
        
        Args:
            title: Article title (e.g., "Goa", "Paris")
        
        Returns:
            Dictionary with title, extract (summary), and thumbnail
        
        Example:
            >>> wiki = WikipediaMCP()
            >>> summary = wiki.get_article_summary("Goa")
            >>> print(summary['extract'][:100])
            'Goa is a state on the southwestern coast of India...'
        """
        logger.info(f"📖 Getting Wikipedia summary for: {title}")
        
        try:
            # URL encode the title
            encoded_title = quote(title.replace(' ', '_'))
            url = f"{self.base_url}/page/summary/{encoded_title}"
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            result = {
                'title': data.get('title', ''),
                'extract': data.get('extract', ''),
                'description': data.get('description', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', None),
                'coordinates': {
                    'lat': data.get('coordinates', {}).get('lat'),
                    'lon': data.get('coordinates', {}).get('lon')
                } if 'coordinates' in data else None,
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
            }
            
            logger.info(f"✅ Retrieved summary for: {title}")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ Article not found: {title}")
            else:
                logger.error(f"❌ HTTP error getting summary: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting summary: {e}")
            return None
    
    def get_destination_info(self, destination: str) -> Dict[str, Any]:
        """
        Get comprehensive destination information from Wikipedia
        
        This is the main method for Travel Buddy integration.
        Searches for the destination and returns detailed information.
        
        Args:
            destination: Destination name (e.g., "Goa", "Paris", "Tokyo")
        
        Returns:
            Dictionary with:
            - title: Article title
            - summary: Short description
            - extract: Full summary text
            - thumbnail: Image URL
            - coordinates: Lat/lon if available
            - url: Wikipedia article URL
            - related_articles: List of related articles
        
        Example:
            >>> wiki = WikipediaMCP()
            >>> info = wiki.get_destination_info("Goa")
            >>> print(info['summary'])
            'State on the southwestern coast of India'
        """
        logger.info(f"🌍 Getting destination info for: {destination}")
        
        try:
            # Step 1: Search for the destination
            search_results = self.search_articles(destination, limit=1)
            
            if not search_results:
                logger.warning(f"⚠️ No Wikipedia article found for: {destination}")
                return {
                    'found': False,
                    'message': f"No Wikipedia article found for '{destination}'"
                }
            
            # Step 2: Get detailed summary of top result
            top_result = search_results[0]
            summary = self.get_article_summary(top_result['title'])
            
            if not summary:
                return {
                    'found': False,
                    'message': f"Could not retrieve details for '{destination}'"
                }
            
            # Step 3: Search for related articles (tourism, culture, history)
            related_queries = [
                f"{destination} tourism",
                f"{destination} culture",
                f"{destination} attractions"
            ]
            
            related_articles = []
            for query in related_queries:
                results = self.search_articles(query, limit=2)
                related_articles.extend([r['title'] for r in results if r['title'] != top_result['title']])
            
            # Remove duplicates
            related_articles = list(set(related_articles))[:5]
            
            # Step 4: If no thumbnail, try Pixabay
            thumbnail = summary['thumbnail']
            if not thumbnail:
                logger.info(f"📸 No Wikipedia thumbnail for {destination}, trying Pixabay...")
                thumbnail = self._get_pixabay_image(destination)
            
            # Step 5: Compile comprehensive information
            destination_info = {
                'found': True,
                'title': summary['title'],
                'summary': summary['description'],
                'extract': summary['extract'],
                'thumbnail': thumbnail,
                'coordinates': summary['coordinates'],
                'url': summary['url'],
                'related_articles': related_articles
            }
            
            logger.info(f"✅ Destination info compiled for: {destination}")
            return destination_info
            
        except Exception as e:
            logger.error(f"❌ Error getting destination info: {e}")
            return {
                'found': False,
                'message': f"Error retrieving information: {str(e)}"
            }
    
    def _get_pixabay_image(self, place_name: str) -> Optional[str]:
        """Fetch image from Pixabay API as fallback"""
        try:
            import os
            api_key = os.getenv('PIXABAY_API')
            
            if not api_key:
                logger.warning("⚠️ PIXABAY_API key not found in .env")
                print("⚠️ [PIXABAY-WIKI] PIXABAY_API key not found in .env")
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
            
            print(f"🔍 [PIXABAY-WIKI] Searching for destination: {search_query}")
            print(f"🔍 [PIXABAY-WIKI] API URL: {url}")
            
            headers = {"User-Agent": "travel-buddy-wikipedia-service/1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            print(f"📊 [PIXABAY-WIKI] Response status: {response.status_code}")
            print(f"📊 [PIXABAY-WIKI] Total hits: {data.get('totalHits', 0)}")
            
            if data.get('hits') and len(data['hits']) > 0:
                # Get the first high-quality image
                image_url = data['hits'][0].get('largeImageURL') or data['hits'][0].get('webformatURL')
                logger.info(f"✅ Found Pixabay image for {place_name}")
                print(f"✅ [PIXABAY-WIKI] Found destination image for {place_name}")
                print(f"🖼️ [PIXABAY-WIKI] Image URL: {image_url[:80]}...")
                return image_url
            else:
                logger.info(f"ℹ️ No Pixabay images found for {place_name}")
                print(f"ℹ️ [PIXABAY-WIKI] No images found for {place_name}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Pixabay fetch failed for {place_name}: {e}")
            print(f"❌ [PIXABAY-WIKI] Error fetching image for {place_name}: {e}")
            return None
    
    def get_travel_context(self, destination: str) -> str:
        """
        Get formatted travel context for LLM consumption
        
        This method formats Wikipedia information in a way that's
        easy for the LLM to understand and use in trip planning.
        
        Args:
            destination: Destination name
        
        Returns:
            Formatted string with destination context
        
        Example:
            >>> wiki = WikipediaMCP()
            >>> context = wiki.get_travel_context("Goa")
            >>> print(context)
            '''
            DESTINATION: Goa
            DESCRIPTION: State on the southwestern coast of India
            
            OVERVIEW:
            Goa is a state on the southwestern coast of India...
            
            COORDINATES: 15.2993° N, 74.1240° E
            
            RELATED TOPICS:
            - Goa tourism
            - Goan culture
            ...
            '''
        """
        logger.info(f"📝 Formatting travel context for: {destination}")
        
        info = self.get_destination_info(destination)
        
        if not info.get('found'):
            return f"⚠️ {info.get('message', 'Information not available')}"
        
        # Format context for LLM
        context = f"""
═══════════════════════════════════════════════════════════════════════════
WIKIPEDIA DESTINATION CONTEXT
═══════════════════════════════════════════════════════════════════════════

DESTINATION: {info['title']}
DESCRIPTION: {info['summary']}

OVERVIEW:
{info['extract']}

"""
        
        # Add coordinates if available
        if info['coordinates']:
            context += f"COORDINATES: {info['coordinates']['lat']}° N, {info['coordinates']['lon']}° E\n\n"
        
        # Add related articles
        if info['related_articles']:
            context += "RELATED TOPICS:\n"
            for article in info['related_articles']:
                context += f"- {article}\n"
            context += "\n"
        
        # Add Wikipedia URL
        context += f"SOURCE: {info['url']}\n"
        context += "═══════════════════════════════════════════════════════════════════════════\n"
        
        logger.info(f"✅ Travel context formatted for: {destination}")
        return context


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR EASY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def search_wikipedia(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to search Wikipedia
    
    Args:
        query: Search query
        limit: Maximum results
    
    Returns:
        List of article dictionaries
    """
    wiki = WikipediaMCP()
    return wiki.search_articles(query, limit)


def get_destination_context(destination: str) -> str:
    """
    Convenience function to get destination context
    
    Args:
        destination: Destination name
    
    Returns:
        Formatted context string
    """
    wiki = WikipediaMCP()
    return wiki.get_travel_context(destination)


def get_article_info(title: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get article summary
    
    Args:
        title: Article title
    
    Returns:
        Article summary dictionary
    """
    wiki = WikipediaMCP()
    return wiki.get_article_summary(title)


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Test Wikipedia MCP functionality"""
    
    print("\n" + "="*80)
    print("🧪 TESTING WIKIPEDIA MCP")
    print("="*80 + "\n")
    
    wiki = WikipediaMCP()
    
    # Test 1: Search articles
    print("📝 Test 1: Search for 'Goa India'")
    print("-" * 80)
    results = wiki.search_articles("Goa India", limit=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['snippet'][:100]}...")
        print()
    
    # Test 2: Get article summary
    print("\n📝 Test 2: Get summary for 'Goa'")
    print("-" * 80)
    summary = wiki.get_article_summary("Goa")
    if summary:
        print(f"Title: {summary['title']}")
        print(f"Description: {summary['description']}")
        print(f"Extract: {summary['extract'][:200]}...")
        print(f"Coordinates: {summary['coordinates']}")
        print(f"URL: {summary['url']}")
    
    # Test 3: Get destination info
    print("\n📝 Test 3: Get destination info for 'Paris'")
    print("-" * 80)
    info = wiki.get_destination_info("Paris")
    if info.get('found'):
        print(f"Title: {info['title']}")
        print(f"Summary: {info['summary']}")
        print(f"Related: {', '.join(info['related_articles'][:3])}")
    
    # Test 4: Get travel context
    print("\n📝 Test 4: Get travel context for 'Tokyo'")
    print("-" * 80)
    context = wiki.get_travel_context("Tokyo")
    print(context[:500] + "...")
    
    print("\n" + "="*80)
    print("✅ WIKIPEDIA MCP TESTS COMPLETE")
    print("="*80 + "\n")
