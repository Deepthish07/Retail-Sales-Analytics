-- ===========================================================
-- KPI Queries - Drop-in queries for ad-hoc reporting
-- ===========================================================

-- 1. Total revenue YTD
SELECT
    SUM(total_amount) AS ytd_revenue,
    SUM(quantity)     AS ytd_units
FROM sales
WHERE sale_date >= DATE_TRUNC('year', CURRENT_DATE);

-- 2. Top 10 products
SELECT p.product_name, SUM(s.total_amount) AS revenue
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.product_name
ORDER BY revenue DESC
LIMIT 10;

-- 3. Products with critical stock (less than 14 days cover)
SELECT product_name, total_stock, avg_daily_sales, days_of_cover
FROM vw_stock_coverage
WHERE days_of_cover IS NOT NULL
  AND days_of_cover < 14
ORDER BY days_of_cover;

-- 4. Category contribution to revenue
SELECT c.category_name,
       SUM(s.total_amount)               AS revenue,
       ROUND(SUM(s.total_amount) * 100.0 /
             (SELECT SUM(total_amount) FROM sales
              WHERE sale_date >= CURRENT_DATE - INTERVAL '90 days'), 2) AS pct
FROM sales s
JOIN products   p ON p.product_id  = s.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE s.sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY c.category_name
ORDER BY revenue DESC;
