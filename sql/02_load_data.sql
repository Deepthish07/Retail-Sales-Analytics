-- ===========================================================
-- Sample seed data
-- ===========================================================

INSERT INTO categories (category_name) VALUES
    ('Electronics'),
    ('Clothing'),
    ('Groceries'),
    ('Home & Kitchen'),
    ('Sports & Outdoors');

INSERT INTO stores (store_name, region, city) VALUES
    ('Downtown Flagship', 'North',   'New York'),
    ('Mall Central',     'East',    'Boston'),
    ('Westgate Outlet',  'West',    'Los Angeles'),
    ('South Plaza',      'South',   'Houston');

INSERT INTO products (sku, product_name, category_id, unit_price, cost_price) VALUES
    ('EL-001', 'Wireless Headphones',  1, 89.99,  35.00),
    ('EL-002', '4K Smart TV 55"',      1, 599.00, 380.00),
    ('EL-003', 'Bluetooth Speaker',    1, 49.50,  18.00),
    ('CL-001', 'Men''s Running Shoes', 2, 79.99,  32.00),
    ('CL-002', 'Women''s Jacket',      2, 129.00, 55.00),
    ('CL-003', 'Cotton T-Shirt',       2, 19.99,   6.50),
    ('GR-001', 'Organic Coffee Beans', 3, 14.99,   5.00),
    ('GR-002', 'Premium Olive Oil',    3, 24.50,   9.00),
    ('HK-001', 'Stainless Cookware',   4, 199.00, 85.00),
    ('HK-002', 'Memory Foam Pillow',   4, 39.99,  12.00),
    ('SP-001', 'Yoga Mat',             5, 29.99,   9.50),
    ('SP-002', 'Dumbbell Set 20kg',    5, 89.00,  42.00);

-- Inventory seed
INSERT INTO inventory (product_id, store_id, stock_qty, reorder_level)
SELECT p.product_id, s.store_id,
       CASE WHEN p.sku LIKE 'EL-002' THEN 5  -- low stock for demo
            WHEN p.sku LIKE 'CL-003' THEN 50
            ELSE 100 END,
       20
FROM products p CROSS JOIN stores s;
