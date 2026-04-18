import logging
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.transaction import Transaction
from app.models.response import (
    TransactionResponse,
    AnomalyResponse,
    TransactionHistoryResponse,
    DashboardStatsResponse,
)

from app.services.scoring import score_transaction_logic, get_stats
from app.services.anomaly import (
    log_transaction,
    detect_anomalies,
    get_user_transactions,
)
from app.core.redis_client import is_rate_limited

router = APIRouter()
logger = logging.getLogger(__name__)

# 🔥 Simulated event queue (for architecture signal)
event_queue = []


# 🔥 FRAUD SCORING
@router.post("/transaction/score", response_model=TransactionResponse)
async def score_transaction(request: Transaction, http_request: Request):
    if await is_rate_limited(request.user_id):
        logger.info(
            "transaction_score request_id=%s user_id=%s transaction_id=%s latency_ms=0.00",
            getattr(http_request.state, "request_id", "unknown"),
            request.user_id,
            request.transaction_id,
        )
        return JSONResponse(
            status_code=429,
            content={"message": "Rate limit exceeded"},
        )

    start = time.time()

    try:
        score, reasons = await score_transaction_logic(request)
    except Exception:
        logger.info(
            "transaction_score request_id=%s user_id=%s transaction_id=%s latency_ms=0.00",
            getattr(http_request.state, "request_id", "unknown"),
            request.user_id,
            request.transaction_id,
        )
        return {
            "risk_score": 0.1,
            "reasons": ["Fallback scoring due to error"],
            "latency_ms": 0.0,
        }

    # 🔥 Log transaction (for anomaly system)
    log_transaction(request)

    # 🔥 Event queue (simulating async processing)
    event_queue.append({
        "type": "transaction_processed",
        "transaction_id": request.transaction_id,
    })

    latency = (time.time() - start) * 1000

    logger.info(
        "transaction_score request_id=%s user_id=%s transaction_id=%s latency_ms=%.2f",
        getattr(http_request.state, "request_id", "unknown"),
        request.user_id,
        request.transaction_id,
        latency,
    )

    return {
        "risk_score": score,
        "reasons": reasons,
        "latency_ms": latency,
    }


# 🔥 ANOMALY DETECTION
@router.get("/user/anomalies/{user_id}", response_model=AnomalyResponse)
def get_anomalies(user_id: int):
    return {
        "user_id": user_id,
        "anomalies": detect_anomalies(user_id),
    }


# 🔥 TRANSACTION HISTORY
@router.get("/transaction/history/{user_id}", response_model=TransactionHistoryResponse)
def get_transaction_history(user_id: int):
    return {
        "user_id": user_id,
        "transactions": get_user_transactions(user_id),
    }


# 🔥 DASHBOARD STATS
@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def dashboard_stats():
    return get_stats()


# 🔥 INTERNAL: PROCESS EVENT QUEUE (simulation)
@router.get("/internal/process-events")
def process_events():
    processed = []

    while event_queue:
        event = event_queue.pop(0)
        processed.append(event)

    return {"processed_events": processed}
