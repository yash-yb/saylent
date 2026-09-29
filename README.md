<div align="center">

# 🏥 Saylent

**A Federated AI Platform for National PHC Network Resilience**

*BRICS Hackathon 2026 · Track 3 — Smart Health & Supply Chain Resilience*

[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](./backend)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)](./frontend)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)
[![Status](https://img.shields.io/badge/status-hackathon%20prototype-orange)](#roadmap)

[Live Demo (3D)](./demo/immersive.html) · [Live Demo (classic)](./demo/index.html) · [Pitch Deck](./docs/Saylent_BRICS_Track3.pptx) · [Backend Docs](./backend/README.md)

</div>

---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Team](#team)
- [Repo Layout](#repo-layout)
- [Architecture](#architecture)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Verifying It Works](#verifying-it-works)
- [How the Forecasting Works](#how-the-forecasting-works)
- [Federated Learning](#federated-learning)
- [Tech Stack](#tech-stack)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## The Problem

Public healthcare systems across developing nations face persistent supply
chain vulnerabilities. The inability to track medicines, patient footfall,
and resource utilisation in real time across vast networks of Primary Health
Centres (PHCs) leads to stock-outs and limits a nation's capacity to respond
when it matters most.

## The Solution

**Saylent** is a federated AI platform for national-scale health resource
and supply chain management — real-time visibility into medicine stock, bed
availability, and medical personnel attendance across an entire PHC network.
It forecasts demand, generates early warnings for potential stock-outs, and
recommends automated cross-district resource redistribution — while allowing
shared predictive modelling across districts (and, by extension, BRICS
nations) **without centralising anyone's raw data**.

| Pillar | What it does |
|---|---|
| 📊 **National Visibility** | Live medicine stock, bed occupancy, and staff attendance for every PHC, rolled up to district and national dashboards |
| 📈 **Demand Forecasting** | 14-day per-medicine, per-PHC demand projections with predicted stock-out dates, using Holt's linear-trend smoothing on consumption history |
| 🔔 **Early-Warning Alerts** | Automatic stock-out, bed-capacity, and staff-attendance alerts generated before a crisis, not after |
| 🔄 **Smart Redistribution** | AI recommends cross-district transfers from surplus PHCs to at-risk PHCs, with one-click approval |
| 🕸️ **Federated Learning** | A real FedAvg implementation — districts train locally, only model weights are aggregated, never raw records |

---

## Team

| Name | 
|---|
| **Adarsh Chawrasia** |
| **Shreya Gaur** |
| **Yash Bhanushali** |

Built for **BRICS Hackathon 2026, Track 3 — Smart Health & Supply Chain
Resilience**.

---

## Repo Layout

```text
saylent/
├── backend/          FastAPI service
│   ├── app/
│   │   ├── ml/                    forecasting.py, federated_learning.py, redistribution_engine.py
│   │   ├── routers/               national, phc, alerts, redistribution, federated
│   │   ├── models.py              SQLAlchemy schema
│   │   ├── compute.py             orchestrates one full compute cycle
│   │   ├── seed_data.py           generates the realistic demo dataset
│   │   └── main.py                app entrypoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md                  full endpoint reference + production notes
├── frontend/         React + Vite + Tailwind + Recharts dashboard
│   └── src/
│       ├── pages/                 Dashboard, Districts, Alerts, Redistribution, Federated, PHCExplorer
│       └── components/
├── demo/
│   ├── immersive.html             flagship 3D/WebGL interactive demo (no setup required)
│   └── index.html                 classic lightweight dashboard demo (no setup required)
├── docs/
│   └── Saylent_BRICS_Track3.pptx  pitch deck
├── LICENSE
└── README.md                      you are here
```

## Architecture

```text
 DATA LAYER              BACKEND API             AI / ML ENGINE           DASHBOARDS
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ PHC stock entry│     │ FastAPI        │     │ Demand          │     │ National        │
│ Consumption logs├────▶│ services       ├────▶│ forecasting     ├────▶│ overview        │
│ Bed & staff     │     │ District DB /  │     │ Federated       │     │ District        │
│ status          │     │ Postgres       │     │ averaging       │     │ drill-down      │
│                 │     │ REST endpoints │     │ Redistribution  │     │ Alerts &        │
│                 │     │                │     │ engine          │     │ approvals       │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

Deployment is containerized per nation (Docker Compose), SQLite for the demo
and Postgres-ready for production, with **zero cross-border raw-data
transfer** — only aggregated model weights travel between nodes.

## Quickstart

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Docker, if you'd rather containerize the backend

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

First run auto-seeds a realistic dataset (29 PHCs, 10 districts, 4 states, 8
medicines, 60 days of consumption history) and runs one full
forecast → FedAvg → alert → redistribution compute cycle.

- API: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`
- Alternative ReDoc view: `http://localhost:8000/redoc`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173` (proxies `/api` to the backend on port 8000)
- Production build: `npm run build` → outputs to `frontend/dist`

### Docker (backend only)

```bash
cd backend
docker build -t saylent-backend .
docker run -p 8000:8000 saylent-backend
```

### Instant demo — no setup required

Two zero-setup, self-contained demo pages with mock data mirroring the real
backend's output — open either directly in a browser, no install needed:

- [`demo/immersive.html`](./demo/immersive.html) — the flagship 3D/immersive
  experience: a draggable Three.js globe with live district markers and
  animated supply-route arcs, glassmorphic cards with cursor-tracked
  lighting and 3D tilt, levitating tactile buttons, particle-burst
  micro-interactions on approve/resolve actions, and a working Chart.js
  forecast chart in the PHC explorer.
- [`demo/index.html`](./demo/index.html) — a simpler, classic dashboard
  layout (tabs + tables + one chart) for a faster-loading or lower-powered
  device.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./saylent.db` | SQLAlchemy connection string. Point this at a managed PostgreSQL instance in production — no code changes needed, only `connect_args` in `database.py` is SQLite-specific. |

No environment variables are required for the frontend in development;
`vite.config.js` proxies `/api` straight to `localhost:8000`.

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/national/summary` | National KPI header — beds, alerts, medicines at risk |
| `GET` | `/api/national/districts` | Per-district health score (healthy / watch / critical) |
| `GET` | `/api/phc` | All PHCs with live bed occupancy |
| `GET` | `/api/phc/{id}/stock` | Medicine stock lines + days-of-stock-left |
| `GET` | `/api/phc/{id}/forecast/{medicine_id}` | 14-day forecast + predicted stock-out date |
| `GET` | `/api/alerts` | Active alerts, filterable by `severity` / `type` / `district_id` |
| `POST` | `/api/alerts/{id}/resolve` | Mark an alert resolved |
| `GET` | `/api/redistribution` | Pending cross-district transfer recommendations |
| `POST` | `/api/redistribution/{id}/approve` | Approve and execute the stock transfer |
| `POST` | `/api/redistribution/{id}/reject` | Reject a recommendation |
| `GET` | `/api/federated/rounds` | Latest FedAvg round per medicine (transparency) |
| `POST` | `/api/federated/run-cycle` | Manually re-run the full compute cycle |

Full request/response schemas are in the auto-generated Swagger UI at
`/docs` once the backend is running.

## Verifying It Works

With the backend running on port 8000, a quick smoke test:

```bash
curl -s localhost:8000/ | python3 -m json.tool
curl -s localhost:8000/api/national/summary | python3 -m json.tool
curl -s localhost:8000/api/alerts | python3 -m json.tool
curl -s localhost:8000/api/redistribution | python3 -m json.tool
curl -s localhost:8000/api/federated/rounds | python3 -m json.tool
```

Every one of these was run against a live instance during development —
this isn't a mocked spec, the endpoints return real, computed results from
the seeded dataset (forecasts, alerts, and redistribution recommendations
all change if you re-run `/api/federated/run-cycle`).

## How the Forecasting Works

1. **Local trend fit** — Holt's linear-trend exponential smoothing on each
   PHC's own daily dispensed quantity: a *level* (today's typical use) plus a
   *trend* (rising or falling).
2. **Federated blend** — the district-level trend is combined with the
   FedAvg global trend (30% weight), so short-history PHCs borrow signal
   from the national pattern.
3. **14-day projection** — the blended trend projects daily demand forward
   two weeks; cumulative demand is subtracted from current stock day by day.
4. **Stock-out date + alert** — the day stock would first go negative
   becomes the predicted stock-out date; if that falls inside the medicine's
   procurement lead time, an alert fires automatically.

See [`backend/app/ml/forecasting.py`](./backend/app/ml/forecasting.py).

## Federated Learning

Every district trains a local demand-trend model on its own PHCs'
consumption data. **Only `(slope, intercept, n_points)` — three numbers per
medicine, per district — ever leave the district boundary.** The aggregator
combines them via sample-weighted FedAvg into one global trend per medicine,
which is blended back into every PHC's local forecast. Every round is logged
(`FederatedModelRound`) for full auditability.

This is what lets the platform extend from cross-district (this demo) to
cross-*nation* federation with no architecture change — each BRICS member
would simply run its own instance and exchange the same small numeric
payload with a shared aggregator.

See [`backend/app/ml/federated_learning.py`](./backend/app/ml/federated_learning.py)
and [`backend/app/compute.py`](./backend/app/compute.py).

## Tech Stack

| Layer | Choices |
|---|---|
| **Backend** | FastAPI · SQLAlchemy ORM · SQLite (→ PostgreSQL in production) |
| **AI / ML** | NumPy (Holt trend model) · custom FedAvg aggregator · greedy redistribution solver |
| **Frontend** | React 18 · Vite · Tailwind CSS · Recharts |
| **Demo** | Three.js (WebGL globe) · Chart.js |
| **Infra** | Docker Compose · REST + OpenAPI/Swagger · CORS-enabled API |

## Design Decisions & Trade-offs

- **Holt's linear trend over a heavier model (ARIMA/Prophet/LSTM)** —
  chosen because it has to run per-PHC, per-medicine, at national scale,
  nightly, and still be explainable in one sentence to a non-technical
  district health officer. Two numbers (level, trend) are auditable in a
  way a neural net isn't.
- **FedAvg over a fully custom aggregation scheme** — it's the standard,
  well-understood approach, which matters when the pitch depends on the
  aggregation being trustworthy and reviewable, not novel for its own sake.
- **Greedy matching over a full LP solver for redistribution** — a
  transportation-problem solver would find a marginally more optimal set of
  transfers, but a greedy surplus-to-deficit match is easy to explain and
  fast enough to recompute on every cycle; optimality is a v2 concern once
  real-world constraints (transport cost, distance, cold-chain requirements)
  are added anyway.
- **SQLite for the demo, Postgres-ready by design** — every access goes
  through SQLAlchemy; only `connect_args` in `database.py` is SQLite-
  specific, so swapping `DATABASE_URL` is the entire migration.

## Known Limitations

- The dataset is realistic but **synthetic** — consumption logs are
  generated with deliberate trends/noise, not sourced from a real PHC
  network. Forecast accuracy against real-world data is unvalidated.
- Redistribution recommendations don't yet account for transport distance,
  cost, or cold-chain requirements for temperature-sensitive medicines
  (vaccines, insulin) — a real deployment would need to fold those into the
  matching logic.
- The federated rounds in this repo aggregate across **districts within one
  database**, as a stand-in for aggregating across **separate national
  instances**; the math doesn't change, but the network/deployment layer
  for true cross-nation federation isn't built here.
- No authentication/authorization layer yet (no RBAC for PHC vs. district
  vs. national roles) — flagged in the Roadmap below.

## Roadmap

| Phase | Milestone |
|---|---|
| 1 — Prototype (now) | Full-stack demo: forecasting, FedAvg, redistribution, dashboards on realistic mock PHC data |
| 2 — Single-state pilot | Integrate real PHC reporting (manual entry app + CSV import); validate forecasts against real consumption |
| 3 — National rollout | Postgres + nightly compute cycle; district health officer training; mobile reporting app for PHC staff; RBAC |
| 4 — Cross-BRICS federation | Each member nation runs its own instance; shared FedAvg aggregator endpoint; joint epidemiological early-warning |

## Contributing

This is a hackathon submission, but suggestions and issues are welcome:

1. Fork the repo and create a feature branch (`git checkout -b feature/x`)
2. Make your changes — for backend changes, please run the smoke test in
   [Verifying It Works](#verifying-it-works) before opening a PR
3. Open a pull request describing what changed and why

## Acknowledgements

- Problem statement: **BRICS Hackathon 2026, Track 3 — Smart Health &
  Supply Chain Resilience**
- Built with FastAPI, React, SQLAlchemy, Recharts, Three.js, and Chart.js

## License

MIT — see [`LICENSE`](./LICENSE).
