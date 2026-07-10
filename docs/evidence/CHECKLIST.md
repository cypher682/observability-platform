# Evidence Checklist

Screenshots and artifacts go in this folder, named exactly as below so the
README and Dev.to article can reference them directly.

Full step-by-step instructions for producing each one are in the separate
**TESTING-GUIDE.md** at the repo root. This file is just the checklist to
tick off.

- [ ] `01-architecture-diagram.png` — the Mermaid diagram from architecture.md, rendered
- [ ] `02-prometheus-targets.png` — Prometheus `/targets`, all jobs UP
- [ ] `03-grafana-datasources.png` — Grafana datasource list, all 3 provisioned
- [ ] `04-dashboard-infrastructure.png`
- [ ] `05-dashboard-containers.png`
- [ ] `06-dashboard-application-slis.png`
- [ ] `07-dashboard-custom-business-metrics.png`
- [ ] `08-dashboard-loki-log-explorer.png`
- [ ] `09-dashboard-tempo-traces.png`
- [ ] `10-dashboard-alertmanager.png`
- [ ] `11-alert-firing.png` — an alert in "Firing" state in Prometheus/Alertmanager UI
- [ ] `12-alertmanager-routing.png` — webhook-receiver `/received` showing the routed payload
- [ ] `13-alert-resolved.png` — same alert transitioned to resolved
- [ ] `14-runbook-example.png` or link — one complete runbook shown
- [ ] `15-custom-exporter-metrics.png` — raw `/metrics` output from custom-exporter
- [ ] `16-logql-query.png` — a LogQL query with real results in Grafana Explore
- [ ] `17-tempo-trace-waterfall.png` — a full trace with multiple spans
- [ ] `18-trace-to-log-correlation.png` — clicking from a trace into its logs
- [ ] `19-k8s-pods-running.png` — `kubectl get pods -n observability` all Running
- [ ] `20-dashboards-as-code-proof.png` — dashboards reappearing identically after deleting the Grafana volume and re-running `docker compose up`

Once all boxes are checked, D1 is fully evidenced and ready for:
1. GitHub push
2. Dev.to article ("Building the full LGTM observability stack...")
3. LinkedIn post
4. X thread
