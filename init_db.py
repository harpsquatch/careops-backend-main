"""
Create all tables if they don't exist.
Runs at container startup so it has access to runtime DATABASE_URL.
"""
from database import engine, Base

# Import every model so Base.metadata knows about them
from models import Account, Patient, Visit, Worker  # noqa: F401

print(f"Database URL prefix: {engine.url.drivername}")
Base.metadata.create_all(bind=engine)
print("Tables ensured:", list(Base.metadata.tables.keys()))

