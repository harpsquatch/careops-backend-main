#!/bin/sh
set -e

echo "── Initialising database tables ──"
python init_db.py

echo "── Starting uvicorn ──"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

