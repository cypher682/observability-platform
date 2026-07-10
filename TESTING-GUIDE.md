# TESTING-GUIDE.md
# observability-platform — Step-by-Step Verification

This is the document to follow when actually running this stack. It's
separate from the README because the README describes *what the repo is*;
this describes *what to type and what you should see*, stage by stage,
matching the original 7-stage build plan.

Run these in order. Each stage builds on the last — don't skip ahead if
something in an earlier stage doesn't look right, since later stages
depend on it.

---

## Prerequisites

- Docker Desktop running (WSL2 backend is fine)
- `docker compose version` → should show v2.x
- Ports free on your machine: 3000, 8000, 8080 (cadvisor), 8090, 9090,
  9093, 9100, 9115, 9200, 3100, 3200, 4317, 4318, 5432
- ~4GB RAM free for Docker

```bash
cd observability-platform/docker-compose
docker compose up -d --build
```

First run will take a few minutes (building target-app, custom-exporter,
webhook-receiver images + pulling the rest). Subsequent runs are fast.

```bash
docker compose ps
```

All 14 services should show `Up` (or `Up (healthy)` where a healthcheck
exists). If any show `Restarting` or `Exit`, run:
```bash
docker compose logs <service-name>
```
before moving on — see the Troubleshooting section at the bottom.

---

## Stage 1 — Core Metrics (Prometheus, Grafana, Alertmanager, node-exporter, cadvisor)

1. **Prometheus targets** → http://localhost:9090/targets
   Expect `prometheus`, `node-exporter`, `cadvisor`, `custom-exporter`,
   `otel-collector`, `blackbox-http` jobs all `UP`. (custom-exporter and
   otel-collector show UP once you've also confirmed those containers
   built successfully in Stage 3/4 — if this is your very first pass
   through and those aren't up yet, that's expected.)

   📸 **Evidence #02**: screenshot this page.

2. **Grafana** → http://localhost:3000
   Login: `admin` / password from your `.env` file.
   Go to Connections → Data sources. You should see **Prometheus**,
   **Loki**, and **Tempo** already listed — provisioned automatically,
   not added by hand.

   📸 **Evidence #03**: screenshot the datasource list.

3. Grafana → Dashboards. You should see all 7 dashboards already present:
   Infrastructure Overview, Container Metrics, Application SLIs, Custom
   Business Metrics, Loki Log Explorer, Tempo Traces, Alertmanager.

4. Open **Infrastructure Overview** — CPU/memory/disk/network panels
   should show live data within ~30 seconds.

   📸 **Evidence #04**: screenshot this dashboard with data populated.

5. Open **Container Metrics** — per-container CPU/memory should be
   populated (cadvisor data).

   📸 **Evidence #05**

**If targets aren't UP:** check `docker compose logs prometheus`. A
common cause is a typo in `prometheus.yml` — check indentation, since
YAML is whitespace-sensitive.

---

## Stage 2 — Logs (Loki, Promtail)

1. Grafana → Explore → select **Loki** datasource.
2. Query: `{compose_project="observability-platform"}`
   You should see log lines streaming from all containers.
3. Try: `{container="target-app"}` — should show FastAPI/uvicorn startup
   logs and per-request logs from the load-generator hitting it.

   📸 **Evidence #16**: screenshot this query with results.

4. Open the **Loki Log Explorer** dashboard — the "Log Volume by
   Container" panel should show activity, and the two log panels should
   be populated.

   📸 **Evidence #08**

**If no logs appear:** Promtail needs access to the Docker socket. On
Linux/WSL2 this is usually automatic; on Docker Desktop for Mac/Windows,
confirm `/var/run/docker.sock` is shared with the Docker VM (Settings →
Resources → File sharing).

---

## Stage 3 — Traces (Tempo, OTel Collector, target-app)

1. Confirm target-app is receiving traffic — the `load-generator`
   container hits `/work`, `/error-prone`, and `/slow` every 2s
   automatically. Confirm with:
   ```bash
   docker compose logs -f load-generator
   ```
   (Ctrl+C to stop watching, it keeps running in the background.)

