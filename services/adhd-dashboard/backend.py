import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import APIKeyHeader
import uvicorn
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.shared.brand_voice import StatusChip, brand_log, brand_error, brand_payload, voice_header
from task_recommender import TaskRecommender

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional in local dev
    CONTENT_TYPE_LATEST = "text/plain"
    PROMETHEUS_AVAILABLE = False


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_NAME = "adhd-dashboard"
API_KEY = os.getenv("DASHBOARD_API_KEY") or None
ADHD_ENGINE_API_KEY = os.getenv("ADHD_ENGINE_API_KEY") or None
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
ACTIVITY_CAPTURE_URL = os.getenv("ACTIVITY_CAPTURE_URL", "http://localhost:8096")
ADHD_ENGINE_URL = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095")
DASHBOARD_USER_ID = os.getenv("DASHBOARD_USER_ID", "default")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8097,http://127.0.0.1:8097",
).split(",")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

REQUEST_COUNT = Counter(
    "adhd_dashboard_requests_total",
    "Dashboard request count",
    ["endpoint", "status"],
) if PROMETHEUS_AVAILABLE else None
REQUEST_LATENCY = Histogram(
    "adhd_dashboard_request_latency_seconds",
    "Dashboard request latency",
    ["endpoint"],
) if PROMETHEUS_AVAILABLE else None
COGNITIVE_LOAD_GAUGE = Gauge(
    "adhd_dashboard_cognitive_load",
    "Latest cognitive load rendered by the dashboard",
    ["user_id"],
) if PROMETHEUS_AVAILABLE else None
FOCUS_DURATION_GAUGE = Gauge(
    "adhd_dashboard_focus_duration_minutes",
    "Latest focus duration rendered by the dashboard",
    ["user_id"],
) if PROMETHEUS_AVAILABLE else None
HYPERFOCUS_ALERTS = Counter(
    "adhd_dashboard_hyperfocus_alerts_total",
    "Hyperfocus alerts surfaced on the dashboard",
    ["user_id"],
) if PROMETHEUS_AVAILABLE else None
NOTIFICATIONS_TOTAL = Counter(
    "adhd_dashboard_notifications_total",
    "Dashboard notifications by type",
    ["notification_type"],
) if PROMETHEUS_AVAILABLE else None


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Any):
        if isinstance(message, str):
            payload = message
        else:
            payload = json.dumps(message)

        stale_connections: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)


manager = ConnectionManager()


def _metric_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if ADHD_ENGINE_API_KEY:
        headers["X-API-Key"] = ADHD_ENGINE_API_KEY
    return headers


def _task_recommender() -> TaskRecommender:
    return TaskRecommender(
        adhd_engine_url=ADHD_ENGINE_URL,
        user_id=DASHBOARD_USER_ID,
        api_key=ADHD_ENGINE_API_KEY,
    )


async def verify_api_key(api_key: str = Security(api_key_header)):
    if API_KEY is None:
        return None
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail=brand_error("Invalid API key"))
    return api_key


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
) -> Dict[str, Any]:
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            text = await response.text()
            return {"error": f"upstream_status={response.status}", "detail": text[:200]}
    except Exception as exc:
        logger.error(brand_log("Upstream GET failed for %s: %s", url, exc, chip=StatusChip.BLOCKER))
        return {"error": str(exc)}


def _normalize_stream_type(event_type: str) -> str:
    aliases = {
        "progress_updated": "progress.updated",
        "task.progress.updated": "progress.updated",
        "task_progress_updated": "progress.updated",
        "decision_logged": "decision.logged",
        "break_taken": "break.taken",
        "session_started": "session.started",
    }
    return aliases.get((event_type or "").strip(), (event_type or "").strip())


