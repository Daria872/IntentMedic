from pydantic import BaseModel, Field


class InterceptRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Negotiation message to inspect")


class InterceptResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    tactic: str
    tier: int = 1
    action: str
    matched_rules: list[str]
    safe_message: str
    latency_ms: float = Field(..., ge=0.0)
