"""
Budget Agent with Structured Output
Returns both human-readable display and structured JSON data
"""
from backend.agents.common.azure_llm import ask_llm
from backend.models.travel_plan import (
    BudgetBreakdown, BudgetAgentResponse, 
    StructuredResponse, DataType, DisplayFormat, 
    ExecutionMetadata, PlanStatus, Currency
)
import logging
import json
import uuid
import re

logger = logging.getLogger(__name__)


class BudgetAgent:
    """Creates travel budget breakdowns with structured output"""
    
    def run(self, query: str) -> str:
        """
        Main entry point - returns structured response
        
        Args:
            query: User query about budget
            
        Returns:
            JSON string with structured response
        """
        logger.info(f"BudgetAgent processing: {query}")
        
        try:
            # Get LLM response
            display_text = self._get_llm_response(query)
            
            # Parse structured data from response
            budget_data = self._parse_budget_data(display_text, query)
            
            # Create structured response
            structured_response = self._create_structured_response(
                display_text, budget_data
            )
            
            # Return as JSON string
            return structured_response.model_dump_json(indent=2)
            
        except Exception as e:
            logger.error(f"Error in BudgetAgent: {e}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _get_llm_response(self, query: str) -> str:
        """Get human-readable response from LLM with proper Indian budget guidance"""
        
        # Extract destination and duration from query
        duration_match = re.search(r'(\d+)\s*day', query, re.IGNORECASE)
        duration = int(duration_match.group(1)) if duration_match else 3
        
        system = f"""You are an expert Indian travel budget planner.

CRITICAL RULES FOR REALISTIC INDIAN BUDGETS:
1. Use INDIAN RUPEES (₹) ONLY
2. Base calculations on {duration} days
3. Use realistic Indian prices (2024-2026)

REALISTIC PRICE RANGES (per person, per day):

Budget Travel:
- Accommodation: ₹800-1,500/night (budget hotels, hostels)
- Food: ₹500-800/day (local restaurants, street food)
- Local Transport: ₹300-500/day (auto, bus, metro)
- Activities: ₹500-1,000/day (entry fees, basic tours)

Mid-Range Travel:
- Accommodation: ₹2,000-4,000/night (3-star hotels)
- Food: ₹1,000-1,500/day (good restaurants)
- Local Transport: ₹500-800/day (Uber, Ola, private cabs)
- Activities: ₹1,500-3,000/day (guided tours, attractions)

Luxury Travel:
- Accommodation: ₹5,000-15,000/night (4-5 star hotels)
- Food: ₹2,000-4,000/day (fine dining)
- Local Transport: ₹1,000-2,000/day (private car, premium cabs)
- Activities: ₹3,000-8,000/day (premium experiences)

ADDITIONAL COSTS:
- Inter-city Transport: ₹2,000-8,000 (train/flight to destination)
- Miscellaneous: 10-15% of total (emergencies, shopping, tips)

FORMAT YOUR RESPONSE:
1. Start with destination analysis
2. List each category with REALISTIC amounts in ₹
3. Show per-day breakdown
4. Calculate total for {duration} days
5. Add 10% buffer for miscellaneous

EXAMPLE FORMAT:
Transportation: ₹5,000
- Round trip train/flight: ₹3,500
- Local transport ({duration} days × ₹500): ₹{duration * 500}

Accommodation: ₹{duration * 2500}
- Hotel ({duration} nights × ₹2,500): ₹{duration * 2500}

Food: ₹{duration * 1200}
- Meals ({duration} days × ₹1,200): ₹{duration * 1200}

Activities: ₹{duration * 2000}
- Sightseeing and experiences ({duration} days × ₹2,000): ₹{duration * 2000}

Miscellaneous: ₹1,500
- Emergency fund and extras

TOTAL: ₹[SUM OF ALL]
"""
        
        return ask_llm(system, query)
    
    def _parse_budget_data(self, llm_response: str, query: str) -> BudgetBreakdown:
        """
        Parse structured budget data from LLM response
        Uses improved regex to extract numerical values
        """
        logger.info("="*80)
        logger.info("🔍 PARSING BUDGET DATA")
        logger.info(f"📄 LLM Response:\n{llm_response[:500]}")
        logger.info("="*80)
        
        # Always use INR for Indian travel
        currency = Currency.INR
        
        # Improved extraction function
        def extract_amount(patterns: list, text: str, category: str) -> float:
            """Extract amount using multiple patterns"""
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    try:
                        # Extract number, handle commas and currency symbols
                        num_str = match.group(1).replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').replace('$', '').strip()
                        amount = float(num_str)
                        if amount > 0:
                            logger.info(f"✅ {category}: ₹{amount:,.0f} (pattern: {pattern[:30]}...)")
                            return amount
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to parse {category}: {e}")
                        continue
            logger.warning(f"❌ No amount found for {category}")
            return 0.0
        
        # Multiple patterns for each category (more flexible, handle ₹ and Rs.)
        transport = extract_amount([
            r'Transportation[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Transport[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Travel[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'(?:Round trip|Flight|Train)[^\n]*(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Transportation')
        
        accommodation = extract_amount([
            r'Accommodation[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Hotel[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Stay[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Lodging[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Accommodation')
        
        food = extract_amount([
            r'Food[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Meals[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Dining[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Food')
        
        activities = extract_amount([
            r'Activities[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Sightseeing[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Entertainment[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Attractions[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Activities')
        
        miscellaneous = extract_amount([
            r'Miscellaneous[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Misc[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Emergency[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Other[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Miscellaneous')
        
        # Extract total
        total = extract_amount([
            r'TOTAL[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Total[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
            r'Grand Total[:\s]+(?:₹|Rs\.?|INR)?\s*([0-9,]+)',
        ], llm_response, 'Total')
        
        # If total not found or too small, calculate from parts
        calculated_total = transport + accommodation + food + activities + miscellaneous
        if total == 0.0 or total < calculated_total * 0.8:
            total = calculated_total
            logger.info(f"💡 Calculated total from parts: Rs.{total:,.0f}")
        
        # If any category is 0, use reasonable defaults based on total
        if total > 0:
            if transport == 0:
                transport = total * 0.25  # 25% for transport
                logger.info(f"💡 Using default transport: Rs.{transport:,.0f}")
            if accommodation == 0:
                accommodation = total * 0.30  # 30% for accommodation
                logger.info(f"💡 Using default accommodation: Rs.{accommodation:,.0f}")
            if food == 0:
                food = total * 0.20  # 20% for food
                logger.info(f"💡 Using default food: Rs.{food:,.0f}")
            if activities == 0:
                activities = total * 0.20  # 20% for activities
                logger.info(f"💡 Using default activities: Rs.{activities:,.0f}")
            if miscellaneous == 0:
                miscellaneous = total * 0.05  # 5% for misc
                logger.info(f"💡 Using default miscellaneous: Rs.{miscellaneous:,.0f}")
        
        logger.info("="*80)
        logger.info("📊 FINAL BUDGET BREAKDOWN:")
        logger.info(f"   Transportation: Rs.{transport:,.0f}")
        logger.info(f"   Accommodation: Rs.{accommodation:,.0f}")
        logger.info(f"   Food: Rs.{food:,.0f}")
        logger.info(f"   Activities: Rs.{activities:,.0f}")
        logger.info(f"   Miscellaneous: Rs.{miscellaneous:,.0f}")
        logger.info(f"   TOTAL: Rs.{total:,.0f}")
        logger.info("="*80)
        
        return BudgetBreakdown(
            transport=transport,
            accommodation=accommodation,
            food=food,
            activities=activities,
            miscellaneous=miscellaneous,
            total=total,
            currency=currency,
            leftover=None
        )
    
    def _create_structured_response(
        self, 
        display_text: str, 
        budget_data: BudgetBreakdown
    ) -> StructuredResponse:
        """Create complete structured response"""
        
        return StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.SUCCESS,
            data_type=DataType.BUDGET,
            data={
                "budget": budget_data.model_dump()
            },
            display=DisplayFormat(
                text=display_text,
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["BudgetAgent"]
            )
        )
    
    def _create_error_response(self, error_msg: str) -> str:
        """Create error response"""
        response = StructuredResponse(
            request_id=str(uuid.uuid4()),
            status=PlanStatus.ERROR,
            data_type=DataType.BUDGET,
            data={},
            display=DisplayFormat(
                text=f"❌ Error generating budget: {error_msg}",
                format="markdown"
            ),
            metadata=ExecutionMetadata(
                agents_called=["BudgetAgent"]
            ),
            error=error_msg
        )
        return response.model_dump_json(indent=2)
