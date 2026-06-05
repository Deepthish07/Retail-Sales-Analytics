"""Core analytics computations: top/low sellers, stock coverage, 6-month averages."""
import logging
from datetime import datetime, timedelta

import pandas as pd

from config import AnalyticsConfig, Paths
from db_connection import Database

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 1. Top Selling Products
# ------------------------------------------------------------------
def top_selling_products(window_days: int = 90, top_n: int = 20) -> pd.DataFrame:
    cutoff = datetime.today() - timedelta(days=window_days)
    query = """
        SELECT p.product_id,
               p.sku,
               p.product_name,
               c.category_name,
               SUM(s.quantity)     AS units_sold,
               SUM(s.total_amount) AS revenue
        FROM sales s
        JOIN products   p ON p.product_id  = s.product_id
        JOIN categories c ON c.category_id = p.category_id
        WHERE s.sale_date >= :cutoff
        GROUP BY p.product_id, p.sku, p.product_name, c.category_name
        ORDER BY revenue DESC
        LIMIT :top_n
    """
    df = Database.fetch_df(query, params={"cutoff": cutoff.date(), "top_n": top_n})
    logger.info("Top %d sellers computed (window=%d days)", top_n, window_days)
    return df


# ------------------------------------------------------------------
# 2. Low Selling Products
# ------------------------------------------------------------------
def low_selling_products(window_days: int = 90) -> pd.DataFrame:
    cutoff = datetime.today() - timedelta(days=window_days)
    threshold = AnalyticsConfig.LOW_SELLER_THRESHOLD
    query = """
        SELECT p.product_id,
               p.sku,
               p.product_name,
               c.category_name,
               COALESCE(SUM(s.quantity), 0)     AS units_sold,
               COALESCE(SUM(s.total_amount), 0) AS revenue
        FROM products p
        JOIN categories c ON c.category_id = p.category_id
        LEFT JOIN sales s
               ON s.product_id = p.product_id
              AND s.sale_date >= :cutoff
        GROUP BY p.product_id, p.sku, p.product_name, c.category_name
        HAVING COALESCE(SUM(s.quantity), 0) < :threshold
        ORDER BY units_sold ASC
    """
    df = Database.fetch_df(query, params={"cutoff": cutoff.date(), "threshold": threshold})
    logger.info("Found %d low selling products", len(df))
    return df


# ------------------------------------------------------------------
# 3. Stock Coverage
# ------------------------------------------------------------------
def stock_coverage() -> pd.DataFrame:
    """Days of inventory remaining given the 30-day sales velocity."""
    from config import DatabaseConfig
    if DatabaseConfig.TYPE == "sqlite":
        query = """
            WITH velocity AS (
                SELECT product_id,
                       SUM(quantity) * 1.0 / 30.0 AS avg_daily_sales
                FROM sales
                WHERE sale_date >= date('now', '-30 days')
                GROUP BY product_id
            )
            SELECT p.product_id,
                   p.sku,
                   p.product_name,
                   c.category_name,
                   COALESCE(SUM(i.stock_qty), 0)             AS total_stock,
                   COALESCE(v.avg_daily_sales, 0)             AS avg_daily_sales,
                   CASE
                       WHEN COALESCE(v.avg_daily_sales, 0) = 0 THEN NULL
                       ELSE ROUND(SUM(i.stock_qty) / v.avg_daily_sales, 1)
                   END                                        AS days_of_cover,
                   CASE
                       WHEN COALESCE(v.avg_daily_sales, 0) = 0 THEN 'NO_SALES'
                       WHEN SUM(i.stock_qty) / v.avg_daily_sales < :warn_days THEN 'CRITICAL'
                       WHEN SUM(i.stock_qty) / v.avg_daily_sales < 30           THEN 'LOW'
                       ELSE 'OK'
                   END                                        AS stock_status
            FROM products p
            JOIN categories c        ON c.category_id = p.category_id
            LEFT JOIN inventory i    ON i.product_id  = p.product_id
            LEFT JOIN velocity v     ON v.product_id  = p.product_id
            GROUP BY p.product_id, p.sku, p.product_name, c.category_name, v.avg_daily_sales
            ORDER BY days_of_cover NULLS LAST
        """
    else:
        query = """
            WITH velocity AS (
                SELECT product_id,
                       SUM(quantity)::NUMERIC / 30.0 AS avg_daily_sales
                FROM sales
                WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY product_id
            )
            SELECT p.product_id,
                   p.sku,
                   p.product_name,
                   c.category_name,
                   COALESCE(SUM(i.stock_qty), 0)             AS total_stock,
                   COALESCE(v.avg_daily_sales, 0)             AS avg_daily_sales,
                   CASE
                       WHEN COALESCE(v.avg_daily_sales, 0) = 0 THEN NULL
                       ELSE ROUND(SUM(i.stock_qty) / v.avg_daily_sales, 1)
                   END                                        AS days_of_cover,
                   CASE
                       WHEN COALESCE(v.avg_daily_sales, 0) = 0 THEN 'NO_SALES'
                       WHEN SUM(i.stock_qty) / v.avg_daily_sales < :warn_days THEN 'CRITICAL'
                       WHEN SUM(i.stock_qty) / v.avg_daily_sales < 30           THEN 'LOW'
                       ELSE 'OK'
                   END                                        AS stock_status
            FROM products p
            JOIN categories c        ON c.category_id = p.category_id
            LEFT JOIN inventory i    ON i.product_id  = p.product_id
            LEFT JOIN velocity v     ON v.product_id  = p.product_id
            GROUP BY p.product_id, p.sku, p.product_name, c.category_name, v.avg_daily_sales
            ORDER BY days_of_cover NULLS LAST
        """
    df = Database.fetch_df(query, params={"warn_days": AnalyticsConfig.STOCK_COVERAGE_WARNING_DAYS})
    logger.info("Stock coverage computed for %d products", len(df))
    return df


