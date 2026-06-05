# Retail Sales Analytics Project

Complete end-to-end retail sales analytics solution using Python, Pandas, PostgreSQL, and Power BI.

## Project Structure

```
RetailSalesAnalytics/
├── data/                          # CSV data files (raw & processed)
│   ├── raw/                       # Input sales, products, inventory data
│   └── processed/                 # Cleaned data ready for analysis
├── sql/                           # SQL scripts for PostgreSQL
│   ├── 01_schema.sql              # Database schema
│   ├── 02_load_data.sql           # Data loading scripts
│   ├── 03_views.sql               # Analytical views
│   └── 04_kpi_queries.sql         # KPI computation queries
├── python/                        # Python analytics modules
│   ├── config.py                  # Configuration & DB credentials
│   ├── db_connection.py           # PostgreSQL connection handler
│   ├── data_generator.py          # Generate sample sales data
│   ├── etl_pipeline.py            # Extract-Transform-Load pipeline
│   ├── analytics.py               # Core analytics computations
│   ├── forecasting.py             # Sales forecasting module
│   ├── email_summary.py           # Automated email summary
│   └── main.py                    # Main orchestrator
├── powerbi/                       # Power BI files & documentation
│   ├── RetailAnalytics_Dashboard.pdf
│   └── dashboard_measures.dax
├── reports/                       # Generated reports (Excel, CSV, PDF)
├── logs/                          # Application logs
├── scripts/                       # Utility scripts
│   ├── setup_database.py          # One-time DB setup
│   ├── run_pipeline.py            # Run full pipeline
│   └── schedule_daily.bat         # Windows task scheduler script
├── .env.example                   # Environment variables template
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Features

| Feature | Description |
|---------|-------------|
| **Top Selling Products** | Rank products by revenue and units sold |
| **Low Selling Products** | Identify underperformers and slow movers |
| **Stock Coverage** | Days of inventory remaining based on sales velocity |
| **6-Month Average Sales** | Rolling 6-month average per product/category |
| **Forecasting** | Linear regression & seasonal projections (next 3 months) |
| **Automated Email Summary** | Daily executive summary via SMTP |

## Setup

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL and email credentials
   ```

3. **Set up the database**
   ```bash
   python scripts/setup_database.py
   ```

4. **Generate sample data** (optional)
   ```bash
   python python/data_generator.py
   ```

5. **Run the full pipeline**
   ```bash
   python scripts/run_pipeline.py
   ```

6. **Open Power BI**
   - Open `powerbi/RetailAnalytics_Dashboard.pdf` for design reference
   - Connect Power BI Desktop to your PostgreSQL database
   - Import the views from `sql/03_views.sql`

## Business Impact

- Automated sales reporting
- Reduced manual analysis effort
- Enabled inventory monitoring
- Generated sales forecasts
- Automated executive email summaries

## Scheduling

Use `scripts/schedule_daily.bat` with Windows Task Scheduler to run the pipeline daily at a fixed time.

## License

MIT
