# Runbook: CustomExporterJobQueueHigh

## What it means
The `job_queue_depth` gauge exported by custom-exporter has stayed above
100 for 5 minutes — jobs are arriving faster than they're being drained.

## How to investigate
1. Grafana → Custom Business Metrics dashboard → job_queue_depth panel,
   check the trend (climbing steadily vs. one-off spike).
2. Compare `rate(jobs_queued_total[5m])` vs
   `rate(jobs_processed_total[5m])` — confirms whether it's an arrival
   spike or a processing slowdown.
3. Check `jobs_processed_total{status="failure"}` — are jobs failing and
   piling back up rather than draining?

## Steps to resolve
- If arrival spike (traffic surge): may resolve on its own; consider
  scaling worker capacity if sustained.
- If processing slowdown: check worker/consumer health (in this demo,
  the exporter simulates this — in production this maps to your actual
  queue consumer's logs/metrics).
- If failures are piling jobs back onto the queue: fix the underlying
  failure first, the depth alert is downstream of it.

## How to silence during maintenance
```
amtool silence add alertname="CustomExporterJobQueueHigh" --duration=1h \
  --comment="known backlog, processing catch-up in progress"
```