# ------------------------------------------------------------------
# 4. 6-Month Average Sales
# ------------------------------------------------------------------
def six_month_average() -> pd.DataFrame:
    """Per-product rolling 6-month revenue average using Pandas."""
    from config import DatabaseConfig
    if DatabaseConfig.TYPE == "sqlite":
        query = """
            SELECT s.sale_date,
                   p.product_id,
                   p.product_name,
                   c.category_name,
                   s.quantity,
                   s.total_amount
            FROM sales s
            JOIN products   p ON p.product_id  = s.product_id
            JOIN categories c ON c.category_id = p.category_id
            WHERE s.sale_date >= date('now', '-12 months')
        """
    else:
        query = """
            SELECT s.sale_date,
                   p.product_id,
                   p.product_name,
                   c.category_name,
                   s.quantity,
                   s.total_amount
            FROM sales s
            JOIN products   p ON p.product_id  = s.product_id
            JOIN categories c ON c.category_id = p.category_id
            WHERE s.sale_date >= CURRENT_DATE - INTERVAL '12 months'
        """
    df = Database.fetch_df(query)
    if df.empty:
        return df

    df["sale_date"] = pd.to_datetime(df["sale_date"])
    monthly = (
        df.groupby([df["sale_date"].dt.to_period("M"), "product_id", "product_name", "category_name"])
          .agg(units_sold=("quantity", "sum"),
               revenue=("total_amount", "sum"))
          .reset_index()
          .rename(columns={"sale_date": "month"})
    )
    monthly["month"] = monthly["month"].dt.to_timestamp()
    monthly = monthly.sort_values(["product_id", "month"])
    monthly["rolling_6m_avg_revenue"] = (
        monthly.groupby("product_id")["revenue"]
               .transform(lambda s: s.rolling(6, min_periods=1).mean())
               .round(2)
    )
    logger.info("6-month rolling average computed for %d product-months", len(monthly))
    return monthly


# ------------------------------------------------------------------
# Save all reports to Excel (one workbook, multiple sheets)
# ------------------------------------------------------------------
def export_reports(top: pd.DataFrame, low: pd.DataFrame,
                   stock: pd.DataFrame, avg6: pd.DataFrame) -> str:
    out = Paths.REPORTS / f"retail_analytics_{datetime.today():%Y%m%d}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        top.to_excel(writer,  sheet_name="Top_Sellers",      index=False)
        low.to_excel(writer,  sheet_name="Low_Sellers",      index=False)
        stock.to_excel(writer, sheet_name="Stock_Coverage",  index=False)
        avg6.to_excel(writer, sheet_name="6M_Average",       index=False)
    logger.info("Exported analytics workbook to %s", out)
    return str(out)


def run_all_analytics() -> dict:
    return {
        "top_sellers":  top_selling_products(),
        "low_sellers":  low_selling_products(),
        "stock":        stock_coverage(),
        "six_month":    six_month_average(),
    }


if __name__ == "__main__":
    res = run_all_analytics()
    export_reports(res["top_sellers"], res["low_sellers"],
                   res["stock"], res["six_month"])
