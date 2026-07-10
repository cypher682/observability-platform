# Runbook: HostDiskFull

## What it means
A filesystem (excluding tmpfs/overlay) is above 90% used, sustained for
5 minutes.

## How to investigate
1. Identify the mountpoint from the alert's `mountpoint` label.
2. `df -h` on the host to confirm and see which filesystem is affected.
3. `du -sh /* 2>/dev/null | sort -rh | head -20` to find the largest
   consumers.
4. Common culprits in this stack: Prometheus TSDB, Loki chunks, or
   Docker's own image/layer cache growing unbounded.

## Steps to resolve
- Prometheus/Loki retention is already bounded (15d / 7d respectively) —
  if still filling up, retention may need tightening further for a
  resource-constrained dev machine.
- `docker system prune` (careful — removes unused images/volumes) to
  reclaim Docker's layer cache.
- If a specific volume is the cause, consider moving it or expanding disk.

## How to silence during maintenance
```
amtool silence add alertname="HostDiskFull" --duration=1h \
  --comment="manual cleanup in progress"
```
