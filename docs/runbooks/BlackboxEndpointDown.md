# Runbook: BlackboxEndpointDown

## What it means
The blackbox-exporter's HTTP probe against a monitored endpoint has failed
continuously for 1 minute (non-2xx response, timeout, or connection
refused).

## How to investigate
1. Grafana → check the Blackbox probe panel / Prometheus
   `probe_success{instance="<target>"}` to confirm which target is down.
2. `curl -v <target-url>` from the host to reproduce directly.
3. `docker compose ps` — is the target container even running?
4. `docker compose logs <target-service>` for crash/startup errors.

## Steps to resolve
- If the container crashed: `docker compose up -d <service>` to restart,
  then check logs for the crash root cause.
- If the container is up but the app isn't responding: check the app's
  own health endpoint and logs directly.
- If this is expected downtime (e.g. deliberate restart for a config
  change): silence for the duration.

## How to silence during maintenance
```
amtool silence add alertname="BlackboxEndpointDown" instance="<target>" \
  --duration=15m --comment="planned restart"
```
