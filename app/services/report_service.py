import io
import csv
from datetime import datetime
import pandas as pd
from app.db import get_db, query_db

class ReportService:
    @staticmethod
    def get_daily_sales_report(target_date=None):
        """Get daily sales report data for a specific date."""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')

        db = get_db()
        sales_query = """
            SELECT s.invoice_number, s.created_at, s.customer_name, s.payment_method,
                   s.subtotal, s.discount_amount, s.grand_total,
                   u.full_name as cashier_name,
                   (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) as item_count
            FROM sales s
            LEFT JOIN users u ON s.cashier_id = u.id
            WHERE DATE(s.created_at) = DATE(?)
            ORDER BY s.created_at DESC
        """
        sales_df = pd.read_sql_query(sales_query, db, params=(target_date,))

        summary = {
            'target_date': target_date,
            'total_sales': int(len(sales_df)),
            'total_revenue': float(sales_df['grand_total'].sum()) if not sales_df.empty else 0.0,
            'total_discounts': float(sales_df['discount_amount'].sum()) if not sales_df.empty else 0.0,
            'average_bill': round(float(sales_df['grand_total'].mean()), 2) if not sales_df.empty else 0.0,
        }

        # Item level aggregates for the day
        items_query = """
            SELECT si.product_name, p.category, SUM(si.quantity) as units_sold, SUM(si.line_total) as revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            LEFT JOIN products p ON si.product_id = p.id
            WHERE DATE(s.created_at) = DATE(?)
            GROUP BY si.product_id, si.product_name, p.category
            ORDER BY units_sold DESC
        """
        items_df = pd.read_sql_query(items_query, db, params=(target_date,))

        return {
            'summary': summary,
            'sales': sales_df.to_dict(orient='records'),
            'items': items_df.to_dict(orient='records')
        }

    @staticmethod
    def get_monthly_sales_report(year_month=None):
        """Get monthly sales report data grouped by day."""
        if not year_month:
            year_month = datetime.now().strftime('%Y-%m')

        db = get_db()
        query = """
            SELECT DATE(created_at) as sale_date,
                   COUNT(id) as transaction_count,
                   SUM(subtotal) as subtotal,
                   SUM(discount_amount) as discount_amount,
                   SUM(grand_total) as grand_total
            FROM sales
            WHERE strftime('%Y-%m', created_at) = ?
            GROUP BY DATE(created_at)
            ORDER BY sale_date ASC
        """
        df = pd.read_sql_query(query, db, params=(year_month,))

        summary = {
            'year_month': year_month,
            'total_days_active': int(len(df)),
            'total_transactions': int(df['transaction_count'].sum()) if not df.empty else 0,
            'total_revenue': float(df['grand_total'].sum()) if not df.empty else 0.0,
            'total_discounts': float(df['discount_amount'].sum()) if not df.empty else 0.0,
            'average_daily_revenue': round(float(df['grand_total'].mean()), 2) if not df.empty else 0.0,
        }

        return {
            'summary': summary,
            'daily_records': df.to_dict(orient='records')
        }

    @staticmethod
    def get_product_performance_report():
        """Get product sales performance, revenue, COGS and profit margin."""
        db = get_db()
        query = """
            SELECT p.id, p.name, p.sku, p.category, p.cost_price, p.selling_price, p.quantity as current_stock,
                   COALESCE(SUM(si.quantity), 0) as units_sold,
                   COALESCE(SUM(si.line_total), 0.0) as revenue_generated,
                   COALESCE(SUM(si.quantity * si.cost_price), 0.0) as total_cogs
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            GROUP BY p.id, p.name, p.sku, p.category, p.cost_price, p.selling_price, p.quantity
            ORDER BY units_sold DESC
        """
        df = pd.read_sql_query(query, db)
        if not df.empty:
            df['gross_profit'] = (df['revenue_generated'] - df['total_cogs']).round(2)
            df['profit_margin_pct'] = df.apply(
                lambda r: round((r['gross_profit'] / r['revenue_generated'] * 100), 1) if r['revenue_generated'] > 0 else 0.0,
                axis=1
            )
        return df.to_dict(orient='records')

    @staticmethod
    def get_low_stock_report():
        """Get list of all low-stock items with deficit and supplier details."""
        db = get_db()
        query = """
            SELECT p.id, p.name, p.sku, p.category, p.quantity, p.reorder_level,
                   (p.reorder_level - p.quantity) as deficit,
                   p.cost_price, (p.cost_price * (p.reorder_level - p.quantity)) as est_reorder_cost,
                   s.name as supplier_name, s.contact_person, s.phone as supplier_phone, s.email as supplier_email
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.quantity <= p.reorder_level
            ORDER BY (p.reorder_level - p.quantity) DESC, p.quantity ASC
        """
        df = pd.read_sql_query(query, db)
        return df.to_dict(orient='records')

    @staticmethod
    def get_expiry_report(days=15):
        """Get list of products expiring within N days or already expired."""
        db = get_db()
        query = """
            SELECT p.id, p.name, p.sku, p.category, p.quantity, p.selling_price, p.expiry_date,
                   CAST(julianday(p.expiry_date) - julianday('now') AS INTEGER) as days_remaining,
                   CASE 
                       WHEN p.expiry_date < DATE('now') THEN 'Expired'
                       ELSE 'Expiring Soon'
                   END as status,
                   (p.quantity * p.cost_price) as at_risk_cost,
                   s.name as supplier_name, s.phone as supplier_phone
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.expiry_date <= DATE('now', '+' || ? || ' days')
            ORDER BY p.expiry_date ASC
        """
        df = pd.read_sql_query(query, db, params=(days,))
        return df.to_dict(orient='records')

    # CSV Exporters
    @staticmethod
    def export_daily_sales_csv(target_date):
        report = ReportService.get_daily_sales_report(target_date)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Invoice Number', 'Date Time', 'Customer', 'Cashier', 'Payment Method', 'Items Count', 'Subtotal ($)', 'Discount ($)', 'Grand Total ($)'])
        for s in report['sales']:
            writer.writerow([
                s['invoice_number'], s['created_at'], s['customer_name'], s['cashier_name'],
                s['payment_method'], s['item_count'], f"{s['subtotal']:.2f}",
                f"{s['discount_amount']:.2f}", f"{s['grand_total']:.2f}"
            ])
        return output.getvalue()

    @staticmethod
    def export_monthly_sales_csv(year_month):
        report = ReportService.get_monthly_sales_report(year_month)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Transactions', 'Subtotal ($)', 'Discounts ($)', 'Grand Total ($)'])
        for r in report['daily_records']:
            writer.writerow([
                r['sale_date'], r['transaction_count'], f"{r['subtotal']:.2f}",
                f"{r['discount_amount']:.2f}", f"{r['grand_total']:.2f}"
            ])
        return output.getvalue()

    @staticmethod
    def export_product_performance_csv():
        records = ReportService.get_product_performance_report()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product Name', 'SKU', 'Category', 'Current Stock', 'Cost Price ($)', 'Selling Price ($)', 'Units Sold', 'Revenue ($)', 'COGS ($)', 'Gross Profit ($)', 'Margin (%)'])
        for r in records:
            writer.writerow([
                r['name'], r['sku'], r['category'], r['current_stock'],
                f"{r['cost_price']:.2f}", f"{r['selling_price']:.2f}", r['units_sold'],
                f"{r['revenue_generated']:.2f}", f"{r['total_cogs']:.2f}",
                f"{r['gross_profit']:.2f}", f"{r['profit_margin_pct']:.1f}%"
            ])
        return output.getvalue()

    @staticmethod
    def export_low_stock_csv():
        records = ReportService.get_low_stock_report()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product Name', 'SKU', 'Category', 'Current Stock', 'Reorder Level', 'Deficit', 'Cost Price ($)', 'Est. Reorder Cost ($)', 'Supplier', 'Phone', 'Email'])
        for r in records:
            writer.writerow([
                r['name'], r['sku'], r['category'], r['quantity'], r['reorder_level'], r['deficit'],
                f"{r['cost_price']:.2f}", f"{r['est_reorder_cost']:.2f}",
                r['supplier_name'] or 'N/A', r['supplier_phone'] or 'N/A', r['supplier_email'] or 'N/A'
            ])
        return output.getvalue()

    @staticmethod
    def export_expiry_csv():
        records = ReportService.get_expiry_report()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product Name', 'SKU', 'Category', 'Quantity', 'Expiry Date', 'Days Left', 'Status', 'At-Risk Cost ($)', 'Supplier', 'Phone'])
        for r in records:
            writer.writerow([
                r['name'], r['sku'], r['category'], r['quantity'], r['expiry_date'],
                r['days_remaining'], r['status'], f"{r['at_risk_cost']:.2f}",
                r['supplier_name'] or 'N/A', r['supplier_phone'] or 'N/A'
            ])
        return output.getvalue()
