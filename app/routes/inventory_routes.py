from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required, admin_required
from app.services.inventory_service import InventoryService
from app.models.product import Product

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route('/')
@login_required
def index():
    """Inventory overview and stock status."""
    summary = InventoryService.get_inventory_summary()
    products = Product.list_all()
    categories = Product.get_categories()
    return render_template(
        'inventory/index.html',
        summary=summary,
        products=products,
        categories=categories
    )

@bp.route('/low-stock')
@login_required
def low_stock():
    """Dedicated low-stock alert view."""
    low_stock_items = InventoryService.get_low_stock_products()
    return render_template('inventory/low_stock.html', items=low_stock_items)

@bp.route('/expiry')
@login_required
def expiry():
    """Dedicated expiry alert view (within 15 days & expired)."""
    expiring_items = InventoryService.get_expiring_products(days=15)
    return render_template('inventory/expiry.html', items=expiring_items)

@bp.route('/movements')
@admin_required
def movements():
    """Stock movement audit trail."""
    movement_type = request.args.get('type', '').strip() or None
    movements_list = InventoryService.get_stock_movements(limit=100, movement_type=movement_type)
    return render_template('inventory/movements.html', movements=movements_list, current_type=movement_type)

@bp.route('/adjust', methods=['POST'])
@admin_required
def adjust_stock():
    """Process stock adjustment (Restock, Damage, Correction)."""
    product_id = request.form.get('product_id')
    movement_type = request.form.get('movement_type')
    quantity_str = request.form.get('quantity')
    notes = request.form.get('notes', '').strip()
    reference = request.form.get('reference', '').strip()

    if not product_id or not movement_type or not quantity_str:
        flash("Missing required fields for stock adjustment.", "danger")
        return redirect(request.referrer or url_for('inventory.index'))

    try:
        pid = int(product_id)
        qty = int(quantity_str)
        if qty <= 0:
            flash("Adjustment quantity must be greater than zero.", "danger")
            return redirect(request.referrer or url_for('inventory.index'))

        # Delta calculation based on movement type
        if movement_type in ['RESTOCK', 'ADJUSTMENT_ADD']:
            delta = qty
        elif movement_type in ['ADJUSTMENT_REMOVE', 'DAMAGE']:
            delta = -qty
        else:
            flash("Invalid movement type selected.", "danger")
            return redirect(request.referrer or url_for('inventory.index'))

        new_qty = InventoryService.adjust_stock(
            product_id=pid,
            delta=delta,
            movement_type=movement_type,
            user_id=session.get('user_id'),
            reference=reference or 'MANUAL_ADJUSTMENT',
            notes=notes
        )
        flash(f"Stock adjusted successfully! New quantity is {new_qty}.", "success")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error adjusting stock: {str(e)}", "danger")

    return redirect(request.referrer or url_for('inventory.index'))
