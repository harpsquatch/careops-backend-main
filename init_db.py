"""
Create all tables if they don't exist.
Runs at container startup so it has access to runtime DATABASE_URL.
"""
import os
from database import engine, Base

# Import every model so Base.metadata knows about them
from models import Account, Patient, Visit, Worker  # noqa: F401

# Debug: show which env vars are available
for key in ("DATABASE_URL", "MYSQL_URL", "MYSQL_PRIVATE_URL", "MYSQL_PUBLIC_URL"):
    val = os.getenv(key)
    if val:
        # Mask the password
        safe = val.split("@")[-1] if "@" in val else val
        print(f"  {key} found → ...@{safe}")
    else:
        print(f"  {key} not set")

print(f"Resolved engine: {engine.url.drivername}://{engine.url.host or 'local'}")
Base.metadata.create_all(bind=engine)
print("Tables created:", list(Base.metadata.tables.keys()))
