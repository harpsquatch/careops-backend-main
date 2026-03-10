import os
from dotenv import load_dotenv

load_dotenv()


def _resolve_database_url() -> str:
    """
    Resolve the database URL from environment variables.
    Railway MySQL addon exposes MYSQL_URL / MYSQL_PRIVATE_URL / MYSQL_PUBLIC_URL,
    NOT DATABASE_URL.  We check all of them and normalise the dialect for SQLAlchemy.
    """
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("MYSQL_URL")
        or os.getenv("MYSQL_PRIVATE_URL")
        or os.getenv("MYSQL_PUBLIC_URL")
        or ""
    )

    if url:
        # Railway gives  mysql://user:pass@host:port/db
        # SQLAlchemy + PyMySQL needs  mysql+pymysql://user:pass@host:port/db
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url

    # Local dev fallback
    return "sqlite:///./careops.db"


DATABASE_URL = _resolve_database_url()

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "careops-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
