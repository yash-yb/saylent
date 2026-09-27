from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class NationalSummary(BaseModel):
    total_phcs: int
    total_districts: int
    total_beds: int
    occupied_beds: int
    bed_occupancy_pct: float
    active_alerts: int
    critical_alerts: int
    pending_redistributions: int
    medicines_at_risk: int


class DistrictHealthScore(BaseModel):
    district_id: int
    district_name: str
    state_name: str
    phc_count: int
    avg_stock_health_pct: float
    active_alerts: int
    bed_occupancy_pct: float
    status: str  # healthy | watch | critical


class PHCOut(BaseModel):
    id: int
    name: str
    district_name: str
    state_name: str
    lat: float
    lng: float
    total_beds: int
    occupied_beds: int

    class Config:
        from_attributes = True


class StockLine(BaseModel):
    medicine_id: int
    medicine_name: str
    current_qty: float
    reorder_level: float
    unit: str
    days_of_stock_left: Optional[float] = None
    status: str


class ForecastPoint(BaseModel):
    date: date
    predicted_demand: float


class ForecastOut(BaseModel):
    phc_id: int
    medicine_id: int
    medicine_name: str
    method: str
    current_qty: float
    avg_daily_demand: float
    trend_per_day: float
    predicted_stockout_date: Optional[date]
    forecast: List[ForecastPoint]
    federated_adjustment_applied: bool


class AlertOut(BaseModel):
    id: int
    phc_id: int
    phc_name: str
    district_name: str
    type: str
    medicine_name: Optional[str]
    severity: str
    message: str
    predicted_date: Optional[date]
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True


class RedistributionOut(BaseModel):
    id: int
    medicine_name: str
    from_phc: str
    from_district: str
    to_phc: str
    to_district: str
    suggested_qty: float
    reason: str
    status: str
    created_at: datetime


class FederatedRoundOut(BaseModel):
    medicine_name: str
    round_number: int
    participating_districts: int
    global_slope: float
    global_intercept: float
    created_at: datetime
