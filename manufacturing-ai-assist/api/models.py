
from pydantic import BaseModel
from typing import Optional
class SimState(BaseModel):
    eta_offset_days: int = 0
    extra_qty: int = 0
    carrier_upgrade_days: int = 0
    qa_fast_track: bool = False
    resequence: bool = False
    batch_changeovers: bool = False
class KPIResponse(BaseModel):
    throughput_per_day: float
    on_time_pct: float
    defect_rate_pct: float
    downtime_hours: float
    inventory_risk_count: int
    throughput_trend: str
    top_downtime_cause: str
    top_defect_family: str
    lowest_stock_sku: str
    otd_risk_pct: float
    notes: Optional[str] = None
class ApplyActionRequest(BaseModel):
    action: str
    persona: Optional[str] = None
class ApplyActionResponse(BaseModel):
    state: SimState
    message: str
