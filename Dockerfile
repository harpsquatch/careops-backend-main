FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Railway injects PORT env var
ENV PORT=8000

EXPOSE ${PORT}

# start.sh: creates tables at runtime (has access to DATABASE_URL), then starts uvicorn
CMD ["./start.sh"]
