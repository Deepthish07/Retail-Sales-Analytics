"""ETL pipeline: extract from PostgreSQL, transform, save processed data."""
import logging
from datetime import datetime, timedelta

import pandas as pd

from config import Paths
from db_connection import Database

logger = logging.getLogger(__name__)


def extract_sales(days_back: int = 730) -> pd.DataFrame:
    """Pull sales rows for the requested look-back window."""
    cutoff = (datetime.today() - timedelta(days=days_back)).date()
    query = """
        SELECT s.sale_date,
               s.product_id,
               s.store_id,
               s.quantity,
               s.unit_price,
               s.total_amount,
               p.sku,
               p.product_name,
               p.category_id,
               c.category_name
        FROM sales s
        JOIN products   p ON p.product_id  = s.product_id
        JOIN categories c ON c.category_id = p.category_id
        WHERE s.sale_date >= :cutoff
    """
    df = Database.fetch_df(query, params={"cutoff": cutoff})
    logger.info("Extracted %d sales rows since %s", len(df), cutoff)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich sales data."""
    if df.empty:
        return df

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["month"]     = df["sale_date"].dt.to_period("M").dt.to_timestamp()
    df["year"]      = df["sale_date"].dt.year
    df["weekday"]   = df["sale_date"].dt.day_name()

    # Add cost & gross margin using assumed 60 % cost ratio when missing
    df["cost_amount"]   = (df["total_amount"] * 0.60).round(2)
    df["gross_profit"]  = (df["total_amount"] - df["cost_amount"]).round(2)

    df = df.drop_duplicates()
    df = df[df["quantity"] > 0]
    logger.info("Transformed dataset shape: %s", df.shape)
    return df


def save_processed(df: pd.DataFrame) -> None:
    out = Paths.PROCESSED_DATA / "sales_clean.parquet"
    df.to_parquet(out, index=False)
    df.to_csv(out.with_suffix(".csv"), index=False)
    logger.info("Saved processed data to %s", out)


def run_etl() -> pd.DataFrame:
    raw = extract_sales()
    clean = transform(raw)
    save_processed(clean)
    return clean


if __name__ == "__main__":
    run_etl()
