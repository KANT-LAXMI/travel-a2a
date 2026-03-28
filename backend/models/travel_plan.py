"""
Pydantic models for structured travel plan data.
Used by all agents to ensure consistent output format.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"


class PlanStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class DataType(str, Enum):
    TRAVEL_PLAN = "travel_plan"
    BUDGET = "budget"
    ITINERARY = "itinerary"
    MAP = "map"
    KNOWLEDGE_ANSWER = "knowledge_answer"


# Budget Models
class BudgetBreakdown(BaseModel):
    transport: float = Field(..., description="Transportation costs")
    accommodation: float = Field(..., description="Accommodation costs")
    food: float = Field(..., description="Food and dining costs")
    activities: float = Field(..., description="Activities and entertainment costs")
    miscellaneous: float = Field(..., description="Miscellaneous expenses")
    total: float = Field(..., description="Total budget")
    currency: Currency = Field(default=Currency.INR)
    leftover: Optional[float] = Field(None, description="Remaining budget")


# Itinerary Models
class Location(BaseModel):
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class Activity(BaseModel):
    time: str = Field(..., description="Activity time (e.g., '9:00 AM')")
    title: str = Field(..., description="Activity name")
    location: Location
    description: Optional[str] = None
    cost: Optional[float] = None
    duration_minutes: Optional[int] = None
    tips: Optional[List[str]] = None


class ItineraryDay(BaseModel):
    day: int = Field(..., description="Day number (1-indexed)")
    date: Optional[str] = None
    activities: List[Activity] = Field(default_factory=list)
    total_cost: Optional[float] = None


class Itinerary(BaseModel):
    days: List[ItineraryDay]
    total_days: int
    tips: Optional[List[str]] = None


# Map Models
class MapLocation(BaseModel):
    name: str
    latitude: float
    longitude: float
    day: int
    time: str
    description: Optional[str] = None
    duration: Optional[int] = Field(None, description="Duration in minutes")
    image: Optional[str] = Field(None, description="Wikipedia image URL")
    extract: Optional[str] = Field(None, description="Wikipedia extract/description")


class MapData(BaseModel):
    url: str = Field(..., description="Path to generated HTML map file")
    locations: List[MapLocation]
    total_locations: int


# Complete Travel Plan
class TravelPlanData(BaseModel):
    destination: str
    duration_days: int
    budget: BudgetBreakdown
    itinerary: Itinerary
    map: Optional[MapData] = None


# Metadata
class ExecutionMetadata(BaseModel):
    agents_called: List[str] = Field(default_factory=list)
    execution_time_ms: Optional[int] = None
    llm_tokens_used: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Display Format
class DisplayFormat(BaseModel):
    text: str = Field(..., description="Human-readable markdown text")
    format: str = Field(default="markdown")


# Main Response Structure
class StructuredResponse(BaseModel):
    version: str = Field(default="1.0")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: PlanStatus = Field(default=PlanStatus.SUCCESS)
    
    data: Dict[str, Any] = Field(..., description="Structured data payload")
    data_type: DataType = Field(..., description="Type of data in response")
    
    metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    display: DisplayFormat
    
    error: Optional[str] = None


# Agent-specific response models
class BudgetAgentResponse(BaseModel):
    budget: BudgetBreakdown
    recommendations: Optional[List[str]] = None


class PlacesAgentResponse(BaseModel):
    itinerary: Itinerary
    destination: str


class MapAgentResponse(BaseModel):
    map: MapData


class RAGAgentResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