2. Grafana → Explore → select **Tempo** datasource → Search tab.
   Service Name: `target-app`. Run search. You should see a list of
   traces.

3. Click into any trace → you should see a waterfall with spans for the
   FastAPI request handler and the nested `simulate-db-call` span (from
   `/work`).

   📸 **Evidence #17**: screenshot the trace waterfall.

4. From within a trace view, look for the **Logs for this span** button
   (trace-to-log correlation) — click it to jump to the matching Loki
   logs.

   📸 **Evidence #18**

5. Open the **Tempo Traces** dashboard — the pre-built TraceQL panels
   (`{ .service.name = "target-app" }`, slow traces, error traces) should
   populate.

   📸 **Evidence #09**

**If no traces appear:** check `docker compose logs target-app` for OTel
export errors, and `docker compose logs otel-collector`. Common cause:
target-app started before otel-collector was ready — restart target-app:
```bash
docker compose restart target-app
```

---

## Stage 4 — Custom Exporter

1. Raw metrics: http://localhost:9200/metrics
   Should show Prometheus-format text output including
   `active_users_total`, `job_queue_depth`, `jobs_queued_total`,
   `webhook_delivery_success_ratio`, `webhook_delivery_duration_seconds_bucket`.

   📸 **Evidence #15**: screenshot this raw output.

2. Prometheus → `/targets` → confirm `custom-exporter` job is `UP`.

3. Grafana → **Custom Business Metrics** dashboard → all 5 panels should
   show live, changing values (the exporter updates every 5s).

   📸 **Evidence #07**

---

## Stage 5 — Alerting

1. Confirm rules loaded: http://localhost:9090/rules
   All 7 alert rules (grouped by the 6 rule groups in `alert-rules.yml`)
   should be listed, state `inactive` initially.

2. **Trigger a real alert** — easiest is `AppHighErrorRate`, since
   `/error-prone` already fails ~15% of requests under continuous
   load-generator traffic. Wait ~2-3 minutes with the stack running;
   check http://localhost:9090/alerts — `AppHighErrorRate` should
   transition to `pending` then `firing`.

   If you want to force `HostHighCPU` instead for a faster/more visual
   test:
    docker run --rm -it --network observability-platform_obs-net python:3.12 python -c "
    import multiprocessing, time
    def stress():
        while True: pass
    if __name__ == '__main__':
        processes = [multiprocessing.Process(target=stress) for _ in range(4)]
        for p in processes: p.start()
        time.sleep(400)
        for p in processes: p.terminate()
    "

3. Once firing, check Alertmanager: http://localhost:9093
   The alert should appear, routed per severity.

   📸 **Evidence #11**: screenshot the firing alert in Prometheus or Alertmanager.

4. Check the webhook received it: http://localhost:8090/received
   You should see a JSON payload with the alert details, tagged
   `"route": "critical"` or `"route": "warning"`.

   📸 **Evidence #12**

5. Stop the load or wait for the condition to clear, then re-check
   `/received` or the Alertmanager UI — the alert should show as
   resolved (if `send_resolved: true`, which is already configured).

   📸 **Evidence #13**

6. Open the **Alertmanager** dashboard in Grafana — should reflect the
   same firing/resolved state.

   📸 **Evidence #10**

7. Pick one runbook (e.g. `docs/runbooks/AppHighErrorRate.md`) and
   screenshot it rendered (GitHub preview or your editor).

   📸 **Evidence #14**

**Note on metric names:** the alert rules assume OTel's default FastAPI
instrumentation metric names (`http_server_requests_total`,
`http_server_duration_seconds_bucket`). If your installed OTel SDK
version emits different names, check actual names with:
```bash
curl -s http://localhost:9090/api/v1/label/__name__/values | grep http
```
and adjust `alert-rules/rules.yml` + the Application SLIs dashboard
queries to match. This is a normal, expected part of verification — OTel
semantic conventions have changed across versions.

