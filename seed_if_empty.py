"""
Seed the database ONLY if the accounts table is empty.
This prevents re-seeding on every container restart while ensuring
first-time deployments get demo data.
"""
from database import SessionLocal
from models import Account

db = SessionLocal()

try:
    count = db.query(Account).count()
    if count == 0:
        print("Database is empty — running full seed...")
        db.close()
        # Import and execute seed.py
        exec(open("seed.py").read())
    else:
        print(f"Database already has {count} account(s) — skipping seed.")
finally:
    db.close()

