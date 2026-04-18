from pydantic import BaseModel, Field
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str = Field(..., example="txn_123")
    user_id: int = Field(..., example=1)
    amount: float = Field(..., gt=0, example=500.0)
    merchant: str = Field(..., example="Amazon")
    category: str = Field(..., example="shopping")
    timestamp: str = Field(..., example="2026-04-18T10:00:00")

    def get_datetime(self) -> datetime:
        try:
            return datetime.fromisoformat(self.timestamp)
        except:
            return datetime.now()