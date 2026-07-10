# Runbook: AppHighErrorRate

## What it means
The target-app's 5xx response rate has exceeded 5% of total requests,
sustained for 2 minutes.

## How to investigate
1. Grafana → Application SLIs dashboard → error rate panel to confirm
   scope (all endpoints or one).
2. Tempo → filter traces by `status=error` in the relevant time window —
   the trace waterfall will show exactly which span failed and why.
3. Use Grafana's trace-to-log correlation (derived field) to jump from
   the failing trace directly to its log lines in Loki.
4. In this repo's target-app, `/error-prone` intentionally fails ~15% of
   requests — useful for confirming the alert pipeline works end-to-end
   before assuming a real regression.

## Steps to resolve
- If caused by a bad deploy: roll back.
- If caused by a downstream dependency (DB, third-party API): check that
  dependency's health first.
- If it's the intentional `/error-prone` demo endpoint: this is expected
  test traffic, not an incident — silence rather than "resolve."

## How to silence during maintenance
```
amtool silence add alertname="AppHighErrorRate" component="application" \
  --duration=1h --comment="expected from /error-prone demo traffic"
```
