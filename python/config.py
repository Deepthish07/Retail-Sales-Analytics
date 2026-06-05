"""Configuration management for the Retail Sales Analytics project."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class DatabaseConfig:
    """PostgreSQL database configuration."""
    TYPE = os.getenv("DB_TYPE", "postgresql")
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "5432"))
    NAME = os.getenv("DB_NAME", "retail_analytics")
    USER = os.getenv("DB_USER", "postgres")
    PASSWORD = os.getenv("DB_PASSWORD", "")

    @classmethod
    def connection_string(cls) -> str:
        if cls.TYPE == "sqlite":
            # Use absolute path to avoid CWD issues
            db_path = Paths.BASE / f"{cls.NAME}.db"
            return f"sqlite:///{db_path}"
        return (
            f"postgresql+psycopg2://{cls.USER}:{cls.PASSWORD}"
            f"@{cls.HOST}:{cls.PORT}/{cls.NAME}"
        )


class EmailConfig:
    """SMTP email configuration."""
    SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    PORT = int(os.getenv("SMTP_PORT", "587"))
    USERNAME = os.getenv("SMTP_USERNAME", "")
    PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM = os.getenv("EMAIL_FROM", "analytics@yourcompany.com")
    TO = [addr.strip() for addr in os.getenv("EMAIL_TO", "").split(",") if addr.strip()]


class Paths:
    """Filesystem paths used by the pipeline."""
    BASE = BASE_DIR
    DATA = BASE_DIR / os.getenv("DATA_DIR", "./data")
    REPORTS = BASE_DIR / os.getenv("REPORTS_DIR", "./reports")
    LOGS = BASE_DIR / os.getenv("LOGS_DIR", "./logs")
    RAW_DATA = BASE_DIR / "data" / "raw"
    PROCESSED_DATA = BASE_DIR / "data" / "processed"


class AnalyticsConfig:
    """Analytics thresholds and parameters."""
    FORECAST_MONTHS = int(os.getenv("FORECAST_MONTHS", "3"))
    LOW_SELLER_THRESHOLD = int(os.getenv("LOW_SELLER_THRESHOLD", "10"))
    STOCK_COVERAGE_WARNING_DAYS = int(os.getenv("STOCK_COVERAGE_WARNING_DAYS", "14"))


# Ensure folders exist
for folder in (Paths.DATA, Paths.REPORTS, Paths.LOGS,
               Paths.RAW_DATA, Paths.PROCESSED_DATA):
    folder.mkdir(parents=True, exist_ok=True)
