import random
import uuid
from datetime import datetime, timedelta

from locust import HttpUser, between, task


MERCHANTS = [
    "Amazon",
    "Walmart",
    "Uber",
    "Starbucks",
    "Target",
    "BestBuy",
]

CATEGORIES = [
    "shopping",
    "groceries",
    "transport",
    "food",
    "electronics",
]


class TransactionUser(HttpUser):
    wait_time = between(1, 3)

    def _build_payload(self):
        user_id = random.randint(1, 100)
        merchant = random.choice(MERCHANTS)
        category = random.choice(CATEGORIES)
        amount = round(random.uniform(25, 2500), 2)
        timestamp = (
            datetime.utcnow() - timedelta(minutes=random.randint(0, 120))
        ).isoformat()

        return {
            "transaction_id": f"txn_{uuid.uuid4().hex}",
            "user_id": user_id,
            "amount": amount,
            "merchant": merchant,
            "category": category,
            "timestamp": timestamp,
        }

    @task
    def score_transaction(self):
        payload = self._build_payload()
        self.client.post("/transaction/score", json=payload, name="/transaction/score")
