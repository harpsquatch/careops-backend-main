FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Seed the database (creates SQLite DB if no DATABASE_URL is set)
RUN python seed.py

# Railway injects PORT env var
ENV PORT=8000

EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}

