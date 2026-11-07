from datetime import datetime, date
from app.db import query_db
from app.models.product import Product
from app.models.stock_movement import StockMovement

class InventoryService:
    @staticmethod
    def get_inventory_summary():
        """Compute top-level inventory statistics."""
        stats = query_db("""
            SELECT 
                COUNT(*) as total_products,
                COALESCE(SUM(quantity), 0) as total_units,
                COALESCE(SUM(quantity * cost_price), 0.0) as total_cost_valuation,
                COALESCE(SUM(quantity * selling_price), 0.0) as total_retail_valuation,
                SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) as out_of_stock_count,
                SUM(CASE WHEN quantity > 0 AND quantity <= reorder_level THEN 1 ELSE 0 END) as low_stock_count,
                SUM(CASE WHEN expiry_date < DATE('now') THEN 1 ELSE 0 END) as expired_count,
                SUM(CASE WHEN expiry_date >= DATE('now') AND expiry_date <= DATE('now', '+15 days') THEN 1 ELSE 0 END) as expiring_soon_count
            FROM products
        """, one=True)
        return stats

    @staticmethod
    def get_low_stock_products():
        """Retrieve low stock products."""
        return Product.get_low_stock()

    @staticmethod
    def get_expiring_products(days=15):
        """Retrieve products expiring within given days or already expired."""
        return Product.get_expiring(days=days)

    @staticmethod
    def adjust_stock(product_id, delta, movement_type, user_id=None, reference=None, notes=None):
        """Perform stock adjustment with auditing."""
        valid_types = ['RESTOCK', 'ADJUSTMENT_ADD', 'ADJUSTMENT_REMOVE', 'DAMAGE']
        if movement_type not in valid_types:
            raise ValueError(f"Invalid movement type: {movement_type}. Must be one of {valid_types}")
        return Product.adjust_stock(
            product_id=product_id,
            delta=delta,
            movement_type=movement_type,
            user_id=user_id,
            reference=reference,
            notes=notes
        )

    @staticmethod
    def get_stock_movements(limit=100, movement_type=None, product_id=None):
        """Retrieve stock movements audit trail."""
        return StockMovement.list_recent(limit=limit, movement_type=movement_type, product_id=product_id)
