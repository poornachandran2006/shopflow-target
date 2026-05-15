"""
payment-service/main.py — ShopFlow Payment Backend (v1.2 — BUGGY)
==================================================================
This is the CURRENT production version of ShopFlow's payment service.

Bug History:
  v1.0  → process() endpoint: DB connection leak → INC-001 (connection pool exhaustion)
  v1.1  → Bad fix: added try/finally close, but still per-request connections
  v1.2  → New engineer added refund() with EXACT same bug pattern → INC-002

SENTINEL detects:
  DNA(INC-001) ≈ DNA(INC-002) with 0.94 cosine similarity
  Root cause: identical — no connection pooling

Demo trigger: python simulate_load.py --users 10
"""

import asyncio
import time
import uuid
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

from event_emitter import (
    on_deploy, on_error, on_metric, on_incident,
    on_remediation, emit_batch_async
)

load_dotenv()

SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "v1.2")
PORT = int(os.getenv("PORT", "8001"))

# ── Simulated DB Connection Pool (Intentionally Broken) ───────────────────────
# This simulates a connection pool that is NOT being used properly.
# Each request creates a NEW connection. Under load, the pool fills up.

class ConnectionPool:
    """Fake connection pool — tracks open connections globally."""
    _active: list = []
    _total_created: int = 0
    _total_errors: int = 0
    MAX_CONNECTIONS = 3  # Simulated pool limit (deliberately tiny for demo)

    @classmethod
    def acquire(cls, purpose: str = "payment") -> dict:
        cls._total_created += 1
        conn = {
            "id": f"conn-{purpose[:3]}-{cls._total_created:04d}",
            "purpose": purpose,
            "opened_at": time.time(),
        }
        cls._active.append(conn)
        print(f"[DB] ▶ Acquired: {conn['id']} | Active: {len(cls._active)}/{cls.MAX_CONNECTIONS}")
        return conn

    @classmethod
    def release(cls, conn: dict):
        if conn in cls._active:
            cls._active.remove(conn)
            elapsed = (time.time() - conn["opened_at"]) * 1000
            print(f"[DB] ◀ Released: {conn['id']} after {elapsed:.0f}ms")

    @classmethod
    def is_exhausted(cls) -> bool:
        return len(cls._active) >= cls.MAX_CONNECTIONS

    @classmethod
    def stats(cls) -> dict:
        return {
            "active": len(cls._active),
            "max": cls.MAX_CONNECTIONS,
            "total_created": cls._total_created,
            "total_errors": cls._total_errors,
        }


# Track latency measurements for P99 calculation
_latency_samples: list[float] = []
_incident_count: int = 0
_error_count: int = 0
_request_count: int = 0


def record_latency(ms: float):
    global _latency_samples
    _latency_samples.append(ms)
    if len(_latency_samples) > 100:
        _latency_samples = _latency_samples[-100:]


def get_p99() -> float:
    if not _latency_samples:
        return 0.0
    sorted_samples = sorted(_latency_samples)
    idx = int(len(sorted_samples) * 0.99)
    return sorted_samples[min(idx, len(sorted_samples) - 1)]


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — emit deploy event to SENTINEL
    print(f"[BOOT] ShopFlow {SERVICE_NAME} {SERVICE_VERSION} starting on port {PORT}")
    
    # Emit deploy event
    on_deploy(service=SERVICE_NAME, version=SERVICE_VERSION)
    
    # Emit initial metrics
    asyncio.create_task(emit_batch_async([
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "metric",
            "service": SERVICE_NAME,
            "name": "startup",
            "value": 1,
            "version": SERVICE_VERSION,
        }
    ]))

    print(f"[BOOT] ✓ {SERVICE_NAME} ready — SENTINEL notified")
    yield

    # Shutdown
    print(f"[BOOT] {SERVICE_NAME} shutting down")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ShopFlow Payment Service",
    version=SERVICE_VERSION,
    description="ShopFlow payment backend — intentionally broken for SENTINEL demo",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────

