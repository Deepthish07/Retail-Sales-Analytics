"""Generate and send an automated HTML email summary."""
import logging
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable

import pandas as pd

from config import EmailConfig, Paths

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# HTML rendering
# ------------------------------------------------------------------
def _df_to_table(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Render a small DataFrame as a styled HTML table."""
    if df.empty:
        return "<p><em>No data available.</em></p>"
    head = df.head(max_rows).copy()
    return head.to_html(index=False, border=0, classes="data", float_format="%.2f")


def build_html(kpis: dict) -> str:
    """Compose the email HTML body using the analytics KPIs."""
    top = kpis["top_sellers"]
    low = kpis["low_sellers"]
    stock = kpis["stock"]
    forecast = kpis["forecast_total"]

    ytd_revenue = kpis.get("ytd_revenue", 0)
    ytd_units   = kpis.get("ytd_units", 0)
    critical_stock = stock[stock["stock_status"] == "CRITICAL"] if not stock.empty else stock

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            h1   {{ color: #2c3e50; }}
            h2   {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 4px; }}
            .kpi-row {{ display: flex; gap: 20px; margin: 20px 0; }}
            .kpi     {{ background: #3498db; color: white; padding: 16px; border-radius: 8px;
                        flex: 1; text-align: center; }}
            .kpi h3  {{ margin: 0; font-size: 14px; }}
            .kpi p   {{ font-size: 22px; margin: 6px 0 0; font-weight: bold; }}
            table.data {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
            table.data th, table.data td {{ border: 1px solid #ddd; padding: 6px 8px;
                                            text-align: left; font-size: 13px; }}
            table.data th {{ background: #f4f6f8; }}
            .footer {{ color: #95a5a6; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>📊 Daily Retail Sales Summary</h1>
        <p>Report generated on <b>{datetime.today():%Y-%m-%d %H:%M}</b></p>

        <div class="kpi-row">
            <div class="kpi"><h3>YTD Revenue</h3><p>${ytd_revenue:,.0f}</p></div>
            <div class="kpi"><h3>YTD Units Sold</h3><p>{ytd_units:,.0f}</p></div>
            <div class="kpi"><h3>Critical SKUs</h3><p>{len(critical_stock)}</p></div>
        </div>

        <h2>🏆 Top 10 Selling Products (last 90 days)</h2>
        {_df_to_table(top, 10)}

        <h2>⚠️ Low Selling Products</h2>
        {_df_to_table(low, 10)}

        <h2>📦 Critical Stock Coverage</h2>
        {_df_to_table(critical_stock, 10)}

        <h2>📈 Revenue Forecast (next 3 months)</h2>
        {_df_to_table(forecast, 5)}

        <p class="footer">This is an automated message from the Retail Analytics pipeline.</p>
    </body>
    </html>
    """
    return html


# ------------------------------------------------------------------
# SMTP delivery
# ------------------------------------------------------------------
def send_email(subject: str, html_body: str,
               attachments: Iterable[Path] = (),
               to_addrs: list = None) -> None:
    msg = MIMEMultipart()
    msg["From"]    = EmailConfig.FROM
    msg["To"]      = ", ".join(to_addrs or EmailConfig.TO)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    for path in attachments or []:
        if not Path(path).exists():
            continue
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), Name=Path(path).name)
        part["Content-Disposition"] = f'attachment; filename="{Path(path).name}"'
        msg.attach(part)

    try:
        with smtplib.SMTP(EmailConfig.SERVER, EmailConfig.PORT) as server:
            server.starttls()
            server.login(EmailConfig.USERNAME, EmailConfig.PASSWORD)
            server.send_message(msg)
        logger.info("Summary email sent to %s", msg["To"])
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)


def dispatch_summary(kpis: dict, attachments: Iterable[Path] = ()) -> None:
    subject = f"[Retail Analytics] Daily Summary - {datetime.today():%Y-%m-%d}"
    html    = build_html(kpis)
    send_email(subject, html, attachments)
