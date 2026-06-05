"""Generate realistic sample sales data for testing and demos."""
import logging
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from config import Paths
from db_connection import Database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def generate_sales_history(months: int = 18, seed: int = 42) -> pd.DataFrame:
    """Create daily transactional sales rows spanning `months` months."""
    random.seed(seed)
    np.random.seed(seed)

    # Read existing products & stores from the DB
    products = Database.fetch_df("SELECT product_id, unit_price FROM products")
    stores   = Database.fetch_df("SELECT store_id FROM stores")

    if products.empty or stores.empty:
        raise RuntimeError("Products and stores tables must be populated first.")

    end_date   = date.today()
    start_date = end_date - timedelta(days=months * 30)
    date_range = pd.date_range(start_date, end_date, freq="D")

    rows = []
    for d in date_range:
        # Weekend boost + slow start of the year seasonality
        dow_factor = 1.3 if d.weekday() >= 5 else 1.0
        season     = 1.0 + 0.15 * np.sin(2 * np.pi * d.dayofyear / 365)
        for _, p in products.iterrows():
            base = 0.5 if p["product_id"] % 4 == 0 else 3
            for _, s in stores.iterrows():
                if random.random() < 0.55:  # not every product sells every day everywhere
                    qty = max(1, int(np.random.poisson(base) * dow_factor * season))
                    rows.append({
                        "sale_date":     d.date(),
                        "product_id":    int(p["product_id"]),
                        "store_id":      int(s["store_id"]),
                        "quantity":      qty,
                        "unit_price":    float(p["unit_price"]),
                        "total_amount":  round(qty * float(p["unit_price"]), 2),
                    })
    df = pd.DataFrame(rows)
    logger.info("Generated %d sales rows from %s to %s", len(df), start_date, end_date)
    return df


def persist_sales(df: pd.DataFrame) -> None:
    """Write the generated sales data into PostgreSQL."""
    Database.write_df(df, "sales", if_exists="append")
    out = Paths.RAW_DATA / "sales_history.csv"
    df.to_csv(out, index=False)
    logger.info("Sales history saved to %s", out)


if __name__ == "__main__":
    sales = generate_sales_history(months=18)
    persist_sales(sales)
