@echo off
REM =====================================================
REM  Daily Retail Analytics Pipeline
REM  Schedule via Windows Task Scheduler
REM =====================================================

cd /d "C:\Users\TBS\Automation Projects\RetailSalesAnalytics"

REM Activate your virtual environment (uncomment if applicable)
REM call venv\Scripts\activate

python scripts\run_pipeline.py >> logs\scheduled_run.log 2>&1
