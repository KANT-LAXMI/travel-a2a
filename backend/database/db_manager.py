"""
Database Manager for Travel Buddy
Handles all PostgreSQL operations for storing structured travel plans
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
from backend.models.travel_plan import StructuredResponse
from backend.config import Config

logger = logging.getLogger(__name__)


class TravelBuddyDB:
    """PostgreSQL database manager for travel plans"""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or Config.DATABASE_URL
        self._ensure_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
            logger.info(f"✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            raise
    
    def save_travel_plan(self, response: StructuredResponse, user_query: str, session_id: Optional[str] = None) -> str:
        """Save complete travel plan to database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    plan_id = response.request_id
                    
                    cursor.execute("""
                        INSERT INTO travel_plans (
                            id, user_query, session_id, status, version,
                            destination, duration_days,
                            execution_time_ms, llm_tokens_used, agents_called,
                            display_text, display_format, error_message
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        plan_id, user_query, session_id,
                        response.status.value, response.version,
                        response.data.get('destination'),
                        response.data.get('duration_days'),
                        response.metadata.execution_time_ms,
                        response.metadata.llm_tokens_used,
                        json.dumps(response.metadata.agents_called),
                        response.display.text, response.display.format,
                        response.error
                    ))
                    
                    if 'budget' in response.data:
                        self._save_budget(cursor, plan_id, response.data['budget'])
                    if 'itinerary' in response.data:
                        self._save_itinerary(cursor, plan_id, response.data['itinerary'])
                    if 'map' in response.data:
                        self._save_map(cursor, plan_id, response.data['map'], response.data.get('html'))
                    logger.info(f"✅ Saved travel plan: {plan_id}")
                    return plan_id
        except Exception as e:
            logger.error(f"❌ Error saving travel plan: {e}", exc_info=True)
            raise
    
    def _save_budget(self, cursor, plan_id: str, budget_data: Dict):
        """Save budget breakdown"""
        cursor.execute("""
            INSERT INTO budgets (
                plan_id, transport, accommodation, food,
                activities, miscellaneous, total, leftover, currency
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            plan_id,
            budget_data.get('transport', 0),
            budget_data.get('accommodation', 0),
            budget_data.get('food', 0),
            budget_data.get('activities', 0),
            budget_data.get('miscellaneous', 0),
            budget_data.get('total', 0),
            budget_data.get('leftover'),
            budget_data.get('currency', 'INR')
        ))
    
    def _save_itinerary(self, cursor, plan_id: str, itinerary_data: Dict):
        """Save itinerary with days and activities"""
        for day_data in itinerary_data.get('days', []):
            cursor.execute("""
                INSERT INTO itinerary_days (plan_id, day_number, date, total_cost)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (plan_id, day_data['day'], day_data.get('date'), day_data.get('total_cost')))
            day_id = cursor.fetchone()[0]
            
            for activity_data in day_data.get('activities', []):
                if not activity_data:
                    continue
                    
                location = activity_data.get('location', {})
                cursor.execute("""
                    INSERT INTO activities (
                        day_id, time, title, description, cost, duration_minutes,
                        location_name, location_latitude, location_longitude, location_address
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    day_id, activity_data.get('time'), activity_data.get('title'),
                    activity_data.get('description'), activity_data.get('cost'),
                    activity_data.get('duration_minutes'), location.get('name', 'Unknown'),
                    location.get('latitude'), location.get('longitude'), location.get('address')
                ))
                activity_id = cursor.fetchone()[0]
                
                tips = activity_data.get('tips', [])
                if tips:
                    for tip in tips:
                        cursor.execute("INSERT INTO activity_tips (activity_id, tip) VALUES (%s, %s)", (activity_id, tip))
    
    def _save_map(self, cursor, plan_id: str, map_data: Dict, html_content: Optional[str] = None):
        """Save map data and locations"""
        if not map_data:
            logger.warning(f"⚠️ No map data to save for plan {plan_id}")
            return
        
        cursor.execute("""
            INSERT INTO maps (plan_id, url, total_locations, html_content)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (plan_id, map_data.get('url'), map_data.get('total_locations', 0), html_content))
        map_id = cursor.fetchone()[0]
        
        for location in map_data.get('locations', []):
            cursor.execute("""
                INSERT INTO map_locations (map_id, name, latitude, longitude, day, time, description, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                map_id, location.get('name'), location.get('latitude'),
                location.get('longitude'), location.get('day'), location.get('time'),
                location.get('description'), location.get('image')
            ))
    
    def save_knowledge_query(self, response: StructuredResponse, question: str, session_id: Optional[str] = None) -> str:
        """Save RAG knowledge query"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    query_id = response.request_id
                    data = response.data
                    
                    cursor.execute("""
                        INSERT INTO knowledge_queries (
                            id, question, answer, confidence, session_id, execution_time_ms, display_text
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        query_id, question, data.get('answer', ''), data.get('confidence'),
                        session_id, response.metadata.execution_time_ms, response.display.text
                    ))
                    
                    for source in data.get('sources', []):
                        parts = source.split('(Page')
                        source_name = parts[0].strip()
                        page_number = parts[1].strip(' )') if len(parts) > 1 else None
                        cursor.execute("INSERT INTO knowledge_sources (query_id, source_name, page_number) VALUES (%s, %s, %s)",
                                     (query_id, source_name, page_number))
                    
                    conn.commit()
                    logger.info(f"✅ Saved knowledge query: {query_id}")
                    return query_id
        except Exception as e:
            logger.error(f"❌ Error saving knowledge query: {e}", exc_info=True)
            raise
    
    def get_travel_plan(self, plan_id: str) -> Optional[Dict]:
        """Retrieve complete travel plan by ID"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM travel_plans WHERE id = %s", (plan_id,))
                plan_row = cursor.fetchone()
                
                if not plan_row:
                    return None
                
                plan = dict(plan_row)
                
                cursor.execute("SELECT * FROM budgets WHERE plan_id = %s", (plan_id,))
                budget_row = cursor.fetchone()
                if budget_row:
                    plan['budget'] = dict(budget_row)
                
                cursor.execute("SELECT * FROM itinerary_days WHERE plan_id = %s ORDER BY day_number", (plan_id,))
                days = []
                for day_row in cursor.fetchall():
                    day = dict(day_row)
                    cursor.execute("SELECT * FROM activities WHERE day_id = %s ORDER BY time", (day['id'],))
                    day['activities'] = [dict(row) for row in cursor.fetchall()]
                    days.append(day)
                
                plan['itinerary_days'] = days
                
                cursor.execute("SELECT * FROM maps WHERE plan_id = %s", (plan_id,))
                map_row = cursor.fetchone()
                if map_row:
                    map_data = dict(map_row)
                    cursor.execute("SELECT * FROM map_locations WHERE map_id = %s ORDER BY day, time", (map_data['id'],))
                    map_data['locations'] = [dict(row) for row in cursor.fetchall()]
                    plan['map'] = map_data
                
                return plan
    
    def search_plans(self, destination: Optional[str] = None, session_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search travel plans with filters"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM v_complete_travel_plans WHERE 1=1"
                params = []
                
                if destination:
                    query += " AND destination LIKE %s"
                    params.append(f"%{destination}%")
                
                if session_id:
                    query += " AND session_id = %s"
                    params.append(session_id)
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as count FROM travel_plans")
                stats['total_plans'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM knowledge_queries")
                stats['total_knowledge_queries'] = cursor.fetchone()['count']
                
                cursor.execute("""
                    SELECT destination, COUNT(*) as count
                    FROM travel_plans
                    WHERE destination IS NOT NULL
                    GROUP BY destination
                    ORDER BY count DESC
                    LIMIT 5
                """)
                stats['popular_destinations'] = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute("SELECT AVG(total) as avg_budget FROM budgets")
                result = cursor.fetchone()
                avg_budget = result['avg_budget'] if result else None
                stats['average_budget'] = round(float(avg_budget), 2) if avg_budget else 0
                
                return stats
    
    def save_conversation_message(self, session_id: str, role: str, content: str, plan_id: Optional[str] = None) -> int:
        """Save a conversation message"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COALESCE(MAX(message_number), 0) + 1
                        FROM conversation_history WHERE session_id = %s
                    """, (session_id,))
                    message_number = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO conversation_history (session_id, message_number, role, content, plan_id)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (session_id, message_number, role, content, plan_id))
                    
                    message_id = cursor.fetchone()[0]
                    conn.commit()
                    logger.info(f"💬 Saved {role} message #{message_number} for session {session_id}")
                    return message_id
        except Exception as e:
            logger.error(f"❌ Error saving conversation message: {e}", exc_info=True)
            raise
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a session"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM conversation_history
                    WHERE session_id = %s
                    ORDER BY message_number DESC LIMIT %s
                """, (session_id, limit))
                
                messages = [dict(row) for row in cursor.fetchall()]
                messages.reverse()
                return messages
    
    def get_last_plan(self, session_id: str) -> Optional[Dict]:
        """Get the most recent travel plan for a session"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT plan_id FROM conversation_history
                    WHERE session_id = %s AND plan_id IS NOT NULL
                    ORDER BY message_number DESC LIMIT 1
                """, (session_id,))
                
                row = cursor.fetchone()
                if not row or not row['plan_id']:
                    return None
                
                return self.get_travel_plan(row['plan_id'])
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get complete context for a session"""
        return {
            'conversation_history': self.get_conversation_history(session_id, limit=5),
            'last_plan': self.get_last_plan(session_id),
            'session_id': session_id
        }
