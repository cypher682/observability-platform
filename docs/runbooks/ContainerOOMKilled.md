# Runbook: ContainerOOMKilled

## What it means
A container was killed by the Linux OOM killer because it exceeded its
memory limit (or contributed to host memory pressure).

## How to investigate
1. `docker inspect <container>` → check `State.OOMKilled` and
   `HostConfig.Memory` limit.
2. Grafana → Container Metrics dashboard → memory panel for that
   container, look at the trend leading up to the kill.
3. Loki logs immediately before the kill — was there an unusual request
   volume or a memory leak pattern (steadily climbing, never releasing)?

## Steps to resolve
- If the limit is simply too low for legitimate load: raise the memory
  limit in docker-compose.yml (or the Helm values / K8s resource limits).
- If it's a leak: this is a code-level fix in the affected service —
  document as a follow-up, don't just raise the limit as a permanent fix.
- Restart the container: `docker compose restart <service>`.

## How to silence during maintenance
```
amtool silence add alertname="ContainerOOMKilled" name="<container>" \
  --duration=30m --comment="known issue, fix in progress"
```
