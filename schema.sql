PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    product_id     INTEGER PRIMARY KEY,
    model_name     TEXT NOT NULL,
    collection     TEXT NOT NULL,      -- Raga, Edge, Nebula, Octane ...
    gender         TEXT NOT NULL,      -- Men / Women / Unisex
    strap          TEXT NOT NULL,      -- Leather / Metal / Silicone
    movement       TEXT NOT NULL,      -- Analog / Smart / Automatic
    mrp            REAL NOT NULL,
    launch_year    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS stores (
    store_id    INTEGER PRIMARY KEY,
    city        TEXT NOT NULL,
    region      TEXT NOT NULL,
    channel     TEXT NOT NULL          -- World of Titan / Mall / Online
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    store_id       INTEGER NOT NULL REFERENCES stores(store_id),
    sale_date      TEXT NOT NULL,      -- YYYY-MM-DD
    quantity       INTEGER NOT NULL,
    discount_pct   REAL NOT NULL,
    selling_price  REAL NOT NULL,
    revenue        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sales_date    ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_store   ON sales(store_id);
