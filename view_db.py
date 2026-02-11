#!/usr/bin/env python3
"""
Quick script to view database contents.
Run: python view_db.py
"""
from database import SessionLocal
from models import Account, Patient, Visit, Worker

db = SessionLocal()

print("=" * 60)
print("ACCOUNTS")
print("=" * 60)
accounts = db.query(Account).all()
for acc in accounts:
    print(f"ID: {acc.id}, UID: {acc.uid}, Email: {acc.email}, Name: {acc.account_name}")

print("\n" + "=" * 60)
print("PATIENTS")
print("=" * 60)
patients = db.query(Patient).all()
for p in patients:
    print(f"ID: {p.id}, Name: {p.field_name}, Address: {p.address[:50] if p.address else 'N/A'}")
    print(f"  Description: {p.description[:50] if p.description else 'N/A'}")
    print(f"  Avatar URL: {p.avatar_url[:50] if p.avatar_url else 'N/A'}")
    print(f"  Active: {p.active}, Lat: {p.lat}, Lng: {p.lng}")

print("\n" + "=" * 60)
print("VISITS")
print("=" * 60)
visits = db.query(Visit).all()
for v in visits:
    print(f"ID: {v.id}, Patient ID: {v.field_id}, Status: {v.status}, Due: {v.due_date}")
    print(f"  Text: {v.text[:50] if v.text else 'N/A'}")

print("\n" + "=" * 60)
print("WORKERS")
print("=" * 60)
workers = db.query(Worker).all()
for w in workers:
    print(f"ID: {w.id}, UID: {w.uid}, Name: {w.full_name}, Email: {w.email}, Disabled: {w.disabled}")

db.close()

