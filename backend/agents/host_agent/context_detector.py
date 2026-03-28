"""
Context Detector - Identifies follow-up queries and modification types
"""
import re
from typing import Optional, Dict


class ContextDetector:
    """Detects if a query is a follow-up and what type of modification is requested"""
    
    # Patterns for follow-up detection
    FOLLOWUP_PATTERNS = [
        # Budget modifications
        r'\b(make it |more |less )(cheap|expensive|affordable)',
        r'\b(reduce|increase|lower|raise) (the )?(budget|cost|price)',
        r'\bunder \d+',
        
        # Activity modifications
        r'\b(add|include|also) .*(activity|activities|sport|adventure)',
        r'\b(remove|skip|exclude|without)',
        
        # Duration changes
        r'\b(change|make it|extend|reduce) (to )?\d+ day',
        r'\b(longer|shorter) trip',
        
        # Destination changes
        r'\binstead of',
        r'\bchange (to|destination)',
        
        # General modifications
        r'\b(modify|update|adjust|alter)',
        r'\b(also|additionally|plus)',
        
        # Pronouns indicating context
        r'\b(it|this|that|the plan|the trip)',
    ]
    
    # Modification type patterns
    BUDGET_PATTERNS = [
        r'cheap|expensive|budget|cost|price|afford',
        r'reduce|increase|lower|raise|save|spend',
    ]
    
    ACTIVITY_PATTERNS = [
        r'add|include|activity|activities|sport|adventure',
        r'water sport|trekking|museum|temple|beach',
    ]
    
    DURATION_PATTERNS = [
        r'\d+ day|longer|shorter|extend|reduce',
        r'weekend|week',
    ]
    
    DESTINATION_PATTERNS = [
        r'instead|change destination|go to',
        r'different place|another city',
    ]
    
    def is_followup(self, query: str) -> bool:
        """
        Check if query is a follow-up to previous conversation
        
        Args:
            query: User query
            
        Returns:
            True if follow-up, False if new query
        """
        query_lower = query.lower()
        
        # Check against all follow-up patterns
        for pattern in self.FOLLOWUP_PATTERNS:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def get_modification_type(self, query: str) -> Optional[str]:
        """
        Identify what type of modification is requested
        
        Args:
            query: User query
            
        Returns:
            'budget' | 'activity' | 'duration' | 'destination' | None
        """
        query_lower = query.lower()
        
        # Check budget patterns
        for pattern in self.BUDGET_PATTERNS:
            if re.search(pattern, query_lower):
                return 'budget'
        
        # Check activity patterns
        for pattern in self.ACTIVITY_PATTERNS:
            if re.search(pattern, query_lower):
                return 'activity'
        
        # Check duration patterns
        for pattern in self.DURATION_PATTERNS:
            if re.search(pattern, query_lower):
                return 'duration'
        
        # Check destination patterns
        for pattern in self.DESTINATION_PATTERNS:
            if re.search(pattern, query_lower):
                return 'destination'
        
        return None
    
    def extract_budget_intent(self, query: str) -> Dict[str, any]:
        """
        Extract budget modification details
        
        Returns:
            {'action': 'reduce'|'increase', 'amount': int|None}
        """
        query_lower = query.lower()
        
        # Detect action
        action = 'reduce'
        if any(word in query_lower for word in ['more', 'expensive', 'increase', 'raise', 'luxury']):
            action = 'increase'
        
        # Extract amount if specified
        amount_match = re.search(r'under (\d+)', query_lower)
        amount = int(amount_match.group(1)) if amount_match else None
        
        return {
            'action': action,
            'amount': amount
        }
    
    def extract_activities(self, query: str) -> Dict[str, any]:
        """
        Extract activity modification details
        
        Returns:
            {'action': 'add'|'remove', 'activities': [str]}
        """
        query_lower = query.lower()
        
        # Detect action
        action = 'add'
        if any(word in query_lower for word in ['remove', 'skip', 'exclude', 'without']):
            action = 'remove'
        
        # Extract activity keywords
        activities = []
        activity_keywords = [
            'water sport', 'trekking', 'museum', 'temple', 'beach',
            'shopping', 'nightlife', 'adventure', 'sightseeing'
        ]
        
        for keyword in activity_keywords:
            if keyword in query_lower:
                activities.append(keyword)
        
        return {
            'action': action,
            'activities': activities
        }
    
    def extract_duration(self, query: str) -> Optional[int]:
        """
        Extract new duration in days
        
        Returns:
            Number of days or None
        """
        # Look for patterns like "3 days", "5 day"
        match = re.search(r'(\d+)\s*days?', query.lower())
        if match:
            return int(match.group(1))
        
        return None
