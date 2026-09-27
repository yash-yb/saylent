from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models as m
from ..schemas import FederatedRoundOut
from ..compute import run_compute_cycle

router = APIRouter(prefix="/api/federated", tags=["federated"])


@router.get("/rounds", response_model=list[FederatedRoundOut])
def latest_rounds(db: Session = Depends(get_db)):
    out = []
    for med in db.query(m.Medicine).all():
        latest = (db.query(m.FederatedModelRound)
                  .filter(m.FederatedModelRound.medicine_id == med.id)
                  .order_by(m.FederatedModelRound.round_number.desc()).first())
        if latest:
            out.append(FederatedRoundOut(
                medicine_name=med.name, round_number=latest.round_number,
                participating_districts=latest.participating_districts,
                global_slope=latest.global_slope, global_intercept=latest.global_intercept,
                created_at=latest.created_at,
            ))
    return out


@router.post("/run-cycle")
def trigger_cycle(db: Session = Depends(get_db)):
    """Manually trigger a full compute cycle: local training -> FedAvg ->
    per-PHC forecast refresh -> alerts -> redistribution recommendations.
    In production this is a nightly scheduled job per nation."""
    return run_compute_cycle(db)
