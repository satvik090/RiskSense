from datetime import datetime
import numpy as np
from sklearn.ensemble import IsolationForest

# 🔥 FIXED IMPORTS (CRITICAL)
from app.core.redis_client import (
    get_cached_transaction,
    set_cached_transaction,
    get_user_profile,
    set_user_profile,
)

# 🔥 Stats tracking
all_scores = []
all_latencies = []

# 🔥 ML model
model = IsolationForest(contamination=0.1)
training_data = []


def record_latency(latency_ms: float):
    all_latencies.append(latency_ms)


def calculate_p95(values):
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = max(0, int(np.ceil(0.95 * len(sorted_values))) - 1)
    return sorted_values[index]


def train_model():
    if len(training_data) > 10:
        X = np.array(training_data)
        model.fit(X)


def extract_features(amount, profile):
    avg = profile["avg_amount"]

    amount_dev = (amount - avg) / (avg + 1)
    velocity = len(profile["hours"]) / 24

    return [amount_dev, velocity]


async def score_transaction_logic(transaction):
    transaction_id = transaction.transaction_id
    user_id = transaction.user_id
    amount = transaction.amount
    category = transaction.category
    timestamp = transaction.timestamp

    if amount > 10000:
        raise ValueError("Simulated scoring failure")

    # 🔥 IDEMPOTENCY (Redis)
    cached = await get_cached_transaction(transaction_id)
    if cached:
        return cached["score"], cached["reasons"]

    score = 0.0
    reasons = []

    # 🔥 SAFE TIMESTAMP
    try:
        hour = datetime.fromisoformat(timestamp).hour
    except:
        hour = 12

    # 🔥 LOAD USER PROFILE
    profile = await get_user_profile(user_id)

    # 🔥 FIRST TRANSACTION
    if not profile:
        profile = {
            "avg_amount": amount,
            "categories": [category],
            "hours": [hour],
        }

        await set_user_profile(user_id, profile)

        result = (0.0, ["First transaction - no baseline"])

        await set_cached_transaction(
            transaction_id,
            {"score": result[0], "reasons": result[1]},
        )

        all_scores.append(result[0])
        return result

    # 🔥 RULE-BASED SCORING
    if amount > 2 * profile["avg_amount"]:
        score += 0.4
        reasons.append("Spending significantly higher than usual")

    if category not in profile["categories"]:
        score += 0.3
        reasons.append("New merchant category")

    avg_hour = sum(profile["hours"]) / len(profile["hours"])
    if abs(hour - avg_hour) > 6:
        score += 0.2
        reasons.append("Transaction at unusual hour")

    # 🔥 FEATURE ENGINEERING
    features = extract_features(amount, profile)
    training_data.append(features)
    train_model()

    # 🔥 ML SCORING
    try:
        pred = model.predict([features])[0]
        if pred == -1:
            score += 0.3
            reasons.append("ML anomaly detected")
    except:
        pass

    # 🔥 UPDATE PROFILE
    profile["avg_amount"] = (profile["avg_amount"] + amount) / 2

    if category not in profile["categories"]:
        profile["categories"].append(category)

    profile["hours"].append(hour)

    # Limit memory
    if len(profile["hours"]) > 50:
        profile["hours"].pop(0)

    # 🔥 SAVE PROFILE
    await set_user_profile(user_id, profile)

    # 🔥 FINAL RESULT
    final_score = min(score, 1.0)
    result = (final_score, reasons)

    # 🔥 CACHE RESULT
    await set_cached_transaction(
        transaction_id,
        {"score": final_score, "reasons": reasons},
    )

    # 🔥 STATS
    all_scores.append(final_score)

    return result


# 🔥 DASHBOARD STATS
def get_stats():
    return {
        "total_transactions": len(all_scores),
        "average_risk": sum(all_scores) / len(all_scores) if all_scores else 0,
        "average_latency_ms": (
            sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
        ),
        "p95_latency_ms": calculate_p95(all_latencies),
    }
