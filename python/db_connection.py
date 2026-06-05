"""PostgreSQL connection handler."""
import logging
from contextlib import contextmanager
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DatabaseConfig

logger = logging.getLogger(__name__)


class Database:
    """Manages a singleton SQLAlchemy engine and provides helper methods."""

    _engine: Optional[Engine] = None

    @classmethod
    def get_engine(cls) -> Engine:
        if cls._engine is None:
            connection_string = DatabaseConfig.connection_string()
            logger.info("Creating database engine for %s", DatabaseConfig.HOST)
            cls._engine = create_engine(connection_string, pool_pre_ping=True, pool_size=5)
        return cls._engine

    @classmethod
    @contextmanager
    def connection(cls):
        engine = cls.get_engine()
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def execute_script(cls, script: str) -> None:
        """Execute a multi-statement SQL script."""
        with cls.connection() as conn:
            trans = conn.begin()
            try:
                for statement in [s.strip() for s in script.split(";") if s.strip()]:
                    conn.execute(text(statement))
                trans.commit()
                logger.info("Script executed successfully")
            except Exception:
                trans.rollback()
                raise

    @classmethod
    def fetch_df(cls, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        return pd.read_sql(query, cls.get_engine(), params=params)

    @classmethod
    def write_df(cls, df: pd.DataFrame, table: str, if_exists: str = "append") -> None:
        df.to_sql(table, cls.get_engine(), if_exists=if_exists, index=False)
        logger.info("Wrote %d rows to %s", len(df), table)
