"""Main orchestrator - runs the full analytics pipeline end-to-end."""
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import Paths
from db_connection import Database
from analytics import run_all_analytics, export_reports
from forecasting import run_forecasting
from email_summary import dispatch_summary

LOG_FILE = Paths.LOGS / f"pipeline_{datetime.today():%Y%m%d}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pipeline")


def _ytd_kpis() -> dict:
    from config import DatabaseConfig
    if DatabaseConfig.TYPE == "sqlite":
        query = """
            SELECT COALESCE(SUM(total_amount), 0) AS ytd_revenue,
                   COALESCE(SUM(quantity), 0)     AS ytd_units
            FROM sales
            WHERE sale_date >= date('now', 'start of year')
        """
    else:
        query = """
            SELECT COALESCE(SUM(total_amount), 0) AS ytd_revenue,
                   COALESCE(SUM(quantity), 0)     AS ytd_units
            FROM sales
            WHERE sale_date >= DATE_TRUNC('year', CURRENT_DATE)
        """
    row = Database.fetch_df(query).iloc[0]
    return {"ytd_revenue": float(row["ytd_revenue"]),
            "ytd_units":   int(row["ytd_units"])}


def run_full_pipeline(send_email: bool = True) -> dict:
    logger.info("=" * 60)
    logger.info("Starting full analytics pipeline")
    logger.info("=" * 60)

    # 1. Analytics
    logger.info("Step 1/3 - Core analytics")
    analytics = run_all_analytics()
    excel_path = export_reports(analytics["top_sellers"],
                                analytics["low_sellers"],
                                analytics["stock"],
                                analytics["six_month"])

    # 2. Forecasting
    logger.info("Step 2/3 - Forecasting")
    forecasts = run_forecasting()

    # 3. Email summary
    logger.info("Step 3/3 - Email summary")
    kpis = {
        **analytics,
        **forecasts,
        "forecast_total": forecasts["total"],
        **_ytd_kpis(),
    }
    if send_email:
        # Find the most recent xlsx reports
        attachments = sorted(Paths.REPORTS.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)[:2]
        dispatch_summary(kpis, attachments)

    logger.info("Pipeline finished successfully")
    return {"analytics": analytics, "forecasts": forecasts}


if __name__ == "__main__":
    run_full_pipeline(send_email=True)
