"""
Integrated Travel Planner for Vercel Deployment
================================================
Combines all agents (budget, places, map, rag) without A2A architecture
"""

import logging
import os
import sys
import json
from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
import requests

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

logger = logging.getLogger(__name__)


class IntegratedTravelPlanner:
    """
    Integrated travel planner that works in serverless environment
    Uses actual agent implementations directly
    """
    
    def __init__(self):
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        # Import agents
        try:
            from backend.agents.budget_agent.agent import BudgetAgent
            from backend.agents.places_agent.agent import PlacesAgent
            from backend.agents.map_agent.agent import MapAgent
            
            self.budget_agent = BudgetAgent()
            self.places_agent = PlacesAgent()
            self.map_agent = MapAgent()
            
            logger.info("✅ All agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise
    
    def plan_trip(self, query: str, session_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict:
        """
        Plan a trip using all agents
        
        Args:
            query: User's trip planning request
            session_id: Optional session ID
            user_id: Optional user ID for saving to database
            
        Returns:
            Dictionary with complete trip plan
        """
        try:
            logger.info(f"🚀 Planning trip for query: {query}")
            if user_id:
                logger.info(f"👤 User ID: {user_id}")
            
            # Step 1: Budget Agent
            logger.info("💰 Calling Budget Agent...")
            budget_response = self.budget_agent.run(query)
            budget_data = json.loads(budget_response)
            logger.info("✅ Budget generated")
            
            # Step 2: Places Agent (includes Wikipedia)
            logger.info("📍 Calling Places Agent...")
            places_response = self.places_agent.run(query)
            places_data = json.loads(places_response)
            logger.info(f"✅ Itinerary generated")
            logger.info(f"🔍 Places data keys: {places_data.keys()}")
            logger.info(f"🔍 Places data.data keys: {places_data.get('data', {}).keys()}")
            logger.info(f"🔍 Destination from places: {places_data.get('data', {}).get('destination')}")
            
            # Step 3: Map Agent
            logger.info("🗺️ Calling Map Agent...")
            # Extract itinerary text from places response
            itinerary_text = places_data.get('display', {}).get('text', '')
            logger.info(f"📝 Itinerary text length: {len(itinerary_text)}")
            logger.info(f"📝 Itinerary preview: {itinerary_text[:200]}")
            
            map_response = self.map_agent.run(itinerary_text)
            map_data = json.loads(map_response)
            logger.info(f"✅ Map data generated with {len(map_data.get('data', {}).get('map', {}).get('locations', []))} locations")
            
            # Combine all results
            result = {
                'success': True,
                'session_id': session_id or 'default',
                'budget': budget_data.get('data', {}).get('budget'),
                'itinerary': places_data.get('data', {}).get('itinerary'),
                'destination': places_data.get('data', {}).get('destination') or budget_data.get('data', {}).get('destination') or 'Unknown',
                'summary': places_data.get('data', {}).get('summary', ''),
                'wikipedia': places_data.get('data', {}).get('wikipedia'),
                'map': map_data.get('data', {}).get('map'),
                'duration_days': places_data.get('data', {}).get('itinerary', {}).get('total_days', 0) or places_data.get('data', {}).get('duration_days', 0),
                'raw_response': self._generate_summary(budget_data, places_data, map_data)
            }
            
            logger.info(f"✅ Trip data compiled - Destination: {result['destination']}, Duration: {result['duration_days']} days")
            
            # Generate PDF and save to database if user_id is provided
            if user_id:
                try:
                    logger.info("💾 Saving trip to database first...")
                    plan_id = self._save_to_database(result, query, session_id, user_id, pdf_url=None)
                    if plan_id:
                        result['plan_id'] = plan_id
                        logger.info(f"✅ Trip saved to database with ID: {plan_id}")
                    
                    # Try to generate PDF (non-blocking - don't fail if this fails)
                    try:
                        logger.info("📄 Generating PDF...")
                        pdf_url = self._generate_and_upload_pdf(result, query)
                        if pdf_url:
                            result['pdf_url'] = pdf_url
                            logger.info(f"✅ PDF uploaded: {pdf_url}")
                            
                            # Update database with PDF URL
                            self._update_pdf_url(plan_id, pdf_url)
                        else:
                            logger.warning("⚠️ PDF generation returned None")
                    except Exception as pdf_error:
                        logger.error(f"⚠️ PDF generation failed (non-critical): {pdf_error}", exc_info=True)
                        # Continue without PDF - not critical
                        
                except Exception as e:
                    logger.error(f"❌ Failed to save to database: {e}", exc_info=True)
            
            logger.info("✅ Trip planning complete!")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error planning trip: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _generate_and_upload_pdf(self, result: Dict, query: str) -> Optional[str]:
        """Generate PDF using filesystem_api and upload to Vercel Blob"""
        try:
            from backend.mcp_tools.filesystem_mcp_service.filesystem_api import FilesystemAPI
            from backend.config import Config
            import requests
            
            logger.info("📄 Generating PDF using FilesystemAPI...")
            logger.info(f"🔍 Result data keys: {result.keys()}")
            logger.info(f"🔍 Destination: {result.get('destination')}")
            logger.info(f"🔍 Duration: {result.get('duration_days')}")
            logger.info(f"🔍 Budget: {result.get('budget')}")
            logger.info(f"🔍 Itinerary days: {len(result.get('itinerary', {}).get('days', []))}")
            logger.info(f"🔍 Map locations: {len(result.get('map', {}).get('locations', []))}")
            
            # Create filesystem API instance (won't actually save to disk)
            fs_api = FilesystemAPI()
            
            # Generate PDF content (bytes)
            destination = result.get('destination', 'Unknown')
            duration = result.get('duration_days', 0)
            
            logger.info(f"🎨 Calling _generate_pdf_content with destination={destination}, duration={duration}")
            pdf_bytes = fs_api._generate_pdf_content(destination, duration, result)
            
            if not pdf_bytes:
                logger.error("❌ PDF generation returned empty content")
                return None
            
            logger.info(f"✅ PDF generated: {len(pdf_bytes)} bytes")
            
            # Upload to Vercel Blob
            blob_token = Config.BLOB_READ_WRITE_TOKEN
            if not blob_token:
                logger.error("❌ BLOB_READ_WRITE_TOKEN not configured")
                return None
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{duration}_day_plan_to_{destination.replace(' ', '_')}_{timestamp}.pdf"
            
            logger.info(f"☁️ Uploading to Vercel Blob: {filename}")
            
            upload_url = f"https://blob.vercel-storage.com/{filename}"
            headers = {
                'Authorization': f'Bearer {blob_token}',
                'x-content-type': 'application/pdf',
            }
            
            response = requests.put(upload_url, data=pdf_bytes, headers=headers)
            
            if response.status_code in [200, 201]:
                blob_data = response.json()
                pdf_url = blob_data.get('url')
                logger.info(f"✅ PDF uploaded successfully: {pdf_url}")
                return pdf_url
            else:
                logger.error(f"❌ Blob upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ PDF generation/upload failed: {e}", exc_info=True)
            return None
    
    def _update_pdf_url(self, plan_id: str, pdf_url: str) -> bool:
        """Update PDF URL in database after generation"""
        try:
            from backend.database.db_manager import TravelBuddyDB
            
            db = TravelBuddyDB()
            
            with db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE travel_plans 
                        SET pdf_url = %s, pdf_filename = %s
                        WHERE id = %s
                    """, (
                        pdf_url,
                        pdf_url.split('/')[-1] if pdf_url else None,
                        plan_id
                    ))
            
            logger.info(f"✅ Updated PDF URL for plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating PDF URL: {e}", exc_info=True)
            return False
    
    def _save_to_database(self, result: Dict, query: str, session_id: str, user_id: int, pdf_url: Optional[str] = None) -> Optional[str]:
        """Save trip plan to database with full budget, itinerary, and map data"""
        try:
            from backend.database.db_manager import TravelBuddyDB
            import uuid
            
            db = TravelBuddyDB()
            
            # Create plan_id
            plan_id = str(uuid.uuid4())
            
            # Extract PDF filename from URL
            pdf_filename = None
            if pdf_url:
                pdf_filename = pdf_url.split('/')[-1]
            
            with db._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert into travel_plans table
                    cursor.execute("""
                        INSERT INTO travel_plans (
                            id, user_id, user_query, session_id, status,
                            destination, duration_days, display_text,
                            pdf_url, pdf_filename, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        plan_id,
                        user_id,
                        query,
                        session_id,
                        'completed',
                        result.get('destination', 'Unknown'),
                        result.get('duration_days', 0),
                        result.get('raw_response', ''),
                        pdf_url,
                        pdf_filename
                    ))
                    
                    # Save budget data
                    budget = result.get('budget', {})
                    if budget:
                        cursor.execute("""
                            INSERT INTO budgets (
                                plan_id, transport, accommodation, food,
                                activities, miscellaneous, total, currency
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            plan_id,
                            budget.get('transport', 0),
                            budget.get('accommodation', 0),
                            budget.get('food', 0),
                            budget.get('activities', 0),
                            budget.get('miscellaneous', 0),
                            budget.get('total', 0),
                            budget.get('currency', 'INR')
                        ))
                    
                    # Save itinerary data
                    itinerary = result.get('itinerary', {})
                    if itinerary and itinerary.get('days'):
                        for day_data in itinerary['days']:
                            cursor.execute("""
                                INSERT INTO itinerary_days (plan_id, day_number, date, total_cost)
                                VALUES (%s, %s, %s, %s) RETURNING id
                            """, (
                                plan_id,
                                day_data.get('day', 1),
                                day_data.get('date'),
                                day_data.get('total_cost')
                            ))
                            day_id = cursor.fetchone()[0]
                            
                            # Save activities for this day
                            for activity in day_data.get('activities', []):
                                location = activity.get('location', {})
                                cursor.execute("""
                                    INSERT INTO activities (
                                        day_id, time, title, description, cost,
                                        duration_minutes, location_name,
                                        location_latitude, location_longitude
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    day_id,
                                    activity.get('time', ''),
                                    activity.get('title', ''),
                                    activity.get('description', ''),
                                    activity.get('cost'),
                                    activity.get('duration_minutes'),
                                    location.get('name', 'Unknown'),
                                    location.get('latitude'),
                                    location.get('longitude')
                                ))
                    
                    # Save map data
                    map_data = result.get('map', {})
                    if map_data and map_data.get('locations'):
                        cursor.execute("""
                            INSERT INTO maps (plan_id, url, total_locations)
                            VALUES (%s, %s, %s) RETURNING id
                        """, (
                            plan_id,
                            map_data.get('url', ''),
                            len(map_data.get('locations', []))
                        ))
                        map_id = cursor.fetchone()[0]
                        
                        # Save map locations
                        for location in map_data.get('locations', []):
                            cursor.execute("""
                                INSERT INTO map_locations (
                                    map_id, name, latitude, longitude,
                                    day, time, description, image_url
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                map_id,
                                location.get('name', ''),
                                location.get('latitude', 0),
                                location.get('longitude', 0),
                                location.get('day', 1),
                                location.get('time', ''),
                                location.get('extract', ''),
                                location.get('image', '')
                            ))
            
            logger.info(f"✅ Saved complete trip data to database: {plan_id}")
            return plan_id
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}", exc_info=True)
            return None
    
    def _generate_summary(self, budget_data: Dict, places_data: Dict, map_data: Dict) -> str:
        """Generate a combined summary from all agents"""
        summary = "# Your Travel Plan\n\n"
        
        # Budget section
        if budget_data.get('display', {}).get('text'):
            summary += "## Budget Breakdown\n\n"
            summary += budget_data['display']['text'] + "\n\n"
        
        # Itinerary section
        if places_data.get('display', {}).get('text'):
            summary += "## Itinerary\n\n"
            summary += places_data['display']['text'] + "\n\n"
        
        # Map section
        if map_data.get('display', {}).get('text'):
            summary += "## Map\n\n"
            summary += map_data['display']['text'] + "\n\n"
        
        return summary


# Global instance
_integrated_planner = None

def get_simple_planner() -> IntegratedTravelPlanner:
    """Get or create singleton planner"""
    global _integrated_planner
    if _integrated_planner is None:
        _integrated_planner = IntegratedTravelPlanner()
    return _integrated_planner
