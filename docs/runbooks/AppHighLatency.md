# Runbook: AppHighLatency

## What it means
p99 request latency for target-app has exceeded 500ms, sustained for
3 minutes.

## How to investigate
1. Grafana → Application SLIs → latency panel (p50/p95/p99) to see how
   widespread the slowdown is.
2. Tempo → find slow traces (duration > 500ms) → inspect the waterfall to
   see which span (DB call, external call, app logic) dominates the time.
3. Check whether HostHighCPU or container resource limits are also firing
   at the same `instance`/`component` — the inhibition rule in
   alertmanager.yml suppresses this as a duplicate if HostHighCPU is
   already critical on the same instance, since it's often the same root
   cause.

## Steps to resolve
- If DB-bound: check Postgres connection pool exhaustion, slow queries.
- If CPU-bound: see HostHighCPU runbook.
- If it's the intentional `/slow` demo endpoint: expected test traffic.

## How to silence during maintenance
```
amtool silence add alertname="AppHighLatency" --duration=1h \
  --comment="expected from /slow demo traffic"
```