class PaymentRequest(BaseModel):
    user_id: str
    amount: float
    cart_items: list[dict] = []
    currency: str = "INR"


class RefundRequest(BaseModel):
    payment_id: str
    user_id: str
    amount: float
    reason: str = "customer_request"


class PaymentResponse(BaseModel):
    status: str
    payment_id: str
    amount: float
    message: str
    latency_ms: float


class RefundResponse(BaseModel):
    status: str
    refund_id: str
    payment_id: str
    amount: float
    message: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "db_pool": ConnectionPool.stats(),
        "latency_p99_ms": round(get_p99(), 2),
        "total_requests": _request_count,
        "total_errors": _error_count,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint."""
    pool = ConnectionPool.stats()
    return {
        "db_active_connections": pool["active"],
        "db_max_connections": pool["max"],
        "db_pool_utilization": pool["active"] / max(pool["max"], 1),
        "latency_p50_ms": round(get_p99() * 0.7, 2),
        "latency_p99_ms": round(get_p99(), 2),
        "error_rate": round(_error_count / max(_request_count, 1), 4),
        "total_requests": _request_count,
        "total_errors": _error_count,
        "incidents": _incident_count,
    }


@app.post("/process", response_model=PaymentResponse)
async def process_payment(payload: PaymentRequest, request: Request):
    """
    Process a checkout payment.
    
    v1.2 BUG: /process uses try/finally (v1.1 fix), so it's mostly OK.
    The NEW bug is in /refund below.
    
    Under COMBINED load (process + refund), pool still exhausts.
    """
    global _request_count, _error_count, _incident_count
    _request_count += 1
    start = time.time()
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"

    # Emit metric to SENTINEL
    asyncio.create_task(emit_batch_async([{
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "metric",
        "service": SERVICE_NAME,
        "name": "payment_request",
        "value": payload.amount,
        "trace_id": trace_id,
    }]))

    conn = None
    try:
        # Check if pool is exhausted
        if ConnectionPool.is_exhausted():
            # Simulate latency spike before failure
            spike_ms = random.uniform(4000, 8500)
            await asyncio.sleep(spike_ms / 1000)
            
            elapsed = (time.time() - start) * 1000
            _error_count += 1
            ConnectionPool._total_errors += 1

            # Emit error to SENTINEL
            error_msg = f"DB pool exhausted: {len(ConnectionPool._active)}/{ConnectionPool.MAX_CONNECTIONS} connections active"
            on_error(SERVICE_NAME, error_msg, trace_id)
            on_metric(SERVICE_NAME, "latency_p99", elapsed)
            on_metric(SERVICE_NAME, "error_rate", _error_count / _request_count)

            # Check if this is incident-worthy (error rate > 20%)
            if _error_count / _request_count > 0.2:
                _incident_count += 1
                inc_id = f"INC-{_incident_count:03d}"
                on_incident(
                    SERVICE_NAME,
                    inc_id,
                    "db_pool_exhaustion",
                    f"Payment service error rate {_error_count / _request_count:.0%} — DB pool exhausted under load"
                )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "payment_service_unavailable",
                    "message": "Payment service temporarily unavailable. Please try again.",
                    "trace_id": trace_id,
                    "latency_ms": round(elapsed, 2),
                }
            )

        # Happy path
        conn = ConnectionPool.acquire("payment")
        await asyncio.sleep(random.uniform(0.08, 0.15))  # Simulate DB write

        elapsed = (time.time() - start) * 1000
        record_latency(elapsed)

        payment_id = f"pay-{uuid.uuid4().hex[:10]}"

        # Emit success metric
        asyncio.create_task(emit_batch_async([{
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": "metric",
            "service": SERVICE_NAME,
            "name": "payment_success",
            "value": elapsed,
            "trace_id": trace_id,
        }]))

        return PaymentResponse(
            status="success",
            payment_id=payment_id,
            amount=payload.amount,
            message="Payment processed successfully",
            latency_ms=round(elapsed, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        _error_count += 1
        on_error(SERVICE_NAME, str(e), trace_id)
        raise HTTPException(status_code=500, detail={"error": str(e), "trace_id": trace_id})
    finally:
        if conn:
            ConnectionPool.release(conn)


@app.post("/refund", response_model=RefundResponse)
async def process_refund(payload: RefundRequest):
    """
    Process a refund.
    
    v1.2 BUG: New engineer added this endpoint copying the BAD v1.0 pattern.
    DB connection is acquired but NEVER RELEASED in error path.
    Under load: refund connections pile up → pool exhaustion → service down.
    
    This is INC-002. SENTINEL detects 94% DNA similarity to INC-001.
    """
    global _request_count, _error_count, _incident_count
    _request_count += 1
    start = time.time()
    trace_id = f"trace-{uuid.uuid4().hex[:8]}"

    # Emit metric
    asyncio.create_task(emit_batch_async([{
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": "metric",
        "service": SERVICE_NAME,
        "name": "refund_request",
        "value": payload.amount,
        "trace_id": trace_id,
    }]))

    # ==================== THE BUG ====================
    # New engineer copied v1.0 pattern — NO try/finally
    conn = ConnectionPool.acquire("refund")  # BUG: acquired but never released in error path

    if ConnectionPool.is_exhausted():
        # Spike latency — same as INC-001 pattern
        spike_ms = random.uniform(5000, 9000)
        await asyncio.sleep(spike_ms / 1000)

        elapsed = (time.time() - start) * 1000
        _error_count += 1
        ConnectionPool._total_errors += 1

        error_msg = f"Refund failed: DB pool exhausted ({len(ConnectionPool._active)}/{ConnectionPool.MAX_CONNECTIONS} active)"
        on_error(SERVICE_NAME, error_msg, trace_id)
        on_metric(SERVICE_NAME, "latency_p99", elapsed)
        on_metric(SERVICE_NAME, "refund_error_rate", _error_count / _request_count)

        if _error_count / _request_count > 0.15:
            _incident_count += 1
            inc_id = f"INC-{_incident_count:03d}"
            on_incident(
                SERVICE_NAME,
                inc_id,
                "db_pool_exhaustion",
                f"Refund service error rate {_error_count / _request_count:.0%} — connection pool exhausted (same pattern as INC-001)"
            )

        # conn is NOT released here — that's the bug
        raise HTTPException(
            status_code=503,
            detail={
                "error": "refund_service_unavailable",
                "message": "Refund service temporarily unavailable.",
                "trace_id": trace_id,
                "latency_ms": round(elapsed, 2),
            }
        )
    # ==================== END BUG ====================

    # Happy path
    await asyncio.sleep(random.uniform(0.1, 0.2))
    ConnectionPool.release(conn)  # Only released on success path — not on error

    elapsed = (time.time() - start) * 1000
    record_latency(elapsed)

    refund_id = f"ref-{uuid.uuid4().hex[:10]}"

    return RefundResponse(
        status="refunded",
        refund_id=refund_id,
        payment_id=payload.payment_id,
        amount=payload.amount,
        message="Refund processed successfully",
    )


@app.post("/reset")
async def reset_state():
    """
    Reset service state — use this between demo runs.
    Simulates a service restart / rollback.
    """
    global _error_count, _request_count, _incident_count, _latency_samples
    ConnectionPool._active.clear()
    ConnectionPool._total_created = 0
    ConnectionPool._total_errors = 0
    _error_count = 0
    _request_count = 0
    _incident_count = 0
    _latency_samples = []

    on_remediation(
        incident_id="INC-002",
        action="rollback",
        target=f"{SERVICE_NAME}@{SERVICE_VERSION}",
        outcome="success",
    )

    return {"status": "reset", "message": "Service state cleared — all connections released"}


@app.get("/")
async def root():
    return {
        "service": "ShopFlow Payment API",
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "metrics": "GET /metrics",
            "process": "POST /process",
            "refund": "POST /refund",
            "reset": "POST /reset",
        },
    }


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info",
    )
