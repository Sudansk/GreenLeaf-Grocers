from app.models.sale import Sale
from app.models.product import Product

class POSService:
    @staticmethod
    def process_checkout(cashier_id, customer_name, customer_phone, items, discount_percent=0.0, payment_method='Cash', notes=None):
        """
        Validate and execute checkout.
        Items: list of dicts with keys 'product_id', 'quantity' (and optional 'unit_price').
        """
        if not items or len(items) == 0:
            return False, "Cart is empty. Please add products before checking out.", None

        # Validate discount percentage
        try:
            discount_percent = float(discount_percent or 0.0)
        except (ValueError, TypeError):
            return False, "Discount percentage must be a valid number.", None

        if discount_percent < 0 or discount_percent > 100:
            return False, "Discount percent must be between 0 and 100.", None

        # Pre-check item formats and stock
        for idx, itm in enumerate(items):
            try:
                pid = int(itm.get('product_id'))
                qty = int(itm.get('quantity', 1))
            except (ValueError, TypeError):
                return False, f"Invalid product ID or quantity at item index {idx+1}.", None

            if qty <= 0:
                return False, f"Quantity must be at least 1 (item index {idx+1}).", None

            prod = Product.get_by_id(pid)
            if not prod:
                return False, f"Product #{pid} was not found.", None

            if prod['quantity'] < qty:
                return False, f"Insufficient stock for '{prod['name']}'. In stock: {prod['quantity']}, Requested: {qty}.", None

        try:
            result = Sale.create_sale(
                cashier_id=cashier_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                items=items,
                discount_percent=discount_percent,
                payment_method=payment_method,
                notes=notes
            )
            return True, "Sale completed successfully!", result
        except ValueError as ve:
            return False, str(ve), None
        except Exception as e:
            return False, f"Checkout failed: {str(e)}", None

    @staticmethod
    def get_invoice_details(invoice_number):
        """Retrieve complete invoice details including items and cashier."""
        sale = Sale.get_by_invoice(invoice_number)
        if not sale:
            return None, None
        items = Sale.get_sale_items(sale['id'])
        return sale, items
