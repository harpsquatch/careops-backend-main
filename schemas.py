from pydantic import BaseModel
from typing import Optional


# ─── Patient ───

class PatientCreate(BaseModel):
    field_name: str
    address: str = ""
    description: str = ""
    lat: float = 0.0
    lng: float = 0.0
    acres: str = "Skilled"
    service_type: int = 1
    scheduled_visits: int = 0
    notes: str = ""
    active: bool = True
    avatar_url: str = ""


class PatientUpdate(BaseModel):
    field_name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    acres: Optional[str] = None
    service_type: Optional[int] = None
    scheduled_visits: Optional[int] = None
    notes: Optional[str] = None
    active: Optional[bool] = None
    avatar_url: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    uid: str
    field_name: str
    address: str
    description: str
    lat: float
    lng: float
    acres: str
    service_type: int
    scheduled_visits: int
    notes: str
    active: bool
    avatar_url: str

    class Config:
        from_attributes = True


# ─── Visit ───

class VisitCreate(BaseModel):
    field_id: int
    text: str = ""
    status: int = 1
    due_date: str = ""


class VisitUpdate(BaseModel):
    id: int
    status: Optional[int] = None
    text: Optional[str] = None
    completed_date: Optional[str] = None


class VisitOut(BaseModel):
    id: int
    uid: str
    field_id: int
    text: str
    status: int
    due_date: str
    completed_date: str

    class Config:
        from_attributes = True


# ─── Worker ───

class WorkerCreate(BaseModel):
    email: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None


class WorkerUpdate(BaseModel):
    uid: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    disabled: Optional[bool] = None


class WorkerOut(BaseModel):
    id: int
    uid: str
    account_uid: str
    full_name: str
    email: str
    avatar: str
    disabled: bool

    class Config:
        from_attributes = True


# ─── Auth ───

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Account ───

class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    notify_days: Optional[int] = None


class AccountOut(BaseModel):
    id: int
    uid: str
    email: str
    account_name: str
    full_name: str
    phone: str
    notify_days: int

    class Config:
        from_attributes = True

