"""
Seed the database with realistic healthcare demo data.
Run:  python seed.py
"""
import random
from database import SessionLocal, engine, Base
from models import Account, Patient, Visit, Worker
from auth import hash_password
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
    hashed_password=hash_password("admin123"),
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

# ─── Visit instructions pool ───
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

# ─── Generate 90 days of visit history per patient ───
today = date.today()
rng = random.Random(42)  # deterministic seed for reproducibility

total_visits = 0

for p in patients:
    # Each patient has scheduled_visits per month. Calculate interval in days.
    visits_per_month = p.scheduled_visits or 4
    interval = max(1, round(30 / visits_per_month))

    # Per-patient behavior profile (simulates different quality of care)
    # completion_rate: likelihood a visit gets completed
    # on_time_rate: likelihood a completed visit is on time
    # decline_phase: optional period of declining care (adds realism)
    seed_val = p.id * 31
    prng = random.Random(seed_val)
    base_completion = 0.65 + prng.random() * 0.30   # 65-95%
    base_on_time   = 0.60 + prng.random() * 0.30    # 60-90%
    # Some patients have a "rough patch" mid-period
    rough_start = prng.randint(25, 50)
    rough_end   = rough_start + prng.randint(8, 18)
    rough_penalty = 0.15 + prng.random() * 0.20     # drop 15-35% during rough patch

    # Walk through 90 days and create visits at the expected cadence
    day_offset = 0
    visit_idx = 0
    while day_offset < 90:
        due = today - timedelta(days=89 - day_offset)

        # During rough patch, lower completion and on-time rates
        in_rough = rough_start <= day_offset <= rough_end
        completion_rate = base_completion - (rough_penalty if in_rough else 0)
        on_time_rate = base_on_time - (rough_penalty * 0.5 if in_rough else 0)

        # Determine if visit is completed
        is_future = due > today
        is_completed = (not is_future) and (rng.random() < completion_rate)

        # Determine completion date
        completed_date_str = ""
        if is_completed:
            if rng.random() < on_time_rate:
                # On time: completed on due date or 1 day before
                offset_days = rng.choice([0, 0, 0, -1])
                comp = due + timedelta(days=offset_days)
            else:
                # Late: 1-4 days after due date
                comp = due + timedelta(days=rng.randint(1, 4))
            completed_date_str = comp.isoformat()

        status = 2 if is_completed else 1

        v = Visit(
            uid="1",
            field_id=p.id,
            text=visit_templates[visit_idx % len(visit_templates)],
            status=status,
            due_date=due.isoformat(),
            completed_date=completed_date_str,
        )
        db.add(v)
        total_visits += 1
        visit_idx += 1

        # Add jitter to interval (-1 to +2 days) for realism
        jitter = rng.randint(-1, 2)
        day_offset += max(1, interval + jitter)

    # Also add a few future scheduled visits (next 14 days)
    for fwd in range(1, 15, interval):
        due = today + timedelta(days=fwd)
        v = Visit(
            uid="1",
            field_id=p.id,
            text=visit_templates[(visit_idx + fwd) % len(visit_templates)],
            status=1,
            due_date=due.isoformat(),
            completed_date="",
        )
        db.add(v)
        total_visits += 1

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

print(f"Seeded: 1 account, {len(patients)} patients, {total_visits} visits, {len(worker_data)} workers")
