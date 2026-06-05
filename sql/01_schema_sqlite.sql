-- ===========================================================
-- Retail Sales Analytics - Database Schema (SQLite)
-- ===========================================================

DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS stores;

-- ---------- Categories ----------
CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Stores ----------
CREATE TABLE stores (
    store_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name VARCHAR(150) NOT NULL,
    region     VARCHAR(100),
    city       VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Products ----------
CREATE TABLE products (
    product_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    sku          VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    category_id  INT REFERENCES categories(category_id),
    unit_price   DECIMAL(12, 2) NOT NULL,
    cost_price   DECIMAL(12, 2) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Inventory ----------
CREATE TABLE inventory (
    inventory_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INT REFERENCES products(product_id),
    store_id      INT REFERENCES stores(store_id),
    stock_qty     INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 10,
    last_updated  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, store_id)
);

-- ---------- Sales ----------
CREATE TABLE sales (
    sale_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date   DATE NOT NULL,
    product_id  INT REFERENCES products(product_id),
    store_id    INT REFERENCES stores(store_id),
    quantity    INT NOT NULL CHECK (quantity > 0),
    unit_price  DECIMAL(12, 2) NOT NULL,
    total_amount DECIMAL(14, 2) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_sales_date      ON sales(sale_date);
CREATE INDEX idx_sales_product   ON sales(product_id);
CREATE INDEX idx_sales_store     ON sales(store_id);
CREATE INDEX idx_inventory_prod  ON inventory(product_id);
CREATE INDEX idx_products_cat    ON products(category_id);
