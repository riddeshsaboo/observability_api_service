import json
import logging
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your-exam-login-email@example.com")
START_TIME = time.monotonic()

# This counter is live and is incremented for every HTTP request by middleware.
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests received",
    ["method", "path", "status"],
)

app = FastAPI(title="Observability Service")

log_buffer = deque(maxlen=2000)
log_lock = Lock()


def write_json_log(entry: dict) -> None:
    line = json.dumps(entry, separators=(",", ":"), default=str)
    print(line, flush=True)
    with log_lock:
        log_buffer.append(entry)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        path = request.url.path
        HTTP_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(status_code),
        ).inc()
        entry = {
            "level": "INFO" if status_code < 500 else "ERROR",
            "ts": datetime.fromtimestamp(started, timezone.utc).isoformat(),
            "path": path,
            "request_id": request_id,
            "method": request.method,
            "status": status_code,
            "duration_ms": round((time.time() - started) * 1000, 3),
        }
        write_json_log(entry)


@app.get("/work")
def work(n: int = 1):
    # The assignment asks for K units of work; report the requested non-negative count.
    done = max(0, n)
    # Small deterministic CPU work proportional to n, with a bound to avoid runaway requests.
    accumulator = 0
    for i in range(min(done, 100000)):
        accumulator += i
    return {"email": EMAIL_ADDRESS, "done": done}


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": max(0.0, time.monotonic() - START_TIME)}


@app.get("/logs/tail")
def logs_tail(limit: int = 100):
    limit = max(0, min(limit, 2000))
    with log_lock:
        entries = list(log_buffer)[-limit:] if limit else []
    return entries
