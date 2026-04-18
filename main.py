import logging
import time
import uuid

from fastapi import FastAPI
from app.routes import router
from app.core.redis_client import init_redis
from app.services.scoring import record_latency

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="RiskSense API",
    description="Real-time fraud detection and anomaly system",
    version="1.0.0"
)


@app.middleware("http")
async def track_request_latency(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        record_latency(latency_ms)


# 🔥 Startup event (initialize Redis)
@app.on_event("startup")
async def startup():
    await init_redis()


# 🔥 Root health check
@app.get("/")
def root():
    return {"message": "RiskSense API is running"}


# 🔥 Include routes
app.include_router(router)
