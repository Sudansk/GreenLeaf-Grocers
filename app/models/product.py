from datetime import datetime, date, timedelta
from app.db import query_db, execute_db, get_db

class Product:
    @staticmethod
    def create(name, sku, category, cost_price, selling_price, quantity, reorder_level, expiry_date, unit='unit', supplier_id=None, user_id=None):
        """Create a new product and record initial stock movement."""
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                """INSERT INTO products (name, sku, category, cost_price, selling_price, quantity, reorder_level, expiry_date, unit, supplier_id, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (name.strip(), sku.strip().upper(), category.strip(), float(cost_price), float(selling_price),
                 int(quantity), int(reorder_level), str(expiry_date), unit.strip(), supplier_id)
            )
            product_id = cursor.lastrowid

            if int(quantity) > 0:
                cursor.execute(
                    """INSERT INTO stock_movements (product_id, movement_type, quantity, previous_quantity, new_quantity, reference_id, notes, created_by)
                       VALUES (?, 'RESTOCK', ?, 0, ?, 'INITIAL_STOCK', 'Initial inventory creation', ?)""",
                    (product_id, int(quantity), int(quantity), user_id)
                )

            db.commit()
            return product_id
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_by_id(product_id):
        """Fetch product with supplier name."""
        return query_db(
            """SELECT p.*, s.name as supplier_name 
               FROM products p 
               LEFT JOIN suppliers s ON p.supplier_id = s.id 
               WHERE p.id = ?""",
            (product_id,),
            one=True
        )

    @staticmethod
    def get_by_sku(sku):
        """Fetch product by SKU."""
        return query_db(
            """SELECT p.*, s.name as supplier_name 
               FROM products p 
               LEFT JOIN suppliers s ON p.supplier_id = s.id 
               WHERE UPPER(p.sku) = UPPER(?)""",
            (sku.strip(),),
            one=True
        )

    @staticmethod
    def update(product_id, name, sku, category, cost_price, selling_price, reorder_level, expiry_date, unit='unit', supplier_id=None):
        """Update product metadata (stock adjustments are handled separately for audit trail)."""
        execute_db(
            """UPDATE products 
               SET name = ?, sku = ?, category = ?, cost_price = ?, selling_price = ?, 
                   reorder_level = ?, expiry_date = ?, unit = ?, supplier_id = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (name.strip(), sku.strip().upper(), category.strip(), float(cost_price), float(selling_price),
             int(reorder_level), str(expiry_date), unit.strip(), supplier_id, product_id)
        )

    @staticmethod
    def delete(product_id):
        """Delete product (cascades to stock_movements; will fail if referenced in sale_items or handle gracefully)."""
        # First check if product has sale_items
        sales = query_db("SELECT COUNT(*) as cnt FROM sale_items WHERE product_id = ?", (product_id,), one=True)
        if sales and sales['cnt'] > 0:
            raise ValueError("Cannot delete product with historical sales records. You may set its quantity to 0 instead.")
        execute_db("DELETE FROM products WHERE id = ?", (product_id,))

    @staticmethod
    def list_all(search=None, category=None, stock_filter=None, expiry_filter=None):
        """List products with optional search, category, stock and expiry filters."""
        query = """
            SELECT p.*, s.name as supplier_name,
                   CASE 
                       WHEN p.quantity = 0 THEN 'Out of Stock'
                       WHEN p.quantity <= p.reorder_level THEN 'Low Stock'
                       ELSE 'In Stock'
                   END as stock_status,
                   CASE
                       WHEN p.expiry_date < DATE('now') THEN 'Expired'
                       WHEN p.expiry_date <= DATE('now', '+15 days') THEN 'Expiring Soon'
                       ELSE 'Good'
                   END as expiry_status,
                   CAST(julianday(p.expiry_date) - julianday('now') AS INTEGER) as days_to_expiry
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
        """
        args = []

        if search:
            query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.category LIKE ?)"
            term = f"%{search.strip()}%"
            args.extend([term, term, term])

        if category and category != 'All':
            query += " AND p.category = ?"
            args.append(category)

        if stock_filter == 'low':
            query += " AND p.quantity <= p.reorder_level AND p.quantity > 0"
        elif stock_filter == 'out':
            query += " AND p.quantity = 0"
        elif stock_filter == 'in':
            query += " AND p.quantity > p.reorder_level"

        if expiry_filter == 'expired':
            query += " AND p.expiry_date < DATE('now')"
        elif expiry_filter == 'soon':
            query += " AND p.expiry_date >= DATE('now') AND p.expiry_date <= DATE('now', '+15 days')"

        query += " ORDER BY p.name ASC"
        return query_db(query, args)

    @staticmethod
    def get_categories():
        """Get distinct product categories."""
        rows = query_db("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category ASC")
        return [r['category'] for r in rows]

    @staticmethod
    def get_low_stock():
        """Get all products with quantity <= reorder_level."""
        return query_db(
            """SELECT p.*, s.name as supplier_name,
                      (p.reorder_level - p.quantity) as deficit
               FROM products p
               LEFT JOIN suppliers s ON p.supplier_id = s.id
               WHERE p.quantity <= p.reorder_level
               ORDER BY p.quantity ASC"""
        )

    @staticmethod
    def get_expiring(days=15):
        """Get products expiring within N days or already expired."""
        return query_db(
            """SELECT p.*, s.name as supplier_name,
                      CAST(julianday(p.expiry_date) - julianday('now') AS INTEGER) as days_left
               FROM products p
               LEFT JOIN suppliers s ON p.supplier_id = s.id
               WHERE p.expiry_date <= DATE('now', '+' || ? || ' days')
               ORDER BY p.expiry_date ASC""",
            (days,)
        )

    @staticmethod
    def adjust_stock(product_id, delta, movement_type, user_id=None, reference=None, notes=None):
        """Atomically adjust product quantity and log to stock_movements."""
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Product not found")

            prev_qty = row['quantity']
            new_qty = prev_qty + delta
            if new_qty < 0:
                raise ValueError(f"Insufficient stock. Available: {prev_qty}, Requested reduction: {-delta}")

            cursor.execute(
                "UPDATE products SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_qty, product_id)
            )

            cursor.execute(
                """INSERT INTO stock_movements (product_id, movement_type, quantity, previous_quantity, new_quantity, reference_id, notes, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (product_id, movement_type, abs(delta), prev_qty, new_qty, reference, notes, user_id)
            )

            db.commit()
            return new_qty
        except Exception:
            db.rollback()
            raise