def _read_stream_event(fields: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    event_type = fields.get("event_type") or fields.get("type") or ""
    data = fields.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {"raw": data}
    return _normalize_stream_type(event_type), data


def _notification_message(event_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if event_type == "decision.logged":
        summary = data.get("summary") or data.get("decision", {}).get("summary") or "Decision logged"
        return {
            "type": "dashboard_notification",
            "notification_type": "decision",
            "message": summary,
            "timestamp": datetime.utcnow().isoformat(),
        }
    if event_type == "progress.updated":
        status = data.get("status") or data.get("to_status") or "updated"
        task_id = data.get("task_id") or data.get("description") or "task"
        return {
            "type": "dashboard_notification",
            "notification_type": "progress",
            "message": f"{task_id} -> {status}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    if event_type in {"hyperfocus_detected", "hyperfocus_warning_90", "hyperfocus_warning_120"}:
        minutes = data.get("focus_duration_minutes") or data.get("duration_minutes")
        suffix = f" after {minutes} minutes" if minutes is not None else ""
        return {
            "type": "dashboard_notification",
            "notification_type": "hyperfocus",
            "message": f"Hyperfocus protection triggered{suffix}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    if event_type == "break.taken":
        minutes = data.get("duration_minutes")
        message = "Break logged"
        if minutes is not None:
            message = f"Break logged for {minutes} minutes"
        return {
            "type": "dashboard_notification",
            "notification_type": "break",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    if event_type == "session.started":
        task_id = data.get("task_id") or data.get("session_id") or "focus session"
        return {
            "type": "dashboard_notification",
            "notification_type": "session",
            "message": f"Started {task_id}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    return None


def _record_state_metrics(message: Dict[str, Any]) -> None:
    if not PROMETHEUS_AVAILABLE:
        return

    if message.get("type") != "state_update":
        return

    data = message.get("data", {})
    user_id = DASHBOARD_USER_ID
    COGNITIVE_LOAD_GAUGE.labels(user_id=user_id).set(float(data.get("cognitive_load", 0.0)))
    FOCUS_DURATION_GAUGE.labels(user_id=user_id).set(float(data.get("session_duration_minutes", 0.0)))


async def redis_pubsub_reader():
    """Broadcast ADHD state changes produced by the engine."""
    logger.info(brand_log("Starting Redis Pub/Sub reader for ADHD state changes", chip=StatusChip.LIVE))
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe("adhd:state_changes:*")

    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue

            data = message["data"]
            if isinstance(data, str):
                try:
                    decoded = json.loads(data)
                except json.JSONDecodeError:
                    decoded = {"type": "raw_state_update", "raw": data}
            else:
                decoded = data

            _record_state_metrics(decoded)
            await manager.broadcast(decoded)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.error(brand_log("Redis Pub/Sub error: %s", exc, chip=StatusChip.BLOCKER))
    finally:
        await pubsub.unpsubscribe("adhd:state_changes:*")
        await pubsub.close()


async def redis_stream_reader(stream: str, consumer_group: str, consumer_name: str):
    """Read dashboard-worthy notifications from Redis streams."""
    try:
        await redis_client.xgroup_create(stream, consumer_group, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise

    while True:
        try:
            messages = await redis_client.xreadgroup(
                consumer_group,
                consumer_name,
                {stream: ">"},
                count=20,
                block=1000,
            )
            if not messages:
                continue

            for _stream_name, entries in messages:
                for message_id, fields in entries:
                    event_type, data = _read_stream_event(fields)
                    payload = _notification_message(event_type, data)
                    if payload:
                        if PROMETHEUS_AVAILABLE:
                            NOTIFICATIONS_TOTAL.labels(notification_type=payload["notification_type"]).inc()
                        if event_type in {"hyperfocus_detected", "hyperfocus_warning_90", "hyperfocus_warning_120"}:
                            HYPERFOCUS_ALERTS.labels(user_id=DASHBOARD_USER_ID).inc()
                        await manager.broadcast(payload)

                    await redis_client.xack(stream, consumer_group, message_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(brand_log("Redis stream reader failed for %s: %s", stream, exc, chip=StatusChip.BLOCKER))
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    tasks = [
        asyncio.create_task(redis_pubsub_reader(), name="dashboard_state_reader"),
        asyncio.create_task(
            redis_stream_reader(
                "dopemux:adhd-findings",
                "adhd-dashboard-findings",
                f"{SERVICE_NAME}-findings",
            ),
            name="dashboard_findings_reader",
        ),
        asyncio.create_task(
            redis_stream_reader(
                "dopemux:events",
                "adhd-dashboard-events",
                f"{SERVICE_NAME}-events",
            ),
            name="dashboard_events_reader",
        ),
    ]

    yield

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await redis_client.close()


app = FastAPI(title="ADHD Dashboard API", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


def _record_request(endpoint: str, status: str, start_time: float) -> None:
    if PROMETHEUS_AVAILABLE:
        REQUEST_COUNT.labels(endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)


@app.get("/")
async def root():
    return {
        "service": "ADHD Dashboard Backend",
        "version": "1.1.0",
        "status": "operational",
        "ui_expected_at": "http://localhost:5173",
        "endpoints": [
            "/api/metrics",
            "/api/adhd-state",
            "/api/cognitive-load",
            "/api/task-recommendations",
            "/api/sessions/today",
            "/metrics",
            "/health",
        ],
        **brand_payload("ADHD Dashboard Backend is operational."),
    }


@app.websocket("/ws/state")
async def websocket_endpoint(websocket: WebSocket, user_id: str = DASHBOARD_USER_ID):
    del user_id
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/metrics")
async def get_metrics(api_key: str = Security(verify_api_key)):
    del api_key
    start_time = time.time()
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = await _get_json(session, f"{ACTIVITY_CAPTURE_URL}/metrics")
        _record_request("/api/metrics", "success", start_time)
        return payload
    except Exception as exc:
        _record_request("/api/metrics", "error", start_time)
        raise HTTPException(status_code=502, detail=brand_error(str(exc))) from exc


@app.get("/api/task-recommendations")
async def get_task_recommendations(api_key: str = Security(verify_api_key)):
    del api_key
    start_time = time.time()
    try:
        payload = await _task_recommender().get_current_recommendation()
        _record_request("/api/task-recommendations", "success", start_time)
        return payload
    except Exception as exc:
        _record_request("/api/task-recommendations", "error", start_time)
        raise HTTPException(status_code=502, detail=brand_error(str(exc))) from exc


@app.get("/api/cognitive-load")
async def get_dashboard_cognitive_load(api_key: str = Security(verify_api_key)):
    del api_key
    start_time = time.time()
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(headers=_metric_headers(), timeout=timeout) as session:
        payload = await _get_json(session, f"{ADHD_ENGINE_URL}/api/v1/cognitive-load/{DASHBOARD_USER_ID}")
    _record_request("/api/cognitive-load", "success" if "error" not in payload else "error", start_time)
    return payload


@app.get("/api/adhd-state")
async def get_adhd_state(api_key: str = Security(verify_api_key)):
    del api_key
    start_time = time.time()
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(headers=_metric_headers(), timeout=timeout) as session:
        health, energy, attention, cognitive_load = await asyncio.gather(
            _get_json(session, f"{ADHD_ENGINE_URL}/health"),
            _get_json(session, f"{ADHD_ENGINE_URL}/api/v1/energy-level/{DASHBOARD_USER_ID}"),
            _get_json(session, f"{ADHD_ENGINE_URL}/api/v1/attention-state/{DASHBOARD_USER_ID}"),
            _get_json(session, f"{ADHD_ENGINE_URL}/api/v1/cognitive-load/{DASHBOARD_USER_ID}"),
        )

    recommendation_payload = await _task_recommender().get_current_recommendation()
    recommendation = recommendation_payload.get("recommendation", {})
    suggestion = recommendation.get("suggestion") or recommendation_payload.get("error")

    status = "success"
    for payload in (health, energy, attention, cognitive_load, recommendation_payload):
        if isinstance(payload, dict) and payload.get("error"):
            status = "partial"
            break

    _record_request("/api/adhd-state", status, start_time)
    return {
        "health": health,
        "energy": energy,
        "attention": attention,
        "cognitive_load": cognitive_load,
        "recommendation": suggestion or "No active recommendation",
        "task_recommendations": recommendation_payload,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/sessions/today")
async def get_today_sessions(api_key: str = Security(verify_api_key)):
    del api_key
    metrics = await get_metrics()
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sessions_tracked": metrics.get("sessions_tracked", 0),
        "activities_logged": metrics.get("activities_logged", 0),
        "session_active": metrics.get("session_active", False),
        "current_duration": metrics.get("current_session_duration_minutes", 0),
        "workspace_switches": metrics.get("workspace_switches", 0),
    }


@app.get("/metrics")
async def metrics():
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(status_code=503, detail=brand_error("prometheus_client not installed"))
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "redis_url": REDIS_URL,
        "activity_capture_url": ACTIVITY_CAPTURE_URL,
        "adhd_engine_url": ADHD_ENGINE_URL,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8097)
