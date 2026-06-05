-- ===========================================================
-- Analytical Views for Power BI / Reporting
-- ===========================================================

-- ---------- Top Selling Products (last 90 days) ----------
CREATE OR REPLACE VIEW vw_top_selling_products AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    SUM(s.quantity)              AS units_sold,
    SUM(s.total_amount)          AS revenue,
    SUM(s.total_amount - (pp.cost_price * s.quantity)) AS gross_profit
FROM sales s
JOIN products   p  ON p.product_id  = s.product_id
JOIN categories c  ON c.category_id = p.category_id
WHERE s.sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.product_id, p.sku, p.product_name, c.category_name
ORDER BY revenue DESC;

-- ---------- Low Selling Products (last 90 days) ----------
CREATE OR REPLACE VIEW vw_low_selling_products AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    COALESCE(SUM(s.quantity), 0)     AS units_sold,
    COALESCE(SUM(s.total_amount), 0) AS revenue
FROM products p
JOIN categories c ON c.category_id = p.category_id
LEFT JOIN sales s
       ON s.product_id = p.product_id
      AND s.sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.product_id, p.sku, p.product_name, c.category_name
HAVING COALESCE(SUM(s.quantity), 0) < 50
ORDER BY units_sold ASC;

-- ---------- Stock Coverage ----------
CREATE OR REPLACE VIEW vw_stock_coverage AS
WITH daily_velocity AS (
    SELECT
        product_id,
        AVG(quantity)::NUMERIC(10,2) AS avg_daily_qty
    FROM sales
    WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY product_id
)
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    SUM(i.stock_qty)                              AS total_stock,
    COALESCE(dv.avg_daily_qty, 0)                 AS avg_daily_sales,
    CASE
        WHEN COALESCE(dv.avg_daily_qty, 0) = 0 THEN NULL
        ELSE ROUND(SUM(i.stock_qty) / dv.avg_daily_qty, 1)
    END                                           AS days_of_cover
FROM products p
LEFT JOIN inventory i        ON i.product_id  = p.product_id
LEFT JOIN daily_velocity dv  ON dv.product_id = p.product_id
GROUP BY p.product_id, p.sku, p.product_name, dv.avg_daily_qty
ORDER BY days_of_cover NULLS LAST;

-- ---------- 6-Month Average Sales per product ----------
CREATE OR REPLACE VIEW vw_six_month_avg AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    DATE_TRUNC('month', s.sale_date) AS month,
    SUM(s.quantity)                  AS units_sold,
    SUM(s.total_amount)              AS revenue,
    AVG(SUM(s.total_amount)) OVER (
        PARTITION BY p.product_id
        ORDER BY DATE_TRUNC('month', s.sale_date)
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    )::NUMERIC(12,2)                 AS rolling_6m_avg_revenue
FROM sales s
JOIN products   p ON p.product_id  = s.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE s.sale_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY p.product_id, p.sku, p.product_name, c.category_name,
         DATE_TRUNC('month', s.sale_date)
ORDER BY p.product_id, month;

-- ---------- Monthly revenue trend ----------
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    SUM(total_amount)              AS revenue,
    SUM(quantity)                  AS units_sold,
    COUNT(DISTINCT sale_id)        AS transactions
FROM sales
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY month;
