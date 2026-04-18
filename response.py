from pydantic import BaseModel, Field
from typing import List


class TransactionResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=1.0, example=0.85)
    reasons: List[str] = Field(
        default_factory=list,
        example=["Spending significantly higher than usual", "ML anomaly detected"]
    )
    latency_ms: float = Field(..., example=45.2)


class AnomalyResponse(BaseModel):
    user_id: int = Field(..., example=1)
    anomalies: List[str] = Field(
        default_factory=list,
        example=["Spending spike detected", "New category detected"]
    )


class TransactionHistoryItem(BaseModel):
    amount: float
    category: str
    timestamp: str


class TransactionHistoryResponse(BaseModel):
    user_id: int
    transactions: List[TransactionHistoryItem]


class DashboardStatsResponse(BaseModel):
    total_transactions: int
    average_risk: float
    average_latency_ms: float
    p95_latency_ms: float
