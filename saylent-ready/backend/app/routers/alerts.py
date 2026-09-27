from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import models as m
from ..schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    severity: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    district_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(m.Alert).filter(m.Alert.resolved == False)  # noqa: E712
    if severity:
        q = q.filter(m.Alert.severity == severity)
    if type:
        q = q.filter(m.Alert.type == type)
    alerts = q.order_by(m.Alert.severity.desc(), m.Alert.created_at.desc()).all()

    out = []
    for a in alerts:
        if district_id and a.phc.district_id != district_id:
            continue
        out.append(AlertOut(
            id=a.id, phc_id=a.phc_id, phc_name=a.phc.name,
            district_name=a.phc.district.name, type=a.type,
            medicine_name=a.medicine.name if a.medicine else None,
            severity=a.severity, message=a.message, predicted_date=a.predicted_date,
            created_at=a.created_at, resolved=a.resolved,
        ))
    return out


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(m.Alert).get(alert_id)
    if alert:
        alert.resolved = True
        db.commit()
    return {"ok": True}
