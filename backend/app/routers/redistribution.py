from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m
from ..schemas import RedistributionOut

router = APIRouter(prefix="/api/redistribution", tags=["redistribution"])


@router.get("", response_model=list[RedistributionOut])
def list_recommendations(status: str = "pending", db: Session = Depends(get_db)):
    q = db.query(m.RedistributionRecommendation)
    if status != "all":
        q = q.filter(m.RedistributionRecommendation.status == status)
    out = []
    for r in q.order_by(m.RedistributionRecommendation.suggested_qty.desc()).all():
        out.append(RedistributionOut(
            id=r.id, medicine_name=r.medicine.name,
            from_phc=r.from_phc.name, from_district=r.from_phc.district.name,
            to_phc=r.to_phc.name, to_district=r.to_phc.district.name,
            suggested_qty=r.suggested_qty, reason=r.reason, status=r.status,
            created_at=r.created_at,
        ))
    return out


@router.post("/{rec_id}/approve")
def approve(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(m.RedistributionRecommendation).get(rec_id)
    if not rec:
        raise HTTPException(404, "Not found")
    rec.status = "approved"
    # move the stock
    from_stock = db.query(m.MedicineStock).filter_by(phc_id=rec.from_phc_id, medicine_id=rec.medicine_id).first()
    to_stock = db.query(m.MedicineStock).filter_by(phc_id=rec.to_phc_id, medicine_id=rec.medicine_id).first()
    if from_stock and to_stock:
        from_stock.current_qty -= rec.suggested_qty
        to_stock.current_qty += rec.suggested_qty
    db.commit()
    return {"ok": True, "status": rec.status}


@router.post("/{rec_id}/reject")
def reject(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(m.RedistributionRecommendation).get(rec_id)
    if not rec:
        raise HTTPException(404, "Not found")
    rec.status = "rejected"
    db.commit()
    return {"ok": True, "status": rec.status}
