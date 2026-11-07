# GreenLeaf Grocers – Inventory & Sales Management System with Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Data%20Analysis-Pandas-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Visualization-Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com/)
[![Bootstrap 5](https://img.shields.io/badge/UI-Bootstrap%205-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Pytest](https://img.shields.io/badge/Tests-39%20Passed-2ba02e?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)

A production-ready, full-stack inventory, Point of Sale (POS), and business analytics system built with **Python Flask**, **SQLite**, **Pandas**, **Plotly**, and **Bootstrap 5**.

Designed specifically for modern grocery and supermarket operations, **GreenLeaf Grocers** combines real-time inventory tracking, role-based security, atomic POS billing transactions, automated perishables expiry alerts, low-stock notifications, and deep sales intelligence.

---

## 📸 Screenshots & UI Showcase

> Place your application screenshots in the [`docs/screenshots/`](docs/screenshots/) directory.

### 1. Executive Analytics Dashboard
Comprehensive business intelligence featuring real-time KPI metric cards, daily revenue trends, top 10 selling products, category-wise revenue share, and slow-moving stock identification.
```
+----------------------------------------------------------------------------------------------------+
|  TOTAL REVENUE       TOTAL SALES        AVG BILL VALUE     TOTAL PRODUCTS     LOW STOCK   TURNOVER |
|   $1,852.60              86                 $21.54               39               6         1.84x  |
+----------------------------------------------------------------------------------------------------+
| [ Daily Revenue & Volume (Plotly Chart) ]     | [ Top 10 Best Selling Products (Bar Chart) ]       |
+----------------------------------------------------------------------------------------------------+
| [ Category Revenue Distribution (Donut) ]     | [ Slow-Moving Inventory Alert (<= 2 sales / 30d) ] |
+----------------------------------------------------------------------------------------------------+
```
*(Preview image: `docs/screenshots/dashboard.png`)*

### 2. Point of Sale (POS) Billing Terminal
High-speed checkout interface equipped with live SKU/name search, category filters, interactive cart calculations, discount adjustments, and printable tax invoice generation.
*(Preview image: `docs/screenshots/pos_terminal.png`)*

### 3. Inventory Control & Perishables Monitoring
Real-time stock valuation table with automatic badges for items needing reorder and perishables expiring within 15 days or past expiration.
*(Preview image: `docs/screenshots/inventory_alerts.png`)*

### 4. Printable Tax Invoice
Clean, standardized receipts formatted for thermal receipt rolls and standard A4 printing, including invoice numbers, store metadata, tax calculations, and cashier details.
*(Preview image: `docs/screenshots/tax_invoice.png`)*

---

## 🌟 Key Features

### 1. Authentication & Role-Based Access Control (RBAC)
- **Role separation**: `admin` (Store Manager) and `cashier` (Terminal Operator).
- **Secure password hashing**: Powered by Werkzeug's `scrypt` hashing algorithm.
- **Granular permissions**: Protected by `@login_required` and `@admin_required` decorators. Cashiers are restricted from financial reports, supplier configuration, and manual stock overrides, immediately redirecting to the POS terminal.
- **Quick Demo Credentials**: One-click login on the authentication screen for rapid testing.

### 2. Product & Supplier Catalog
- **Catalog Lifecycle**: Add, edit, delete, search, and view products with real-time stock status.
- **SKU Uniqueness & Validation**: Enforces unique SKU barcodes, category classification, units of measure (`kg`, `pack`, `bottle`, `loaf`, `dozen`), cost price, selling price, and expiry dates.
- **Supplier Directory**: Full supplier management with contact persons, phone numbers, emails, addresses, and live product counts.
- **Referential Safety**: Foreign key constraints with `SET NULL` on supplier removal.

### 3. Point of Sale (POS) & Billing
- **Real-Time Search**: Search products by name, category, or direct SKU barcode scanner input.
- **Authoritative Server-Side Pricing**: Prices are fetched strictly from the database during checkout, preventing client-side price tampering.
- **Atomic Transactions**: Every checkout executes within an isolated database transaction:
  1. Validates available stock for each line item.
  2. Inserts master record into `sales` table.
  3. Inserts each line item into `sale_items` table.
  4. Automatically deducts product quantities (`quantity = quantity - sold`).
  5. Automatically logs a `SALE` entry into the `stock_movements` audit log.
  6. Reverts completely (`ROLLBACK`) if any item violates constraints or lacks stock.
- **Unique Invoice Numbers**: Formatted as `INV-YYYYMMDD-XXXX`.
- **Printable Tax Invoices**: Formatted for receipt printers and standard printing with store information, tax ID, line items, and breakdown.

### 4. Inventory Control & Perishables Alerts
- **Real-Time Valuation**: Live calculation of total stock units, cost valuation, and retail market valuation.
- **Low-Stock Alerts**: Instant notifications when inventory falls below individual `reorder_level` thresholds with deficit calculations.
- **Expiry Monitoring**: Proactive alerts for perishables expiring within **15 days** or already expired to safeguard quality and minimize shrinkage.
- **Stock Movement Audit Trail**: Every inventory modification (Sales, Restocks, Manual Adjustments, Damaged write-offs) is permanently logged with timestamps, previous/new quantities, and user IDs.

### 5. Analytics Dashboard (Pandas & Plotly)
- **KPI Metrics**: Total Revenue, Total Sales, Average Bill Value, Total Products, Low-Stock Count, and **Stock Turnover Ratio** (COGS / Average Inventory).
- **Pandas Data Analysis**:
  - Daily revenue trends and transaction volume over 30 days.
  - Month-over-month revenue aggregations.
  - Top 10 selling products ranked by volume and revenue.
  - Category-wise revenue share.
  - **Slow-Moving Stock Identification**: Flags products with $\le 2$ sales in the last 30 days for clearance planning.
- **Plotly Visualizations**: Interactive emerald-themed charts with tooltips, legends, and responsive resizing.

### 6. Reports & Data Export
- **Daily Sales Report**: Detailed daily transactions, item velocities, discounts, and cashier breakdown.
- **Monthly Sales Report**: Daily revenue breakdown for any selected month.
- **Product Profitability Report**: Unit volume, revenue, Cost of Goods Sold (COGS), gross profit, and margin percentage.
- **Low Stock Report**: Deficit calculations, estimated reorder capital, and supplier contact details.
- **Expiry Report**: Perishables risk report with tied-up capital calculations.
- **One-Click CSV Export**: Instant CSV downloads for all generated reports.

---

## 🛠 Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.10+ (Tested on Python 3.12 and Python 3.13), Flask 3.1 |
| **Authentication & Security** | Werkzeug (Scrypt password hashing), HTTPOnly/SameSite session cookies |
| **Configuration** | `python-dotenv` for secure environment variable management |
| **Data Analysis** | Pandas 2.2+, NumPy |
| **Data Visualization** | Plotly 5.20+ (Python Plotly + Plotly.js) |
| **Database** | SQLite3 (`PRAGMA foreign_keys = ON;`, Indexes, Check Constraints) |
| **Frontend & UI** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons |
| **Testing Suite** | Pytest 8.0+ (39 automated unit, integration & security tests) |

---

## 📂 Project Structure

```
GreenLeaf_Grocers/
├── .env.example               # Environment configuration template (safe placeholders)
├── .gitignore                 # Excludes .env, databases, virtual environments, caches
├── pytest.ini                 # Pytest runner configuration
├── requirements.txt           # Project dependencies
├── run.py                     # Configurable application entrypoint
├── seed_data.py               # Comprehensive database seeder with realistic test data
├── README.md                  # Complete documentation
│
├── app/                       # Flask application package
│   ├── __init__.py            # Application factory, session cookie & secret key config
│   ├── db.py                  # SQLite connection, adapters, converters & teardown
│   ├── schema.sql             # Relational DDL, constraints, foreign keys & indexes
│   │
│   ├── models/                # Database models & query abstractions
│   │   ├── __init__.py
│   │   ├── user.py            # User authentication & Scrypt password verification
│   │   ├── supplier.py        # Supplier directory & relationships
│   │   ├── product.py         # Catalog CRUD, stock filters & manual adjustments
│   │   ├── sale.py            # Authoritative pricing, checkout & atomic billing
│   │   └── stock_movement.py  # Stock audit records & movement queries
│   │
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Session handling & RBAC route decorators
│   │   ├── pos_service.py     # Cart processing & discount range validation
│   │   ├── inventory_service.py # Inventory valuation, low-stock & expiry calculations
│   │   ├── analytics_service.py # Pandas aggregation & Plotly interactive chart builders
│   │   └── report_service.py  # Sales reports, profitability analysis & CSV streaming
│   │
│   ├── routes/                # Modular Flask Blueprints
│   │   ├── __init__.py
│   │   ├── auth_routes.py     # Login, logout & session management
│   │   ├── dashboard_routes.py # Executive analytics dashboard (Admin only)
│   │   ├── pos_routes.py      # POS terminal, live catalog API, printable invoices
│   │   ├── product_routes.py  # Product directory management & forms
│   │   ├── supplier_routes.py # Supplier directory management & forms
│   │   ├── inventory_routes.py # Stock status, low-stock, expiry, movements
│   │   └── report_routes.py   # Daily/Monthly/Product reports & CSV exports
│   │
│   ├── static/                # Static assets
│   │   ├── css/
│   │   │   └── custom.css     # Emerald-green theme styling & responsive cards
│   │   └── js/
│   │       ├── main.js        # UI toast helpers & confirmation modals
│   │       └── pos.js         # Interactive POS cart state engine & shortcuts
│   │
│   └── templates/             # Jinja2 HTML templates
│       ├── base.html          # Base layout with sidebar, header, alert counters
│       ├── auth/login.html    # Authentication page with one-click demo logins
│       ├── dashboard/index.html # Executive dashboard & Plotly chart embeds
│       ├── pos/               # POS checkout terminal & printable tax invoice
│       ├── products/          # Catalog management, forms, details
│       ├── suppliers/         # Supplier directory & modals
│       ├── inventory/         # Inventory tables, low-stock, expiry, movement audit
│       ├── reports/           # Reports hub & dedicated daily/monthly/profit views
│       └── errors/            # 403 Forbidden, 404 Not Found, 500 Server Error
│
├── docs/                      # Documentation assets
│   └── screenshots/           # Screenshot gallery placeholder
│
└── tests/                     # Automated Pytest suite (39 tests)
    ├── conftest.py            # Fixtures & temporary in-memory database
    ├── test_analytics.py      # Analytics calculations & Plotly chart tests
    ├── test_auth.py           # Authentication, passwords & RBAC permissions tests
    ├── test_inventory.py      # Low-stock & perishables expiry alert tests
    ├── test_pos_billing.py    # POS checkout & stock deduction tests
    ├── test_products.py       # Product catalog CRUD & uniqueness tests
    ├── test_reports.py        # Report datasets & CSV export tests
    └── test_security.py       # Price tampering, cookie flags, debug & secret tests
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher (Tested on Python 3.12 and Python 3.13)
- `pip` package manager
- `git` version control

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/GreenLeaf_Grocers.git
cd GreenLeaf_Grocers
```

### 3. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

GreenLeaf Grocers uses a `.env` file to manage secrets and runtime settings.

### 1. Copy the Environment Template
```bash
# On Linux / macOS:
cp .env.example .env

# On Windows (PowerShell / CMD):
copy .env.example .env
```

### 2. Configure Your Variables
Edit `.env` to customize your local settings:

```env
# Application Environment: 'development' or 'production'
FLASK_ENV=development

# Debug Mode: True in development; strictly disabled in production
FLASK_DEBUG=True

# Server Port
PORT=5000

# Secret Key: Required for session encryption.
# In production, generate a secure random 64-character hex key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=dev-greenleaf-grocers-development-secret-key-32bytes-secure

# Cookie Security (optional): Set to True when serving over HTTPS
SESSION_COOKIE_SECURE=False
```

> [!IMPORTANT]
> The `.env` file is excluded from git via `.gitignore`. Never commit production secrets or actual API keys to GitHub.

---

## 🗄️ Database Initialization & Seeding

The application initializes the SQLite schema automatically upon first launch. To populate the system with rich demonstration data:

```bash
python seed_data.py
```

### What `seed_data.py` Populates:
- **3 User Accounts** (1 Store Manager, 2 Cashiers) with Scrypt hashed passwords.
- **6 Verified Suppliers** (Fresh produce, dairy, bakery, beverages, pantry, snacks).
- **39 Realistic Products** across 7 categories with diverse pricing, stock levels, and expiry dates.
- **Over 80 Historical Sales Transactions** spanning the past 30 days to populate the analytics dashboard.
- **Over 240 Stock Movement Records** establishing an audit trail.

---

## 💻 Running the Application

Start the local Flask development server:

```bash
python run.py
```

Once running, open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo User Credentials

The database seeder provisions the following accounts:

| Role | Username | Password | Access Scope |
|---|---|---|---|
| **Store Manager (Admin)** | `admin` | `admin123` | Full access to Executive Dashboard, Reports, Suppliers, Inventory Overrides, and POS |
| **Cashier 1** | `cashier` | `cashier123` | Access to POS Billing Terminal, Product Search, and Printable Invoices |
| **Cashier 2** | `sarah` | `cashier123` | Access to POS Billing Terminal, Product Search, and Printable Invoices |

> [!TIP]
> On the login page, you can click the **"Quick Demo Credentials"** buttons (`Admin Demo` or `Cashier Demo`) to auto-fill credentials and sign in instantly.

---

## 🧪 Running Automated Tests

The application includes **39 automated unit, integration, and security tests** using Pytest:

```bash
python -m pytest -v
```

### Test Suite Coverage:
- `tests/test_analytics.py`: KPI accuracy, rolling 30-day aggregations, top 10 products, slow-moving detection, Plotly figures (5 tests).
- `tests/test_auth.py`: Authentication, Scrypt hashing, role separation, session teardown, unauthorized route blocking (6 tests).
- `tests/test_inventory.py`: Stock valuation, low-stock threshold detection, 15-day expiry warnings, manual adjustments, audit logs (5 tests).
- `tests/test_pos_billing.py`: Cart validation, atomic stock decrementing, out-of-stock rejection, printable invoice generation (5 tests).
- `tests/test_products.py`: Product catalog CRUD, SKU uniqueness, category filters, detail views (5 tests).
- `tests/test_reports.py`: Daily/monthly sales reports, product performance metrics, CSV streaming (6 tests).
- `tests/test_security.py`: Frontend price tampering defense, quantity checks, discount boundaries, production secret key enforcement, session cookie flags, and debug lockdown (7 tests).

**Sample output:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\acer\Desktop\GreenLeaf_Grocers
configfile: pytest.ini
testpaths: tests
collected 39 items

tests/test_analytics.py::test_analytics_kpi_metrics PASSED                [  2%]
tests/test_analytics.py::test_pandas_top_selling_products PASSED          [  5%]
tests/test_analytics.py::test_pandas_slow_moving_products PASSED          [  7%]
tests/test_analytics.py::test_plotly_chart_builders PASSED                [ 10%]
tests/test_analytics.py::test_dashboard_page_renders_with_plotly PASSED   [ 12%]
tests/test_auth.py::test_login_page_renders PASSED                        [ 15%]
tests/test_auth.py::test_admin_login_success PASSED                       [ 17%]
tests/test_auth.py::test_cashier_login_redirects_to_pos PASSED            [ 20%]
tests/test_auth.py::test_login_failure_invalid_credentials PASSED         [ 23%]
tests/test_auth.py::test_role_based_access_control PASSED                 [ 25%]
tests/test_auth.py::test_logout PASSED                                    [ 28%]
tests/test_inventory.py::test_inventory_overview_page PASSED              [ 30%]
tests/test_inventory.py::test_low_stock_detection PASSED                  [ 33%]
tests/test_inventory.py::test_expiry_alerts_detection PASSED              [ 35%]
tests/test_inventory.py::test_stock_manual_adjustment PASSED              [ 38%]
tests/test_inventory.py::test_stock_movement_audit_view PASSED            [ 41%]
tests/test_pos_billing.py::test_pos_terminal_renders PASSED               [ 43%]
tests/test_pos_billing.py::test_pos_api_products PASSED                   [ 46%]
tests/test_pos_billing.py::test_pos_successful_checkout PASSED            [ 48%]
tests/test_pos_billing.py::test_pos_insufficient_stock_rejection PASSED   [ 51%]
tests/test_pos_billing.py::test_pos_view_printable_invoice PASSED         [ 53%]
tests/test_products.py::test_list_products PASSED                         [ 56%]
tests/test_products.py::test_create_product PASSED                        [ 58%]
tests/test_products.py::test_prevent_duplicate_sku PASSED                 [ 61%]
tests/test_products.py::test_update_product PASSED                        [ 64%]
tests/test_products.py::test_product_detail_view PASSED                   [ 66%]
tests/test_reports.py::test_reports_hub PASSED                            [ 69%]
tests/test_reports.py::test_daily_sales_report_and_csv PASSED             [ 71%]
tests/test_reports.py::test_monthly_sales_report_and_csv PASSED           [ 74%]
tests/test_reports.py::test_product_performance_report_and_csv PASSED     [ 76%]
tests/test_reports.py::test_low_stock_report_and_csv PASSED               [ 79%]
tests/test_reports.py::test_expiry_report_and_csv PASSED                  [ 82%]
tests/test_security.py::test_checkout_ignores_frontend_price_tampering PASSED [ 84%]
tests/test_security.py::test_checkout_rejects_negative_or_zero_quantity PASSED [ 87%]
tests/test_security.py::test_checkout_rejects_out_of_bounds_discounts PASSED [ 89%]
tests/test_security.py::test_production_fails_without_secret_key PASSED  [ 92%]
tests/test_security.py::test_production_succeeds_with_configured_secret_key PASSED [ 94%]
tests/test_security.py::test_session_cookie_settings_in_dev_and_prod PASSED [ 97%]
tests/test_security.py::test_debug_mode_disabled_in_production PASSED     [100%]

============================= 39 passed in 33.75s =============================
```

---

## 🔒 Security & Data Integrity Highlights

1. **Authoritative Server Pricing**: Prices are retrieved directly from the database during checkout. Any unit prices submitted from the frontend or modified by scripts are discarded.
2. **Atomic Billing Transactions**: Billing operations use strict database transactions (`BEGIN`, `COMMIT`, `ROLLBACK`), ensuring invoice creation, line item insertion, inventory reduction, and movement logs commit together or completely revert.
3. **Negative Stock Prevention**: Multi-layered protection using SQLite `CHECK (quantity >= 0)` constraints and pre-sale availability checks prevent out-of-stock checkouts.
4. **Hardened Secret Key Management**: Insecure hardcoded keys have been eliminated. In production, missing secrets trigger an immediate configuration error.
5. **Session Cookie Hardening**: Configured with `SESSION_COOKIE_HTTPONLY=True` to mitigate XSS cookie theft, `SESSION_COOKIE_SAMESITE='Lax'` for CSRF defense, and conditional `SESSION_COOKIE_SECURE=True` in production.
6. **Debug Lockdown**: Interactive debugger is strictly disabled when running in production mode (`FLASK_ENV=production`).
7. **Password Hashing**: Stored as salted, memory-hard `scrypt` hashes using Werkzeug.
8. **Relational Constraints**: SQLite foreign keys (`PRAGMA foreign_keys = ON;`) enforce data consistency across users, products, suppliers, sales, and audit trails.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
