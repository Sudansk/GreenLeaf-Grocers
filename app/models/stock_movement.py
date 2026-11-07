from app.db import query_db, execute_db

class StockMovement:
    @staticmethod
    def record(product_id, movement_type, quantity, prev_qty, new_qty, reference_id=None, notes=None, user_id=None):
        """Record a stock movement entry."""
        mov_id, _ = execute_db(
            """INSERT INTO stock_movements (product_id, movement_type, quantity, previous_quantity, new_quantity, reference_id, notes, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_id, movement_type, quantity, prev_qty, new_qty, reference_id, notes, user_id)
        )
        return mov_id

    @staticmethod
    def list_recent(limit=100, movement_type=None, product_id=None):
        """List stock movements with product details and user info."""
        query = """
            SELECT sm.*, p.name as product_name, p.sku as product_sku, p.unit as product_unit,
                   u.full_name as user_name
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
            LEFT JOIN users u ON sm.created_by = u.id
            WHERE 1=1
        """
        args = []
        if movement_type:
            query += " AND sm.movement_type = ?"
            args.append(movement_type)
        if product_id:
            query += " AND sm.product_id = ?"
            args.append(product_id)

        query += " ORDER BY sm.created_at DESC, sm.id DESC"
        if limit:
            query += " LIMIT ?"
            args.append(limit)

        return query_db(query, args)
