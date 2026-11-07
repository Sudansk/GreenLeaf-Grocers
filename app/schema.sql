-- GreenLeaf Grocers Database Schema
PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'cashier')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    cost_price REAL NOT NULL DEFAULT 0.0 CHECK(cost_price >= 0),
    selling_price REAL NOT NULL CHECK(selling_price >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level >= 0),
    expiry_date DATE NOT NULL,
    unit TEXT NOT NULL DEFAULT 'unit',
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales / Invoices Table
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    cashier_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_name TEXT,
    customer_phone TEXT,
    subtotal REAL NOT NULL CHECK(subtotal >= 0),
    discount_percent REAL NOT NULL DEFAULT 0.0 CHECK(discount_percent >= 0 AND discount_percent <= 100),
    discount_amount REAL NOT NULL DEFAULT 0.0 CHECK(discount_amount >= 0),
    tax_amount REAL NOT NULL DEFAULT 0.0 CHECK(tax_amount >= 0),
    grand_total REAL NOT NULL CHECK(grand_total >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('Cash', 'Card', 'UPI', 'Other')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sale Items Table
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    cost_price REAL NOT NULL DEFAULT 0.0 CHECK(cost_price >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    line_total REAL NOT NULL CHECK(line_total >= 0)
);

-- Stock Movement Audit Table
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    movement_type TEXT NOT NULL CHECK(movement_type IN ('SALE', 'RESTOCK', 'ADJUSTMENT_ADD', 'ADJUSTMENT_REMOVE', 'DAMAGE')),
    quantity INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    reference_id TEXT,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high-performance lookups & reports
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_expiry ON products(expiry_date);
CREATE INDEX IF NOT EXISTS idx_products_qty ON products(quantity);
CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_number);
CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_cashier ON sales(cashier_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_movements_created ON stock_movements(created_at);
