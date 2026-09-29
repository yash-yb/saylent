from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from ..database import get_db
from .. import models as m
from ..schemas import PHCOut, StockLine, ForecastOut, ForecastPoint
from ..ml.forecasting import holt_smoothing, project_forecast, predicted_stockout_date
from ..compute import _series_for

router = APIRouter(prefix="/api/phc", tags=["phc"])


@router.get("", response_model=list[PHCOut])
def list_phcs(db: Session = Depends(get_db)):
    out = []
    today = date.today()
    for p in db.query(m.PHC).all():
        bed_row = (db.query(m.BedStatus).filter(m.BedStatus.phc_id == p.id)
                   .order_by(m.BedStatus.date.desc()).first())
        out.append(PHCOut(
            id=p.id, name=p.name, district_name=p.district.name,
            state_name=p.district.state.name, lat=p.lat, lng=float(p.lng),
            total_beds=p.total_beds, occupied_beds=bed_row.occupied_beds if bed_row else 0,
        ))
    return out


@router.get("/{phc_id}/stock", response_model=list[StockLine])
def phc_stock(phc_id: int, db: Session = Depends(get_db)):
    phc = db.query(m.PHC).get(phc_id)
    if not phc:
        raise HTTPException(404, "PHC not found")

    lines = []
    for stock in db.query(m.MedicineStock).filter(m.MedicineStock.phc_id == phc_id).all():
        series = _series_for(db, phc_id, stock.medicine_id)
        avg_daily = sum(series[-14:]) / 14 if len(series) >= 14 else (sum(series) / len(series) if series else 0)
        days_left = round(stock.current_qty / avg_daily, 1) if avg_daily > 0 else None

        if days_left is not None and days_left <= stock.medicine.procurement_lead_time_days:
            status = "critical"
        elif stock.current_qty <= stock.reorder_level:
            status = "low"
        else:
            status = "healthy"

        lines.append(StockLine(
            medicine_id=stock.medicine_id, medicine_name=stock.medicine.name,
            current_qty=stock.current_qty, reorder_level=stock.reorder_level,
            unit=stock.medicine.unit, days_of_stock_left=days_left, status=status,
        ))
    return lines


@router.get("/{phc_id}/forecast/{medicine_id}", response_model=ForecastOut)
def phc_forecast(phc_id: int, medicine_id: int, db: Session = Depends(get_db)):
    phc = db.query(m.PHC).get(phc_id)
    med = db.query(m.Medicine).get(medicine_id)
    stock = db.query(m.MedicineStock).filter_by(phc_id=phc_id, medicine_id=medicine_id).first()
    if not (phc and med and stock):
        raise HTTPException(404, "PHC/medicine/stock not found")

    latest_round = (db.query(m.FederatedModelRound)
                     .filter(m.FederatedModelRound.medicine_id == medicine_id)
                     .order_by(m.FederatedModelRound.round_number.desc()).first())

    series = _series_for(db, phc_id, medicine_id)
    local = holt_smoothing(series)
    global_slope = latest_round.global_slope if latest_round else None
    forecast_vals = project_forecast(local, horizon_days=14, global_slope=global_slope)

    today = date.today()
    points = [ForecastPoint(date=today.fromordinal(today.toordinal() + i + 1), predicted_demand=round(v, 2))
              for i, v in enumerate(forecast_vals)]
    stockout = predicted_stockout_date(stock.current_qty, forecast_vals, today)

    return ForecastOut(
        phc_id=phc_id, medicine_id=medicine_id, medicine_name=med.name,
        method="Holt linear-trend + federated-averaged global trend blend",
        current_qty=stock.current_qty,
        avg_daily_demand=round(sum(forecast_vals) / len(forecast_vals), 2) if forecast_vals else 0,
        trend_per_day=round(local.trend, 3),
        predicted_stockout_date=stockout,
        forecast=points,
        federated_adjustment_applied=global_slope is not None,
    )