---

## Stage 6 — Kubernetes (minikube)

1. Start minikube and build local images:
   ```bash
   minikube start --cpus=4 --memory=6g
   minikube addons enable ingress

   eval $(minikube docker-env)     # point your shell's docker CLI at minikube's daemon
   docker build -t target-app:local ./target-app
   docker build -t custom-exporter:local ./custom-exporter
   docker build -t webhook-receiver:local ./webhook-receiver
   ```

2. Apply namespace + manifests:
   ```bash
   kubectl apply -f kubernetes/manifests/00-namespace.yaml
   kubectl apply -f kubernetes/manifests/
   ```

3. Install the three Helm releases (see README Kubernetes section for
   exact commands).

4. Check everything is running:
   ```bash
   kubectl get pods -n observability
   ```
   All pods should reach `Running` (allow a few minutes for image pulls).

   📸 **Evidence #19**: screenshot this output.

5. Access Grafana via the Ingress:
   ```bash
   echo "$(minikube ip) grafana.observability.local" | sudo tee -a /etc/hosts
   ```
   Then browse to http://grafana.observability.local

**If pods stay Pending:** likely insufficient CPU/memory allocated to
minikube — increase with `minikube start --cpus=6 --memory=8g` (delete
and restart the cluster first: `minikube delete`).

**If custom-exporter/target-app pods show ImagePullBackOff:** confirm you
ran `eval $(minikube docker-env)` *before* building the images, so they
land in minikube's Docker daemon rather than your host's.

---

## Stage 7 — Dashboards-as-Code Proof + Final Evidence Pass

1. **Prove provisioning, not manual setup:**
   ```bash
   docker compose down
   docker volume rm docker-compose_grafana-data
   docker compose up -d
   ```
   Wait ~30s, log into Grafana again. All 7 dashboards should reappear
   automatically with no manual re-creation.

   📸 **Evidence #20**: screenshot dashboards list immediately after this reset.

2. Go through `docs/evidence/CHECKLIST.md` top to bottom and confirm every
   box has a corresponding screenshot saved into `docs/evidence/`.

3. Take one clean screenshot/export of `docs/architecture.md`'s Mermaid
   diagram (GitHub renders it automatically when the file is viewed, or
   use the Mermaid Live Editor to export a PNG).

   📸 **Evidence #01**

---

## Teardown

```bash
# Docker Compose
cd docker-compose
docker compose down -v     # -v also removes volumes (TSDB, Loki chunks, etc.)

# Kubernetes
helm uninstall kube-prometheus-stack loki tempo -n observability
kubectl delete namespace observability
minikube delete
```

---

## Troubleshooting Quick Reference

| Symptom | Likely cause | Fix |
|---|---|---|
| Target shows DOWN in Prometheus | Container not started yet, or wrong port | `docker compose ps`, check `docker compose logs <service>` |
| No Grafana datasources | Provisioning volume not mounted correctly | Check `docker-compose.yml` volumes match `configs/grafana/provisioning` path exactly |
| No logs in Loki | Docker socket not accessible to Promtail | Check Docker Desktop file sharing settings |
| No traces in Tempo | target-app started before otel-collector | `docker compose restart target-app` |
| Alert never fires | Metric name mismatch (OTel version drift) | Check real metric names via Prometheus API, adjust rule expressions |
| K8s pods Pending | Insufficient minikube resources | `minikube delete` then restart with more `--cpus`/`--memory` |
| ImagePullBackOff on custom images | Built image on host Docker, not minikube's | Re-run `eval $(minikube docker-env)` then rebuild |

---

Once every checklist item in `docs/evidence/CHECKLIST.md` is checked off,
D1 is fully evidenced. At that point — per the portfolio plan — the
sequence is: **F4 deploy + evidence → D3 deploy + evidence → D1 (this,
already done) → then write all three blog posts together.**
