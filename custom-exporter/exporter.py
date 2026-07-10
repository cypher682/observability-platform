"""
custom-exporter: hand-written Prometheus exporter demonstrating understanding
of the Prometheus data model (counter/gauge/histogram) rather than relying
on an off-the-shelf exporter.

Simulates reading business metrics from a Postgres-backed application
(active users, queued jobs, webhook delivery outcomes) and exposes them
on /metrics in Prometheus text exposition format.

Run:
    uvicorn exporter:app --host 0.0.0.0 --port 9200
"""

import random
import time
import threading

from fastapi import FastAPI, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = FastAPI(title="custom-exporter")

# --- Metric definitions ------------------------------------------------
# Gauge: value can go up or down — right choice for "current state" figures.
active_users_total = Gauge(
    "active_users_total",
    "Number of currently active users (simulated from DB session table)",
)

# Counter: monotonically increasing — right choice for cumulative totals.
jobs_queued_total = Counter(
    "jobs_queued_total",
    "Total number of jobs ever placed on the queue (simulated)",
)

jobs_processed_total = Counter(
    "jobs_processed_total",
    "Total number of jobs processed off the queue (simulated)",
    ["status"],  # success | failure
)

# Histogram: distribution of an observed value — right choice for latency
# or ratio-like measurements you want percentiles on.
webhook_delivery_duration_seconds = Histogram(
    "webhook_delivery_duration_seconds",
    "Simulated webhook delivery duration",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

webhook_delivery_success_ratio = Gauge(
    "webhook_delivery_success_ratio",
    "Rolling ratio of successful webhook deliveries (0.0-1.0)",
)

job_queue_depth = Gauge(
    "job_queue_depth",
    "Current depth of the simulated job queue",
)


def _simulate_business_metrics():
    """
    Background thread simulating a real data source (would be a Postgres
    query in production: SELECT count(*) FROM sessions WHERE ...).
    Runs forever, updating metric values every 5s.
    """
    success_count = 0
    total_count = 0
    queue_depth = 20

    while True:
        # active users: random walk between 50 and 500
        active_users_total.set(random.randint(50, 500))

        # queue: jobs arrive and drain
        arrivals = random.randint(0, 8)
        drained = random.randint(0, 6)
        queue_depth = max(0, queue_depth + arrivals - drained)
        job_queue_depth.set(queue_depth)

        for _ in range(arrivals):
            jobs_queued_total.inc()

        for _ in range(drained):
            failed = random.random() < 0.05
            status = "failure" if failed else "success"
            jobs_processed_total.labels(status=status).inc()

        # webhook delivery simulation
        for _ in range(random.randint(1, 5)):
            duration = random.uniform(0.05, 3.0)
            webhook_delivery_duration_seconds.observe(duration)
            total_count += 1
            if duration < 2.5:
                success_count += 1

        if total_count > 0:
            webhook_delivery_success_ratio.set(success_count / total_count)

        time.sleep(5)


@app.on_event("startup")
def start_background_thread():
    thread = threading.Thread(target=_simulate_business_metrics, daemon=True)
    thread.start()


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok"}
