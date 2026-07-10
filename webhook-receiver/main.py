"""
webhook-receiver: intentionally minimal stub service.

Purpose: give Alertmanager's critical/warning receivers a real HTTP target
to POST to, so alert routing can be observed end-to-end (Prometheus fires
-> Alertmanager routes -> webhook receives) without needing a real Slack
or PagerDuty account for the local evidence sprint.

Every POST body is logged to stdout (visible via `docker compose logs -f
webhook-receiver`) and stored in-memory so /received can show the last N
payloads in the browser for screenshotting.
"""

import json
import logging
from collections import deque

from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook-receiver")

app = FastAPI(title="webhook-receiver")

_received = deque(maxlen=50)


@app.post("/critical")
async def critical(request: Request):
    payload = await request.json()
    logger.info("CRITICAL alert received: %s", json.dumps(payload)[:500])
    _received.appendleft({"route": "critical", "payload": payload})
    return {"status": "received"}


@app.post("/warning")
async def warning(request: Request):
    payload = await request.json()
    logger.info("WARNING alert received: %s", json.dumps(payload)[:500])
    _received.appendleft({"route": "warning", "payload": payload})
    return {"status": "received"}


@app.get("/received")
def received():
    return list(_received)


@app.get("/health")
def health():
    return {"status": "ok"}
