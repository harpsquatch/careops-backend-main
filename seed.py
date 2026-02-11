"""
Seed the database with realistic healthcare demo data.
Run:  python seed.py
"""
from database import SessionLocal, engine, Base
from models import Account, Patient, Visit, Worker
from datetime import date, timedelta

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Wipe existing data
for model in [Visit, Worker, Patient, Account]:
    db.query(model).delete()
db.commit()

# ─── Account ───
account = Account(
    uid="1",
    email="admin@careops.io",
    hashed_password="",
    account_name="CareOps Demo",
    full_name="Admin User",
    phone="555-0100",
    notify_days=3,
)
db.add(account)
db.flush()

# ─── Patients ───
patient_data = [
    ("Margaret Thompson", "742 Evergreen Terrace, Springfield, IL",
     "82 y/o, CHF stage III, post-discharge. On Lasix and Lisinopril. Needs daily weight and fluid intake monitoring.",
     39.7817, -89.6501, "Skilled", 1, 8, True),
    ("Robert Chen", "1200 Lakeshore Dr, Chicago, IL",
     "68 y/o, bilateral knee replacement 10 days ago. PT 3x/week. Managing pain with Norco, tapering.",
     41.8827, -87.6233, "Acute", 2, 12, True),
    ("Dorothy Williams", "85 Oak Lane, Peoria, IL",
     "77 y/o, Type 2 diabetic with neuropathy. A1C trending up. Insulin adjustment needed, wound on left heel.",
     40.6936, -89.5890, "Intermediate", 1, 4, True),
    ("James Rivera", "320 Main St, Naperville, IL",
     "55 y/o, C4-C5 spinal cord injury, partial paralysis. Catheter care and pressure ulcer prevention.",
     41.7508, -88.1535, "Skilled", 3, 6, True),
    ("Helen Martinez", "450 Elm Ave, Rockford, IL",
     "91 y/o, advanced dementia with recurrent UTIs. Caregiver burnout risk. Fall precautions in place.",
     42.2711, -89.0940, "Skilled", 6, 10, True),
    ("William Davis", "67 Pine Rd, Champaign, IL",
     "73 y/o, stage IV lung cancer, palliative care. Morphine drip, comfort measures. Family requesting hospice consult.",
     40.1164, -88.2434, "Acute", 4, 8, False),
    ("Patricia Johnson", "1025 Cedar Blvd, Bloomington, IL",
     "64 y/o, COPD exacerbation, on home O2 2L. Nebulizer treatments BID. Smoking cessation counseling ongoing.",
     40.4842, -88.9937, "Skilled", 1, 6, True),
    ("Charles Wilson", "890 Maple Dr, Decatur, IL",
     "70 y/o, post-stroke left hemiparesis. OT/PT in progress. Swallow study cleared for soft diet.",
     39.8403, -88.9548, "Intermediate", 5, 4, True),
]

patients = []
for name, addr, desc, lat, lng, level, stype, sv, active in patient_data:
    p = Patient(
        uid="1",
        field_name=name,
        address=addr,
        description=desc,
        lat=lat, lng=lng,
        acres=level,
        service_type=stype,
        scheduled_visits=sv,
        notes="",
        active=active,
    )
    db.add(p)
    patients.append(p)

db.flush()

# ─── Visits ───
today = date.today()
visit_templates = [
    "Administer medications and check vitals",
    "Wound dressing change and assessment",
    "Physical therapy exercises — lower extremity",
    "Blood pressure monitoring and medication review",
    "Post-surgical incision site inspection",
    "Catheter care and output measurement",
    "Diabetic foot exam and glucose check",
    "Pain management assessment and education",
    "Fall risk evaluation and home safety review",
    "IV therapy and fluid intake tracking",
]

for p in patients:
    for i in range(3):
        due = today + timedelta(days=i * 3 - 2)
        v = Visit(
            uid="1",
            field_id=p.id,
            text=visit_templates[(p.id + i) % len(visit_templates)],
            status=2 if i == 0 else 1,
            due_date=due.isoformat(),
            completed_date=due.isoformat() if i == 0 else "",
        )
        db.add(v)

# ─── Workers ───
worker_data = [
    ("10", "Sarah Mitchell", "sarah.mitchell@careops.io"),
    ("11", "David Park", "david.park@careops.io"),
    ("12", "Maria Gonzalez", "maria.gonzalez@careops.io"),
    ("13", "Kevin O'Brien", "kevin.obrien@careops.io"),
    ("14", "Lisa Nguyen", "lisa.nguyen@careops.io"),
]

for wuid, name, email in worker_data:
    w = Worker(
        uid=wuid,
        account_uid="1",
        full_name=name,
        email=email,
        avatar="",
        disabled=False,
    )
    db.add(w)

db.commit()
db.close()

print("Seeded: 1 account, 8 patients, 24 visits, 5 workers")

