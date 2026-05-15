"""
event_emitter.py — Bridge between ShopFlow and SENTINEL core engine
===================================================================
Sends structured telemetry events to the SENTINEL ingest API.
Called by main.py on every deploy, error, metric, and remediation.
"""

import httpx
import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

ENGINE_URL = os.getenv("ENGINE_INGEST_URL", "http://localhost:8000/api/v1/ingest")
SERVICE_NAME = os.getenv("SERVICE_NAME", "payment-service")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _emit(events: list[dict]):
    """Fire-and-forget: send events to SENTINEL. Silently fail if engine is down."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(ENGINE_URL, json=events)
            resp.raise_for_status()
            print(f"[EMIT] ✓ Sent {len(events)} event(s) to SENTINEL")
    except Exception as e:
        print(f"[EMIT] ⚠ Could not reach SENTINEL engine: {e}")


def emit_sync(events: list[dict]):
    """Synchronous wrapper — runs emit in a new event loop if needed."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule as background task (inside FastAPI async context)
            asyncio.create_task(_emit(events))
        else:
            loop.run_until_complete(_emit(events))
    except RuntimeError:
        asyncio.run(_emit(events))


# ── Public event helpers ──────────────────────────────────────────────────────

def on_deploy(service: str = SERVICE_NAME, version: str = "v1.2", actor: str = "ci"):
    """Emit a deploy event — called when service starts."""
    emit_sync([{
        "ts": _now(),
        "kind": "deploy",
        "service": service,
        "version": version,
        "actor": actor,
        "msg": f"{service} deployed {version}",
    }])


def on_error(service: str, msg: str, trace_id: str = None, level: str = "error"):
    """Emit an error log event."""
    emit_sync([{
        "ts": _now(),
        "kind": "log",
        "service": service,
        "level": level,
        "msg": msg,
        "trace_id": trace_id or f"trace-{int(datetime.now().timestamp()*1000) % 999999}",
    }])


def on_metric(service: str, name: str, value: float):
    """Emit a metric data point."""
    emit_sync([{
        "ts": _now(),
        "kind": "metric",
        "service": service,
        "name": name,
        "value": value,
    }])


def on_incident(service: str, incident_id: str, trigger: str, description: str):
    """Emit an incident event."""
    emit_sync([{
        "ts": _now(),
        "kind": "incident_signal",  # Changed from "incident" to "incident_signal"
        "service": service,
        "incident_id": incident_id,
        "trigger": trigger,
        "msg": description,
    }])


def on_remediation(incident_id: str, action: str, target: str, outcome: str):
    """Emit a remediation event."""
    emit_sync([{
        "ts": _now(),
        "kind": "remediation",
        "incident_id": incident_id,
        "action": action,
        "target": target,
        "outcome": outcome,
        "service": SERVICE_NAME,
    }])


async def emit_batch_async(events: list[dict]):
    """Async version for use inside FastAPI route handlers."""
    await _emit(events)
