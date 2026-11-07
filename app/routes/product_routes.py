from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required, admin_required
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.stock_movement import StockMovement

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    stock_filter = request.args.get('stock', '').strip()
    expiry_filter = request.args.get('expiry', '').strip()

    products = Product.list_all(
        search=search,
        category=category,
        stock_filter=stock_filter,
        expiry_filter=expiry_filter
    )
    categories = Product.get_categories()
    return render_template(
        'products/index.html',
        products=products,
        categories=categories,
        current_search=search,
        current_category=category,
        current_stock=stock_filter,
        current_expiry=expiry_filter
    )

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        category = request.form.get('category', '').strip()
        cost_price = request.form.get('cost_price', '0')
        selling_price = request.form.get('selling_price', '0')
        quantity = request.form.get('quantity', '0')
        reorder_level = request.form.get('reorder_level', '10')
        expiry_date = request.form.get('expiry_date', '').strip()
        unit = request.form.get('unit', 'unit').strip()
        supplier_id = request.form.get('supplier_id') or None

        if not name or not sku or not category or not expiry_date:
            flash("Please fill in all required fields (Name, SKU, Category, Expiry Date).", "danger")
            suppliers = Supplier.list_all()
            return render_template('products/form.html', product=None, suppliers=suppliers)

        existing = Product.get_by_sku(sku)
        if existing:
            flash(f"A product with SKU '{sku}' already exists ({existing['name']}).", "danger")
            suppliers = Supplier.list_all()
            return render_template('products/form.html', product=None, suppliers=suppliers)

        try:
            Product.create(
                name=name,
                sku=sku,
                category=category,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=quantity,
                reorder_level=reorder_level,
                expiry_date=expiry_date,
                unit=unit,
                supplier_id=int(supplier_id) if supplier_id else None,
                user_id=session.get('user_id')
            )
            flash(f"Product '{name}' added successfully!", "success")
            return redirect(url_for('products.index'))
        except Exception as e:
            flash(f"Error creating product: {str(e)}", "danger")

    suppliers = Supplier.list_all()
    categories = Product.get_categories()
    return render_template('products/form.html', product=None, suppliers=suppliers, categories=categories)

@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        category = request.form.get('category', '').strip()
        cost_price = request.form.get('cost_price', '0')
        selling_price = request.form.get('selling_price', '0')
        reorder_level = request.form.get('reorder_level', '10')
        expiry_date = request.form.get('expiry_date', '').strip()
        unit = request.form.get('unit', 'unit').strip()
        supplier_id = request.form.get('supplier_id') or None

        if not name or not sku or not category or not expiry_date:
            flash("Please fill in all required fields.", "danger")
            suppliers = Supplier.list_all()
            return render_template('products/form.html', product=product, suppliers=suppliers)

        existing = Product.get_by_sku(sku)
        if existing and existing['id'] != product_id:
            flash(f"Another product with SKU '{sku}' already exists ({existing['name']}).", "danger")
            suppliers = Supplier.list_all()
            return render_template('products/form.html', product=product, suppliers=suppliers)

        try:
            Product.update(
                product_id=product_id,
                name=name,
                sku=sku,
                category=category,
                cost_price=cost_price,
                selling_price=selling_price,
                reorder_level=reorder_level,
                expiry_date=expiry_date,
                unit=unit,
                supplier_id=int(supplier_id) if supplier_id else None
            )
            flash(f"Product '{name}' updated successfully!", "success")
            return redirect(url_for('products.index'))
        except Exception as e:
            flash(f"Error updating product: {str(e)}", "danger")

    suppliers = Supplier.list_all()
    categories = Product.get_categories()
    return render_template('products/form.html', product=product, suppliers=suppliers, categories=categories)

@bp.route('/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('products.index'))

    try:
        Product.delete(product_id)
        flash(f"Product '{product['name']}' deleted successfully.", "success")
    except ValueError as ve:
        flash(str(ve), "warning")
    except Exception as e:
        flash(f"Could not delete product: {str(e)}", "danger")

    return redirect(url_for('products.index'))

@bp.route('/<int:product_id>')
@login_required
def detail(product_id):
    product = Product.get_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('products.index'))

    movements = StockMovement.list_recent(limit=50, product_id=product_id)
    return render_template('products/detail.html', product=product, movements=movements)
