"""One-time database setup: create schema, load seed data, and create views."""
import logging
import sys
from pathlib import Path

# Add project root to path so we can import python modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from db_connection import Database  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("setup")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def run_script(filename: str) -> None:
    logger.info("Executing %s ...", filename)
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    Database.execute_script(sql)


def main() -> None:
    from config import DatabaseConfig
    schema_file = "01_schema.sql"
    views_file = "03_views.sql"
    if DatabaseConfig.TYPE == "sqlite":
        schema_file = "01_schema_sqlite.sql"
        views_file = "03_views_sqlite.sql"

    run_script(schema_file)
    run_script("02_load_data.sql")
    run_script(views_file)
    logger.info("Database setup complete.")


if __name__ == "__main__":
    main()
