"""
target-app: a small FastAPI service instrumented end-to-end with OpenTelemetry.

Purpose: generate realistic metrics, logs, and traces so the observability
stack (Prometheus, Loki, Tempo, Grafana) has real data to display —
not synthetic/toy dashboards.

Endpoints:
  GET  /health        -> liveness, always 200
  GET  /work          -> simulates variable-latency work + DB call (traced)
  GET  /error-prone   -> randomly errors ~15% of the time (feeds AppHighErrorRate)
  GET  /slow          -> randomly slow ~10% of the time (feeds AppHighLatency)
"""

import logging
import random
import time

from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy import create_engine, text

# --- OTel wiring -----------------------------------------------------------
resource = Resource.create({"service.name": "target-app"})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

LoggingInstrumentor().instrument(set_logging_format=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("target-app")

app = FastAPI(title="target-app")
FastAPIInstrumentor.instrument_app(app)

# Simulated DB — SQLAlchemy engine so SQLAlchemyInstrumentor has something
# real to trace. Points at the postgres service added in Stage 4.
import os

engine = create_engine(
    os.environ.get(
        "DATABASE_URL",
        "postgresql://obs_admin:changeme_local_only@postgres:5432/obs_metrics",
    ),
    pool_pre_ping=True,
)
SQLAlchemyInstrumentor().instrument(engine=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/work")
def work():
    with tracer.start_as_current_span("simulate-db-call"):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # DB may not be up yet during early stages
            logger.warning("db unavailable, continuing without it: %s", exc)
        time.sleep(random.uniform(0.01, 0.08))
    logger.info("work request completed")
    return {"result": "done"}


@app.get("/error-prone")
def error_prone():
    if random.random() < 0.15:
        logger.error("simulated failure in error-prone endpoint")
        raise HTTPException(status_code=500, detail="simulated failure")
    return {"result": "ok"}


@app.get("/slow")
def slow():
    if random.random() < 0.10:
        delay = random.uniform(0.6, 1.2)
        logger.warning("simulated slow path, sleeping %.2fs", delay)
        time.sleep(delay)
    else:
        time.sleep(random.uniform(0.02, 0.1))
    return {"result": "ok"}
