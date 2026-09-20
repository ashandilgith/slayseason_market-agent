from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """The memory graph for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    tenant_id: str  # Enforces FR-401 tenant isolation

class JarvisResponse(BaseModel):
    """Strict FR-501 Data Contract ensuring Jarvis never invents metrics."""
    date_range: str = Field(description="The date range queried, e.g., Last 30 days")
    source_systems: list[str] = Field(description="Data sources used, e.g., ['Shopify', 'Meta']")
    confidence: str = Field(description="High, Medium, or Low")
    known_unknowns: list[str] = Field(description="Explicitly state any missing data")
    answer: str = Field(description="The direct answer regarding profit, MER, or revenue")
    recommended_action: Optional[str] = Field(description="A brief next step based on the data")