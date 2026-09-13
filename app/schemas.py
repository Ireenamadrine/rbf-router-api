"""
Pydantic schemas for the RBF-Router API.
Every request and response is validated through these models.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ModelTier(str, Enum):
    """The three model tiers the router can recommend."""
    SMALL = "small"       # e.g., Llama-3.2-1B, Phi-3-mini
    MEDIUM = "medium"     # e.g., Llama-3.1-8B, Mistral-7B
    FRONTIER = "frontier" # e.g., GPT-4o, Claude-3.5-Sonnet


class RouteRequest(BaseModel):
    """Input to POST /route."""
    query: str = Field(..., min_length=1, max_length=4000,
                       description="The user query to route.")
    user_id: Optional[str] = Field(None, max_length=64,
                                   description="Optional user identifier for personalization.")
    allow_escalation: bool = Field(True,
                                   description="If True, caller may re-call with a higher tier on failure.")


class RouteResponse(BaseModel):
    """Output of POST /route."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str = Field(..., description="Unique ID for this routing decision.")
    recommended_tier: ModelTier
    confidence: float = Field(..., ge=0.0, le=1.0)
    expected_cost_savings_pct: float = Field(..., ge=0.0, le=100.0)
    fallback_tier: ModelTier
    alternatives: dict[str, float] = Field(default_factory=dict,
                                           description="Probability of each tier.")
    routed_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """Input to POST /feedback."""
    request_id: str = Field(..., description="The request_id returned by /route.")
    tier_used: ModelTier = Field(..., description="Which tier was actually used.")
    succeeded: bool = Field(..., description="Did the response satisfy the user?")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0,
                                           description="Optional 0-1 quality rating.")


class FeedbackResponse(BaseModel):
    """Output of POST /feedback."""
    acknowledged: bool
    total_feedback: int
    router_updated: bool
    message: str


class HealthResponse(BaseModel):
    """Output of GET /health."""
    status: str
    version: str
    total_routes: int
    total_feedback: int
    router_trained: bool


class StatsResponse(BaseModel):
    """Output of GET /stats."""
    total_routes: int
    total_feedback: int
    accuracy_by_tier: dict[str, float]
    avg_confidence: float
    tier_distribution: dict[str, int]
