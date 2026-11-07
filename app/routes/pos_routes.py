from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.pos_service import POSService
from app.models.product import Product
from app.models.sale import Sale

bp = Blueprint('pos', __name__, url_prefix='/pos')

@bp.route('/')
@login_required
def index():
    """Main POS / Billing screen."""
    categories = Product.get_categories()
    products = Product.list_all()
    return render_template('pos/index.html', categories=categories, products=products)

@bp.route('/api/products')
@login_required
def api_products():
    """API to search and filter products for the POS cart."""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    products = Product.list_all(search=search, category=category if category != 'All' else None)
    
    result = []
    for p in products:
        result.append({
            'id': p['id'],
            'name': p['name'],
            'sku': p['sku'],
            'category': p['category'],
            'selling_price': float(p['selling_price']),
            'quantity': int(p['quantity']),
            'unit': p['unit'],
            'stock_status': p['stock_status'],
            'expiry_status': p['expiry_status'],
            'days_to_expiry': p['days_to_expiry']
        })
    return jsonify(result)

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Process POS checkout."""
    data = request.get_json(silent=True) or request.form.to_dict()
    
    cashier_id = session.get('user_id')
    customer_name = data.get('customer_name', 'Walk-in Customer')
    customer_phone = data.get('customer_phone', '')
    discount_percent = data.get('discount_percent', 0.0)
    payment_method = data.get('payment_method', 'Cash')
    notes = data.get('notes', '')
    items = data.get('items', [])

    # If form submission stringified items
    if isinstance(items, str):
        import json
        try:
            items = json.loads(items)
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid items format in request.'}), 400

    success, message, result = POSService.process_checkout(
        cashier_id=cashier_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        items=items,
        discount_percent=discount_percent,
        payment_method=payment_method,
        notes=notes
    )

    if success:
        return jsonify({
            'success': True,
            'message': message,
            'invoice_number': result['invoice_number'],
            'redirect_url': url_for('pos.view_invoice', invoice_number=result['invoice_number'])
        })
    else:
        return jsonify({'success': False, 'message': message}), 400

@bp.route('/invoice/<invoice_number>')
@login_required
def view_invoice(invoice_number):
    """Printable invoice view."""
    sale, items = POSService.get_invoice_details(invoice_number)
    if not sale:
        flash(f"Invoice {invoice_number} not found.", "danger")
        return redirect(url_for('pos.index'))

    return render_template('pos/invoice.html', sale=sale, items=items)

@bp.route('/history')
@login_required
def history():
    """Recent sales list."""
    sales = Sale.list_all(limit=50)
    return render_template('pos/history.html', sales=sales)
