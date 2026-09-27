"""
Orchestrates one "compute cycle" of the platform:

1. LOCAL TRAINING — for every district, aggregate its PHCs' consumption logs
   per medicine and fit a local trend model (forecasting.holt_smoothing).
2. FEDERATED AGGREGATION — FedAvg those district-local models per medicine
   into one national GlobalModel (federated_learning.federated_average).
   Only (slope, intercept, n) travel; raw logs never leave step 1.
3. PER-PHC FORECAST — every PHC gets its own local model blended with the
   federated global trend, projects 14-day demand, and gets a predicted
   stockout date.
4. ALERTS — stockout-risk, low-bed-capacity, low-attendance alerts are
   (re)generated from the forecasts + latest snapshots.
5. REDISTRIBUTION — per medicine, PHC surplus/deficit positions are computed
   from the same forecasts and fed to the greedy matcher.

In production this cycle runs nightly per BRICS member nation, with only
step 2's small numeric payload crossing any node boundary.
"""
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models as m
from .ml.forecasting import holt_smoothing, project_forecast, predicted_stockout_date
from .ml.federated_learning import federated_average, GlobalModel
from .ml.redistribution_engine import PHCPosition, recommend_redistribution


def _series_for(db: Session, phc_id: int, medicine_id: int, days: int = 60):
    logs = (
        db.query(m.ConsumptionLog)
        .filter(m.ConsumptionLog.phc_id == phc_id, m.ConsumptionLog.medicine_id == medicine_id)
        .order_by(m.ConsumptionLog.date.asc())
        .all()
    )
    return [l.qty_dispensed for l in logs[-days:]]


def run_compute_cycle(db: Session):
    medicines = db.query(m.Medicine).all()
    districts = db.query(m.District).all()

    global_models: dict[int, GlobalModel] = {}
    fed_round_log = []

    for med in medicines:
        district_local_models = []
        for district in districts:
            phc_ids = [p.id for p in district.phcs]
            if not phc_ids:
                continue
            # aggregate district-wide daily series (sum across its PHCs)
            rows = (
                db.query(m.ConsumptionLog.date, func.sum(m.ConsumptionLog.qty_dispensed))
                .filter(m.ConsumptionLog.phc_id.in_(phc_ids), m.ConsumptionLog.medicine_id == med.id)
                .group_by(m.ConsumptionLog.date)
                .order_by(m.ConsumptionLog.date.asc())
                .all()
            )
            series = [float(v) for _, v in rows]
            if series:
                district_local_models.append(holt_smoothing(series))

        gm = federated_average(district_local_models)
        global_models[med.id] = gm

        existing_round = db.query(func.max(m.FederatedModelRound.round_number)).filter(
            m.FederatedModelRound.medicine_id == med.id
        ).scalar() or 0
        fed_round_log.append(m.FederatedModelRound(
            medicine_id=med.id,
            round_number=existing_round + 1,
            participating_districts=gm.participating_units,
            global_slope=gm.slope,
            global_intercept=gm.intercept,
        ))

    db.add_all(fed_round_log)

    # clear stale pending alerts / recommendations before regenerating
    db.query(m.Alert).filter(m.Alert.resolved == False).delete()  # noqa: E712
    db.query(m.RedistributionRecommendation).filter(
        m.RedistributionRecommendation.status == "pending"
    ).delete()
    db.commit()

    today = date.today()
    new_alerts = []
    positions_by_medicine = defaultdict(list)

    phcs = db.query(m.PHC).all()
    for phc in phcs:
        stocks = db.query(m.MedicineStock).filter(m.MedicineStock.phc_id == phc.id).all()
        for stock in stocks:
            med = stock.medicine
            series = _series_for(db, phc.id, med.id)
            local = holt_smoothing(series)
            gm = global_models.get(med.id)
            forecast = project_forecast(local, horizon_days=14,
                                         global_slope=gm.slope if gm else None)
            stockout = predicted_stockout_date(stock.current_qty, forecast, today)
            avg_daily = sum(forecast) / len(forecast) if forecast else 0.0

            lead_time = med.procurement_lead_time_days
            required_qty = avg_daily * lead_time * 1.5  # safety buffer
            positions_by_medicine[med.id].append(PHCPosition(
                phc_id=phc.id, phc_name=phc.name, district_name=phc.district.name,
                current_qty=stock.current_qty, required_qty=required_qty,
            ))

            if stockout is not None and (stockout - today).days <= lead_time:
                severity = "critical" if (stockout - today).days <= max(1, lead_time // 2) else "high"
                new_alerts.append(m.Alert(
                    phc_id=phc.id, type="stockout_risk", medicine_id=med.id,
                    severity=severity, predicted_date=stockout,
                    message=(f"{med.name} at {phc.name} projected to run out on "
                             f"{stockout.isoformat()} at current consumption trend "
                             f"(lead time {lead_time}d)."),
                ))
            elif stock.current_qty <= stock.reorder_level:
                new_alerts.append(m.Alert(
                    phc_id=phc.id, type="stockout_risk", medicine_id=med.id,
                    severity="medium", predicted_date=None,
                    message=f"{med.name} at {phc.name} is at/below its reorder level.",
                ))

        # bed capacity alert
        bed_row = (db.query(m.BedStatus).filter(m.BedStatus.phc_id == phc.id)
                   .order_by(m.BedStatus.date.desc()).first())
        if bed_row and phc.total_beds > 0:
            occ_pct = bed_row.occupied_beds / phc.total_beds * 100
            if occ_pct >= 90:
                new_alerts.append(m.Alert(
                    phc_id=phc.id, type="low_bed_capacity", severity="high",
                    message=f"{phc.name} bed occupancy at {occ_pct:.0f}% — near capacity.",
                ))

        # attendance alert
        att_rows = db.query(m.PersonnelAttendance).filter(m.PersonnelAttendance.phc_id == phc.id).all()
        if att_rows:
            total_present = sum(a.present for a in att_rows)
            total_expected = sum(a.total for a in att_rows)
            if total_expected > 0 and total_present / total_expected < 0.7:
                new_alerts.append(m.Alert(
                    phc_id=phc.id, type="low_attendance", severity="medium",
                    message=(f"{phc.name} staff attendance at "
                             f"{total_present/total_expected*100:.0f}% of roster today."),
                ))

    db.add_all(new_alerts)
    db.commit()

    # redistribution recommendations, per medicine
    new_moves = []
    for med_id, positions in positions_by_medicine.items():
        moves = recommend_redistribution(positions)
        for mv in moves:
            new_moves.append(m.RedistributionRecommendation(
                medicine_id=med_id, from_phc_id=mv.from_phc_id, to_phc_id=mv.to_phc_id,
                suggested_qty=mv.qty,
                reason="Forecast surplus at source vs. projected shortfall at destination "
                       "within procurement lead time.",
            ))
    db.add_all(new_moves)
    db.commit()

    return {
        "medicines_processed": len(medicines),
        "alerts_generated": len(new_alerts),
        "redistribution_moves": len(new_moves),
        "federated_rounds": len(fed_round_log),
    }
