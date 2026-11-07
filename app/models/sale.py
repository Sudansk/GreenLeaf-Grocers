import random
from datetime import datetime
from app.db import query_db, execute_db, get_db

class Sale:
    @staticmethod
    def generate_invoice_number():
        """Generate unique invoice number: INV-YYYYMMDD-XXXX."""
        date_str = datetime.now().strftime("%Y%m%d")
        # Ensure uniqueness by checking existing invoices
        for _ in range(10):
            rand_suffix = f"{random.randint(1000, 9999)}"
            invoice_num = f"INV-{date_str}-{rand_suffix}"
            exists = query_db("SELECT id FROM sales WHERE invoice_number = ?", (invoice_num,), one=True)
            if not exists:
                return invoice_num
        # Fallback with timestamp seconds
        return f"INV-{date_str}-{datetime.now().strftime('%H%M%S')}"

    @staticmethod
    def create_sale(cashier_id, customer_name, customer_phone, items, discount_percent=0.0, payment_method='Cash', notes=None):
        """
        Execute atomic sale transaction:
        1. Validate items and stock availability.
        2. Calculate subtotal, discount, grand total.
        3. Insert sale header.
        4. Insert sale items.
        5. Deduct product quantities and log stock movements.
        """
        if not items:
            raise ValueError("Cart cannot be empty")

        try:
            discount_percent = float(discount_percent or 0.0)
        except (ValueError, TypeError):
            raise ValueError("Discount percent must be a valid number between 0 and 100")

        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("Discount percent must be between 0 and 100")

        db = get_db()
        cursor = db.cursor()
        try:
            # 1. Validate all products and stock availability
            validated_items = []
            subtotal = 0.0

            for item in items:
                try:
                    prod_id = int(item['product_id'])
                    qty = int(item['quantity'])
                except (KeyError, ValueError, TypeError):
                    raise ValueError("Invalid item format: product_id and positive quantity are required")

                if qty <= 0:
                    raise ValueError(f"Invalid quantity {qty} for product ID {prod_id}. Quantity must be at least 1.")

                cursor.execute(
                    "SELECT id, name, sku, selling_price, cost_price, quantity, expiry_date FROM products WHERE id = ?",
                    (prod_id,)
                )
                prod = cursor.fetchone()
                if not prod:
                    raise ValueError(f"Product ID {prod_id} not found")

                if prod['quantity'] < qty:
                    raise ValueError(
                        f"Insufficient stock for '{prod['name']}' (SKU: {prod['sku']}). "
                        f"Requested: {qty}, Available: {prod['quantity']}"
                    )

                # SECURITY: Always fetch authoritative price from database; never trust prices sent by the client
                unit_price = float(prod['selling_price'])
                cost_price = float(prod['cost_price'])
                line_total = round(unit_price * qty, 2)
                subtotal += line_total

                validated_items.append({
                    'product_id': prod['id'],
                    'product_name': prod['name'],
                    'sku': prod['sku'],
                    'current_qty': prod['quantity'],
                    'qty_sold': qty,
                    'unit_price': unit_price,
                    'cost_price': cost_price,
                    'line_total': line_total
                })

            subtotal = round(subtotal, 2)
            discount_amount = round((subtotal * discount_percent) / 100.0, 2)
            grand_total = round(subtotal - discount_amount, 2)
            invoice_num = Sale.generate_invoice_number()

            # 2. Insert sales master record
            cursor.execute(
                """INSERT INTO sales (invoice_number, cashier_id, customer_name, customer_phone,
                                      subtotal, discount_percent, discount_amount, tax_amount,
                                      grand_total, payment_method, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?)""",
                (invoice_num, cashier_id, customer_name or 'Walk-in Customer', customer_phone or '',
                 subtotal, discount_percent, discount_amount, grand_total, payment_method, notes or '')
            )
            sale_id = cursor.lastrowid

            # 3. Insert sale items & deduct stock
            for item in validated_items:
                cursor.execute(
                    """INSERT INTO sale_items (sale_id, product_id, product_name, unit_price, cost_price, quantity, line_total)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sale_id, item['product_id'], item['product_name'], item['unit_price'],
                     item['cost_price'], item['qty_sold'], item['line_total'])
                )

                new_qty = item['current_qty'] - item['qty_sold']
                cursor.execute(
                    "UPDATE products SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_qty, item['product_id'])
                )

                cursor.execute(
                    """INSERT INTO stock_movements (product_id, movement_type, quantity, previous_quantity, new_quantity, reference_id, notes, created_by)
                       VALUES (?, 'SALE', ?, ?, ?, ?, ?, ?)""",
                    (item['product_id'], item['qty_sold'], item['current_qty'], new_qty,
                     invoice_num, f"Sold on invoice {invoice_num}", cashier_id)
                )

            db.commit()
            return {
                'sale_id': sale_id,
                'invoice_number': invoice_num,
                'subtotal': subtotal,
                'discount_percent': discount_percent,
                'discount_amount': discount_amount,
                'grand_total': grand_total
            }
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_by_id(sale_id):
        """Fetch sale record by ID with cashier info."""
        return query_db(
            """SELECT s.*, u.full_name as cashier_name, u.username as cashier_username
               FROM sales s
               LEFT JOIN users u ON s.cashier_id = u.id
               WHERE s.id = ?""",
            (sale_id,),
            one=True
        )

    @staticmethod
    def get_by_invoice(invoice_number):
        """Fetch sale record by invoice number with cashier info."""
        return query_db(
            """SELECT s.*, u.full_name as cashier_name, u.username as cashier_username
               FROM sales s
               LEFT JOIN users u ON s.cashier_id = u.id
               WHERE s.invoice_number = ?""",
            (invoice_number.strip(),),
            one=True
        )

    @staticmethod
    def get_sale_items(sale_id):
        """Fetch all items for a given sale with SKU and unit."""
        return query_db(
            """SELECT si.*, p.sku, p.unit, p.category
               FROM sale_items si
               LEFT JOIN products p ON si.product_id = p.id
               WHERE si.sale_id = ?
               ORDER BY si.id ASC""",
            (sale_id,)
        )

    @staticmethod
    def list_all(start_date=None, end_date=None, cashier_id=None, limit=100):
        """List sales with optional filters."""
        query = """
            SELECT s.*, u.full_name as cashier_name,
                   (SELECT COUNT(*) FROM sale_items si WHERE si.sale_id = s.id) as item_count
            FROM sales s
            LEFT JOIN users u ON s.cashier_id = u.id
            WHERE 1=1
        """
        args = []
        if start_date:
            query += " AND DATE(s.created_at) >= DATE(?)"
            args.append(start_date)
        if end_date:
            query += " AND DATE(s.created_at) <= DATE(?)"
            args.append(end_date)
        if cashier_id:
            query += " AND s.cashier_id = ?"
            args.append(cashier_id)

        query += " ORDER BY s.created_at DESC"
        if limit:
            query += " LIMIT ?"
            args.append(limit)

        return query_db(query, args)
