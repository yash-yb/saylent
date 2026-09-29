from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from ..database import get_db
from .. import models as m
from ..schemas import NationalSummary, DistrictHealthScore

router = APIRouter(prefix="/api/national", tags=["national"])


@router.get("/summary", response_model=NationalSummary)
def summary(db: Session = Depends(get_db)):
    total_phcs = db.query(m.PHC).count()
    total_districts = db.query(m.District).count()
    total_beds = db.query(func.sum(m.PHC.total_beds)).scalar() or 0

    today = date.today()
    occupied = 0
    for row in db.query(m.BedStatus).filter(m.BedStatus.date == today).all():
        occupied += row.occupied_beds

    active_alerts = db.query(m.Alert).filter(m.Alert.resolved == False).count()  # noqa: E712
    critical_alerts = db.query(m.Alert).filter(
        m.Alert.resolved == False, m.Alert.severity == "critical"  # noqa: E712
    ).count()
    pending_redis = db.query(m.RedistributionRecommendation).filter(
        m.RedistributionRecommendation.status == "pending"
    ).count()
    medicines_at_risk = db.query(m.Alert.medicine_id).filter(
        m.Alert.resolved == False, m.Alert.type == "stockout_risk"  # noqa: E712
    ).distinct().count()

    return NationalSummary(
        total_phcs=total_phcs,
        total_districts=total_districts,
        total_beds=total_beds,
        occupied_beds=occupied,
        bed_occupancy_pct=round((occupied / total_beds * 100) if total_beds else 0, 1),
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
        pending_redistributions=pending_redis,
        medicines_at_risk=medicines_at_risk,
    )


@router.get("/districts", response_model=list[DistrictHealthScore])
def district_scores(db: Session = Depends(get_db)):
    out = []
    today = date.today()
    for d in db.query(m.District).all():
        phc_ids = [p.id for p in d.phcs]
        if not phc_ids:
            continue
        stocks = db.query(m.MedicineStock).filter(m.MedicineStock.phc_id.in_(phc_ids)).all()
        if stocks:
            healthy = sum(1 for s in stocks if s.current_qty > s.reorder_level)
            stock_health_pct = round(healthy / len(stocks) * 100, 1)
        else:
            stock_health_pct = 100.0

        active_alerts = db.query(m.Alert).filter(
            m.Alert.phc_id.in_(phc_ids), m.Alert.resolved == False  # noqa: E712
        ).count()

        beds_total = sum(p.total_beds for p in d.phcs)
        occ = db.query(func.sum(m.BedStatus.occupied_beds)).filter(
            m.BedStatus.phc_id.in_(phc_ids), m.BedStatus.date == today
        ).scalar() or 0
        occ_pct = round((occ / beds_total * 100) if beds_total else 0, 1)

        if stock_health_pct < 60 or active_alerts >= 4:
            status = "critical"
        elif stock_health_pct < 85 or active_alerts >= 1:
            status = "watch"
        else:
            status = "healthy"

        out.append(DistrictHealthScore(
            district_id=d.id, district_name=d.name, state_name=d.state.name,
            phc_count=len(d.phcs), avg_stock_health_pct=stock_health_pct,
            active_alerts=active_alerts, bed_occupancy_pct=occ_pct, status=status,
        ))
    return sorted(out, key=lambda x: x.avg_stock_health_pct)
