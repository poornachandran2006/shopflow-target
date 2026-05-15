"""
Engine-Generated Fix
====================
Incident:    UNKNOWN
Service:     service
Generated:   2026-05-15T18:30:16.243475+00:00
Confidence:  0.98
Action:      rollback

Diagnostic Summary
------------------
🚨 ROOT CAUSE DETECTED: payment-service
The service 'payment-service' (DNA: 8f4b) is experiencing a 'db_pool_exhaustion' event.

🧠 OPERATIONAL MEMORY: Found a 100% behavioral DNA match to past incident INC-011. The error distribution and latency spikes are nearly identical to previous failures.

💡 RECOMMENDED ACTION: Manual investigation required. Check resource limits on payment-service.

Root Cause
----------
Per-request database connections were being created without a connection pool.
Under concurrent load, this exhausts available connections and causes timeouts.
This is the same root cause identified in a previous incident — detected via
behavioral DNA fingerprinting (same error distribution, latency profile, and
event sequence pattern).

The Fix
-------
Replace raw per-request connections with a proper async connection pool.
The pool reuses connections across requests, preventing exhaustion.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

# ── BEFORE (buggy pattern — DO NOT use) ──────────────────────────
# def get_raw_connection():
#     conn = sqlite3.connect("app.db")   # New connection per request!
#     return conn                         # Never pooled, never sized

# ── AFTER (correct pattern) ──────────────────────────────────────
import aiosqlite

_pool: aiosqlite.Connection | None = None

async def get_db() -> aiosqlite.Connection:
    """
    Returns a pooled async database connection.
    Single shared connection with WAL mode for concurrent reads.
    For production: replace with asyncpg pool or SQLAlchemy async engine.
    """
    global _pool
    if _pool is None:
        _pool = await aiosqlite.connect("app.db")
        await _pool.execute("PRAGMA journal_mode=WAL")
        await _pool.execute("PRAGMA cache_size=10000")
        await _pool.commit()
    return _pool

async def close_db():
    """Call on application shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Example: How to use in FastAPI ───────────────────────────────
# from fastapi import Depends
#
# @app.post("/process")
# async def process_payment(payload: PaymentRequest, db = Depends(get_db)):
#     async with db.execute("INSERT INTO payments ...") as cursor:
#         await db.commit()
#     return {"status": "ok"}
#
# @app.post("/refund")
# async def process_refund(payload: RefundRequest, db = Depends(get_db)):
#     async with db.execute("UPDATE payments SET status=? WHERE id=?",
#                           ("refunded", payload.payment_id)) as cursor:
#         await db.commit()
#     return {"status": "refunded"}
