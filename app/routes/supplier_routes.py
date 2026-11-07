from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.auth_service import admin_required
from app.models.supplier import Supplier

bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@bp.route('/', methods=['GET'])
@admin_required
def index():
    search = request.args.get('search', '').strip()
    suppliers = Supplier.list_all(search=search)
    return render_template('suppliers/index.html', suppliers=suppliers, search=search)

@bp.route('/create', methods=['POST'])
@admin_required
def create():
    name = request.form.get('name', '').strip()
    contact_person = request.form.get('contact_person', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    if not name:
        flash("Supplier name is required.", "danger")
        return redirect(url_for('suppliers.index'))

    try:
        Supplier.create(name, contact_person, email, phone, address)
        flash(f"Supplier '{name}' added successfully!", "success")
    except Exception as e:
        flash(f"Error adding supplier: {str(e)}", "danger")

    return redirect(url_for('suppliers.index'))

@bp.route('/edit/<int:supplier_id>', methods=['POST'])
@admin_required
def edit(supplier_id):
    name = request.form.get('name', '').strip()
    contact_person = request.form.get('contact_person', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    if not name:
        flash("Supplier name is required.", "danger")
        return redirect(url_for('suppliers.index'))

    try:
        Supplier.update(supplier_id, name, contact_person, email, phone, address)
        flash(f"Supplier '{name}' updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating supplier: {str(e)}", "danger")

    return redirect(url_for('suppliers.index'))

@bp.route('/delete/<int:supplier_id>', methods=['POST'])
@admin_required
def delete(supplier_id):
    try:
        Supplier.delete(supplier_id)
        flash("Supplier deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting supplier: {str(e)}", "danger")

    return redirect(url_for('suppliers.index'))
