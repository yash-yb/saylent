from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Nation(Base):
    """BRICS member nation — top level of the federation. Each nation's
    data stays inside its own DB instance in a real deployment; this demo
    keeps them in one DB but partitioned by nation_id to model that boundary."""
    __tablename__ = "nations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    code = Column(String, unique=True)  # ISO code e.g. IN, BR, ZA, RU, CN

    states = relationship("State", back_populates="nation")


class State(Base):
    __tablename__ = "states"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    nation_id = Column(Integer, ForeignKey("nations.id"))

    nation = relationship("Nation", back_populates="states")
    districts = relationship("District", back_populates="state")


class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"))
    population = Column(Integer, default=0)

    state = relationship("State", back_populates="districts")
    phcs = relationship("PHC", back_populates="district")


class PHC(Base):
    """Primary Health Centre — the ground-truth reporting unit."""
    __tablename__ = "phcs"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    district_id = Column(Integer, ForeignKey("districts.id"))
    lat = Column(Float)
    lng = Column(String)
    total_beds = Column(Integer, default=20)

    district = relationship("District", back_populates="phcs")
    stocks = relationship("MedicineStock", back_populates="phc")


class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    unit = Column(String, default="units")
    procurement_lead_time_days = Column(Integer, default=7)
    critical = Column(Boolean, default=False)


class MedicineStock(Base):
    """Current on-hand quantity at a PHC, kept up to date by ingest events."""
    __tablename__ = "medicine_stocks"
    id = Column(Integer, primary_key=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    current_qty = Column(Float, default=0)
    reorder_level = Column(Float, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    phc = relationship("PHC", back_populates="stocks")
    medicine = relationship("Medicine")


class ConsumptionLog(Base):
    """Daily dispensed quantity — the time series forecasting trains on."""
    __tablename__ = "consumption_logs"
    id = Column(Integer, primary_key=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    date = Column(Date)
    qty_dispensed = Column(Float)


class BedStatus(Base):
    __tablename__ = "bed_status"
    id = Column(Integer, primary_key=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"))
    date = Column(Date)
    occupied_beds = Column(Integer)


class PersonnelAttendance(Base):
    __tablename__ = "personnel_attendance"
    id = Column(Integer, primary_key=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"))
    date = Column(Date)
    role = Column(String)  # doctor / nurse / pharmacist / support
    present = Column(Integer)
    total = Column(Integer)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    phc_id = Column(Integer, ForeignKey("phcs.id"))
    type = Column(String)  # stockout_risk | low_bed_capacity | low_attendance
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)
    severity = Column(String)  # low | medium | high | critical
    message = Column(Text)
    predicted_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)

    phc = relationship("PHC")
    medicine = relationship("Medicine")


class RedistributionRecommendation(Base):
    __tablename__ = "redistribution_recommendations"
    id = Column(Integer, primary_key=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    from_phc_id = Column(Integer, ForeignKey("phcs.id"))
    to_phc_id = Column(Integer, ForeignKey("phcs.id"))
    suggested_qty = Column(Float)
    reason = Column(Text)
    status = Column(String, default="pending")  # pending | approved | rejected | completed
    created_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine")
    from_phc = relationship("PHC", foreign_keys=[from_phc_id])
    to_phc = relationship("PHC", foreign_keys=[to_phc_id])


class FederatedModelRound(Base):
    """Audit trail of federated-learning rounds: which districts
    participated and the resulting aggregated (global) model, so the
    platform never has to expose a district's raw consumption data to
    prove the model was trained fairly."""
    __tablename__ = "federated_rounds"
    id = Column(Integer, primary_key=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    round_number = Column(Integer)
    participating_districts = Column(Integer)
    global_slope = Column(Float)
    global_intercept = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
