from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey
from database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(64), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    account_name = Column(String(255), default="")
    full_name = Column(String(255), default="")
    phone = Column(String(50), default="")
    notify_days = Column(Integer, default=3)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(64), index=True)          # owner account uid
    field_name = Column(String(255), default="")   # patient name
    address = Column(String(500), default="")
    description = Column(String(500), default="")   # short clinical summary
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    acres = Column(String(100), default="Skilled")  # care level
    service_type = Column(Integer, default=1)
    scheduled_visits = Column(Integer, default=0)
    notes = Column(Text, default="")
    active = Column(Boolean, default=True)


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(64), index=True)           # owner account uid
    field_id = Column(Integer, ForeignKey("patients.id"), index=True)
    text = Column(Text, default="")                # visit instructions
    status = Column(Integer, default=1)            # 1=pending, 2=completed
    due_date = Column(String(20), default="")
    completed_date = Column(String(20), default="")


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(64), unique=True, index=True)
    account_uid = Column(String(64), index=True)   # owner account uid
    full_name = Column(String(255), default="")
    email = Column(String(255), default="")
    avatar = Column(String(500), default="")
    disabled = Column(Boolean, default=False)

