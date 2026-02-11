import os
from dotenv import load_dotenv

load_dotenv()

# MySQL connection — falls back to SQLite for zero-config local dev
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./careops.db",
)

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "careops-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

