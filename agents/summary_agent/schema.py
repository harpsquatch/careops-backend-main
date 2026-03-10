from typing import List, Optional

from pydantic import BaseModel


class RiskItem(BaseModel):
    level: str
    message: str


class NextVisit(BaseModel):
    due_date: Optional[str] = None
    text: Optional[str] = None


class PatientSummaryOutput(BaseModel):
    patient_id: int
    patient_name: str
    status_summary: str
    care_level: str
    description: str
    adherence_30d: float
    total_visits: int
    completed_count: int
    pending_count: int
    overdue_count: int
    upcoming_count: int
    cadence: str
    risks: List[RiskItem]
    next_visit: Optional[NextVisit] = None
    actions: List[str]
    insights: str


class AgentStepTrace(BaseModel):
    step: str
    status: str
    detail: str


class AgentTrace(BaseModel):
    trace_id: str
    steps: List[AgentStepTrace]
    fallback_used: bool = False

