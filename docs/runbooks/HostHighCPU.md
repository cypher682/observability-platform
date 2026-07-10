# Runbook: HostHighCPU

## What it means
Average CPU utilization (non-idle) on a host has stayed above 85% for at
least 5 minutes. A single spike doesn't fire this — sustained load does.

## How to investigate
1. Check Grafana → Infrastructure Overview dashboard → CPU panel for the
   affected `instance` label.
2. `docker stats` (or `top`/`htop` on the host) to identify the top
   CPU-consuming process/container.
3. Cross-check the Container Metrics dashboard (cadvisor) — is one
   container responsible, or is it host-wide?
4. Check Loki logs for the same time window — look for a deploy, cron job,
   or retry storm that coincides with the spike.

## Steps to resolve
- If a single container is runaway: restart or scale it down
  (`docker compose restart <service>`), then investigate root cause
  (infinite loop, missing rate limit, etc.)
- If host-wide and expected (e.g. intentional load test): silence for the
  duration (see below) rather than resolve as an incident.
- If unexpected and host-wide: check for resource contention from another
  process outside the stack.

## How to silence during maintenance
```
amtool silence add alertname="HostHighCPU" instance="<instance>" \
  --duration=2h --comment="planned load test"
```
Or via Alertmanager UI at http://localhost:9093 → Silences → New Silence.
