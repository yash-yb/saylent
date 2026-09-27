<div align="center">

# 🏥 Project

**A Federated AI Platform for National PHC Network Resilience**

*BRICS Hackathon 2026 · Track 3 — Smart Health & Supply Chain Resilience*

[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](./backend)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)](./frontend)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)

[Live Demo](./demo/index.html) · [Pitch Deck](./docs/Project_BRICS_Track3.pptx) · [Backend Docs](./backend/README.md)

</div>

---

## The Problem

Public healthcare systems across developing nations face persistent supply
chain vulnerabilities. The inability to track medicines, patient footfall,
and resource utilisation in real time across vast networks of Primary Health
Centres (PHCs) leads to stock-outs and limits a nation's capacity to respond
when it matters most.

## The Solution

**Project** is a federated AI platform for national-scale health resource
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

## Table of Contents

- [Repo Layout](#repo-layout)
- [Architecture](#architecture)
- [Quickstart](#quickstart)
- [API Reference](#api-reference)
- [How the Forecasting Works](#how-the-forecasting-works)
- [Federated Learning](#federated-learning)
- [Tech Stack](#tech-stack)
- [Roadmap](#roadmap)
- [License](#license)

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
│   └── index.html                 self-contained, zero-setup interactive demo
└── docs/
    └── Project_BRICS_Track3.pptx
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

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173` (proxies `/api` to the backend on port 8000)

### Docker (backend only)

```bash
cd backend
docker build -t arogyagrid-backend .
docker run -p 8000:8000 arogyagrid-backend
```

### Instant demo — no setup required

Open [`demo/index.html`](./demo/index.html) directly in any browser. It's a
fully self-contained page with mock data mirroring the real backend's output
— useful for a quick screen recording or for sharing before you've deployed
the full stack.

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
| **Infra** | Docker Compose · REST + OpenAPI/Swagger · CORS-enabled API |

## Roadmap

| Phase | Milestone |
|---|---|
| 1 — Prototype (now) | Full-stack demo: forecasting, FedAvg, redistribution, dashboards on realistic mock PHC data |
| 2 — Single-state pilot | Integrate real PHC reporting (manual entry app + CSV import); validate forecasts against real consumption |
| 3 — National rollout | Postgres + nightly compute cycle; district health officer training; mobile reporting app for PHC staff |
| 4 — Cross-BRICS federation | Each member nation runs its own instance; shared FedAvg aggregator endpoint; joint epidemiological early-warning |

## License

MIT — see [`LICENSE`](./LICENSE).
