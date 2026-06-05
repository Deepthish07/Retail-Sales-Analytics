"""Sales forecasting using simple linear regression and seasonal naive models."""
import logging
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy import text

from config import AnalyticsConfig, Paths
from db_connection import Database

warnings.filterwarnings("ignore", category=UserWarning)
logger = logging.getLogger(__name__)


def _load_monthly_revenue() -> pd.DataFrame:
    from config import DatabaseConfig
    if DatabaseConfig.TYPE == "sqlite":
        query = """
            SELECT strftime('%Y-%m-01', sale_date) AS month,
                   SUM(total_amount)              AS revenue,
                   SUM(quantity)                  AS units_sold
            FROM sales
            WHERE sale_date >= date('now', '-24 months')
            GROUP BY strftime('%Y-%m-01', sale_date)
            ORDER BY month
        """
    else:
        query = """
            SELECT DATE_TRUNC('month', sale_date) AS month,
                   SUM(total_amount)              AS revenue,
                   SUM(quantity)                  AS units_sold
            FROM sales
            WHERE sale_date >= CURRENT_DATE - INTERVAL '24 months'
            GROUP BY DATE_TRUNC('month', sale_date)
            ORDER BY month
        """
    df = Database.fetch_df(query)
    df["month"] = pd.to_datetime(df["month"])
    return df


def _load_product_monthly_revenue() -> pd.DataFrame:
    from config import DatabaseConfig
    if DatabaseConfig.TYPE == "sqlite":
        query = """
            SELECT p.product_id,
                   p.product_name,
                   strftime('%Y-%m-01', s.sale_date) AS month,
                   SUM(s.total_amount)              AS revenue
            FROM sales s
            JOIN products p ON p.product_id = s.product_id
            WHERE s.sale_date >= date('now', '-18 months')
            GROUP BY p.product_id, p.product_name, strftime('%Y-%m-01', s.sale_date)
            ORDER BY p.product_id, month
        """
    else:
        query = """
            SELECT p.product_id,
                   p.product_name,
                   DATE_TRUNC('month', s.sale_date) AS month,
                   SUM(s.total_amount)              AS revenue
            FROM sales s
            JOIN products p ON p.product_id = s.product_id
            WHERE s.sale_date >= CURRENT_DATE - INTERVAL '18 months'
            GROUP BY p.product_id, p.product_name, DATE_TRUNC('month', s.sale_date)
            ORDER BY p.product_id, month
        """
    df = Database.fetch_df(query)
    df["month"] = pd.to_datetime(df["month"])
    return df


def forecast_total_revenue(months_ahead: int = None) -> pd.DataFrame:
    """Forecast total store revenue using a linear trend + monthly seasonality."""
    months_ahead = months_ahead or AnalyticsConfig.FORECAST_MONTHS
    df = _load_monthly_revenue()
    if df.empty or len(df) < 6:
        logger.warning("Not enough data to forecast (need >= 6 months).")
        return pd.DataFrame()

    df = df.set_index("month").asfreq("MS").infer_objects(copy=False).interpolate()

    # Feature engineering: numeric month index + month-of-year dummies
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["revenue"].values
    model = LinearRegression().fit(X, y)

    future_idx = np.arange(len(df), len(df) + months_ahead).reshape(-1, 1)
    forecast   = model.predict(future_idx)

    last_month = df.index.max()
    future_months = pd.date_range(last_month + pd.offsets.MonthBegin(1),
                                  periods=months_ahead, freq="MS")

    forecast_df = pd.DataFrame({
        "month":               future_months,
        "forecast_revenue":    np.round(forecast, 2),
        "lower_bound":         np.round(forecast * 0.90, 2),
        "upper_bound":         np.round(forecast * 1.10, 2),
    })
    logger.info("Total revenue forecast computed for next %d months", months_ahead)
    return forecast_df


def forecast_top_products(top_n: int = 10, months_ahead: int = None) -> pd.DataFrame:
    """Forecast revenue for the top-N products by recent sales."""
    months_ahead = months_ahead or AnalyticsConfig.FORECAST_MONTHS
    df = _load_product_monthly_revenue()
    if df.empty:
        return df

    # Identify top-N products
    cutoff = df["month"].max() - pd.DateOffset(months=3)
    top_ids = (df[df["month"] >= cutoff]
               .groupby("product_id")["revenue"].sum()
               .sort_values(ascending=False).head(top_n).index.tolist())

    forecasts = []
    for pid in top_ids:
        sub = (df[df["product_id"] == pid]
               .set_index("month")
               .asfreq("MS")
               .infer_objects(copy=False)
               .interpolate())
        if len(sub) < 6:
            continue
        X = np.arange(len(sub)).reshape(-1, 1)
        y = sub["revenue"].values
        model  = LinearRegression().fit(X, y)
        future = np.arange(len(sub), len(sub) + months_ahead).reshape(-1, 1)
        pred   = model.predict(future)
        last_m = sub.index.max()
        future_months = pd.date_range(last_m + pd.DateOffset(months=1),
                                      periods=months_ahead, freq="MS")
        for m, p in zip(future_months, pred):
            forecasts.append({
                "product_id":       pid,
                "product_name":     sub["product_name"].iloc[0],
                "forecast_month":   m,
                "forecast_revenue": round(max(p, 0), 2),
            })

    fc = pd.DataFrame(forecasts)
    logger.info("Per-product forecast for top %d products over %d months", top_n, months_ahead)
    return fc


def persist_forecasts(total: pd.DataFrame, per_product: pd.DataFrame) -> None:
    """Store forecasts in PostgreSQL for Power BI to read."""
    with Database.connection() as conn:
        conn.execute(text("DROP TABLE IF EXISTS forecast_total_revenue"))
        conn.execute(text("DROP TABLE IF EXISTS forecast_product_revenue"))
        conn.commit()
    if not total.empty:
        Database.write_df(total, "forecast_total_revenue", if_exists="append")
    if not per_product.empty:
        Database.write_df(per_product, "forecast_product_revenue", if_exists="append")


def save_forecast_excel(total: pd.DataFrame, per_product: pd.DataFrame) -> str:
    out = Paths.REPORTS / f"forecasts_{datetime.today():%Y%m%d}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        total.to_excel(writer, sheet_name="Total_Revenue", index=False)
        per_product.to_excel(writer, sheet_name="Product_Forecast", index=False)
    logger.info("Forecast workbook saved: %s", out)
    return str(out)


def run_forecasting() -> dict:
    total = forecast_total_revenue()
    per   = forecast_top_products()
    persist_forecasts(total, per)
    save_forecast_excel(total, per)
    return {"total": total, "products": per}


if __name__ == "__main__":
    run_forecasting()
