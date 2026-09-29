# Saylent — Backend

Federated AI platform for national PHC (Primary Health Centre) network
resilience. Built for **BRICS Hackathon Track 3 — Smart Health & Supply
Chain Resilience**.

## What it actually does

1. **Data model** — Nation → State → District → PHC, with per-PHC medicine
   stock, daily consumption logs, bed status, and staff attendance.
2. **Local forecasting** (`app/ml/forecasting.py`) — Holt's linear-trend
   exponential smoothing per PHC per medicine, fit on real consumption
   history, projecting 14 days of demand and a predicted stockout date.
3. **Federated averaging** (`app/ml/federated_learning.py`) — every district
   trains its own local trend model on its own PHCs' data; only
   `(slope, intercept, n_points)` — never raw records — are sent to the
   aggregator, which computes a sample-weighted FedAvg global trend. Each
   PHC's own forecast is then blended with that global trend, so low-history
   PHCs still benefit from national patterns without centralising anyone's
   raw data. This is the direct answer to the brief's "federated AI
   platform" + "shared predictive modelling across BRICS nations" ask —
   extending to more nations is just adding more `Nation`/`State` rows and
   running the same aggregation across them.
4. **Redistribution engine** (`app/ml/redistribution_engine.py`) — for every
   medicine, computes each PHC's surplus/deficit against its own forecast
   need (+ safety buffer) and greedily proposes transfers from
   surplus PHCs to deficit PHCs.
5. **Alerts** — stockout-risk, low-bed-capacity, and low-attendance alerts
   are regenerated from live forecasts + snapshots.
6. **`compute.py`** ties 2–5 together into one "compute cycle" — this is
   what would run nightly per nation in production.

## Run it

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

First run auto-seeds a realistic 60-day mock dataset (29 PHCs, 10 districts,
4 states, 8 medicines) and runs one full compute cycle. Open
`http://localhost:8000/docs` for interactive Swagger docs of every endpoint.

## Run with Docker

```bash
docker build -t project-backend .
docker run -p 8000:8000 project-backend
```

## Key endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/national/summary` | National KPI header (beds, alerts, medicines at risk) |
| `GET /api/national/districts` | Per-district health score (healthy/watch/critical) |
| `GET /api/phc` | All PHCs with live bed occupancy |
| `GET /api/phc/{id}/stock` | Medicine stock lines + days-of-stock-left |
| `GET /api/phc/{id}/forecast/{medicine_id}` | 14-day forecast + stockout date |
| `GET /api/alerts` | Active alerts (filterable by severity/type/district) |
| `GET /api/redistribution` | Pending cross-district transfer recommendations |
| `POST /api/redistribution/{id}/approve` | Executes the stock transfer |
| `GET /api/federated/rounds` | Latest FedAvg round per medicine (transparency) |
| `POST /api/federated/run-cycle` | Manually re-run the full compute cycle |

## Swapping in production infra

- `DATABASE_URL` env var — point at Postgres per nation (SQLAlchemy already
  supports this; only `connect_args` is SQLite-specific).
- Wrap `run_compute_cycle` in a scheduler (cron / Celery beat / Airflow).
- For real cross-*nation* federation (not just cross-district within one
  demo DB), each nation runs its own instance of this service and only the
  small `(slope, intercept, n)` payload is exchanged with a shared
  aggregator endpoint — the FedAvg math in `federated_learning.py` doesn't
  change at all.
