import json
import os
import pytest
from app import create_app
from app.models.product import Product
from app.models.sale import Sale

def test_checkout_ignores_frontend_price_tampering(cashier_client, app):
    """
    Security Test 1: Verify that client-supplied unit prices are completely ignored
    and authoritative product prices from the database are strictly enforced.
    """
    with app.app_context():
        product = Product.get_by_sku('TEST-APP-01')
        pid = product['id']
        actual_price = float(product['selling_price'])  # 2.00 in test fixture
        initial_qty = product['quantity']

    qty_to_buy = 4
    # Attempt price tampering: pass $0.05 instead of $2.00
    tampered_price = 0.05
    payload = {
        'customer_name': 'Price Tamperer',
        'customer_phone': '555-0000',
        'discount_percent': 0.0,
        'payment_method': 'Cash',
        'items': [
            {
                'product_id': pid,
                'quantity': qty_to_buy,
                'unit_price': tampered_price  # Malicious price injection
            }
        ]
    }

    res = cashier_client.post(
        '/pos/checkout',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    inv_num = data['invoice_number']

    with app.app_context():
        sale = Sale.get_by_invoice(inv_num)
        assert sale is not None
        # Subtotal must be calculated using 2.00 * 4 = 8.00, NOT 0.05 * 4 = 0.20
        expected_subtotal = round(actual_price * qty_to_buy, 2)
        assert sale['subtotal'] == expected_subtotal
        assert sale['grand_total'] == expected_subtotal

        # Verify sale line item in database
        items = Sale.get_sale_items(sale['id'])
        assert len(items) == 1
        assert items[0]['unit_price'] == actual_price
        assert items[0]['line_total'] == expected_subtotal

        # Verify atomic stock deduction
        updated_prod = Product.get_by_id(pid)
        assert updated_prod['quantity'] == initial_qty - qty_to_buy

def test_checkout_rejects_negative_or_zero_quantity(cashier_client, app):
    """
    Security Test 2: Verify that checkout rejects invalid, zero, or negative quantities.
    """
    with app.app_context():
        product = Product.get_by_sku('TEST-APP-01')
        pid = product['id']
        initial_qty = product['quantity']

    for invalid_qty in [0, -1, -10]:
        payload = {
            'customer_name': 'Zero Qty Test',
            'discount_percent': 0.0,
            'payment_method': 'Cash',
            'items': [{'product_id': pid, 'quantity': invalid_qty}]
        }
        res = cashier_client.post(
            '/pos/checkout',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['success'] is False

    with app.app_context():
        # Stock must remain unchanged
        updated_prod = Product.get_by_id(pid)
        assert updated_prod['quantity'] == initial_qty

def test_checkout_rejects_out_of_bounds_discounts(cashier_client, app):
    """
    Security Test 3: Verify that discount percentage is strictly validated between 0 and 100.
    """
    with app.app_context():
        product = Product.get_by_sku('TEST-APP-01')
        pid = product['id']

    for invalid_discount in [-5.0, 105.0, 999.0]:
        payload = {
            'customer_name': 'Discount Exploit Test',
            'discount_percent': invalid_discount,
            'payment_method': 'Cash',
            'items': [{'product_id': pid, 'quantity': 1}]
        }
        res = cashier_client.post(
            '/pos/checkout',
            data=json.dumps(payload),
            content_type='application/json'
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data['success'] is False
        assert 'discount' in data['message'].lower()

def test_production_fails_without_secret_key(monkeypatch):
    """
    Security Test 4: Verify that in production, startup fails if SECRET_KEY is missing.
    Insecure fallback secret keys must not be used.
    """
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.delenv('SECRET_KEY', raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        create_app()
    assert "SECRET_KEY environment variable is missing" in str(exc_info.value)

def test_production_succeeds_with_configured_secret_key(monkeypatch, tmp_path):
    """
    Security Test 5: Verify that when SECRET_KEY is set in production, it is loaded properly.
    """
    prod_key = "secure-production-random-token-64-bytes-abc123"
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', prod_key)

    db_path = str(tmp_path / "test_prod.db")
    prod_app = create_app({'DATABASE': db_path, 'SECRET_KEY': prod_key})
    assert prod_app.config['SECRET_KEY'] == prod_key

def test_session_cookie_settings_in_dev_and_prod(monkeypatch, tmp_path):
    """
    Security Test 6: Verify HTTPOnly, SameSite, and Secure flags across environments.
    """
    db_path = str(tmp_path / "test_cookie.db")

    # In development: HTTPOnly=True, SameSite='Lax', Secure=False
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('SECRET_KEY', 'dev-key-123')
    monkeypatch.delenv('SESSION_COOKIE_SECURE', raising=False)
    dev_app = create_app({'DATABASE': db_path, 'SECRET_KEY': 'dev-key-123'})
    assert dev_app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert dev_app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert dev_app.config['SESSION_COOKIE_SECURE'] is False

    # In production: Secure=True
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'prod-key-123')
    monkeypatch.delenv('SESSION_COOKIE_SECURE', raising=False)
    prod_app = create_app({'DATABASE': db_path, 'SECRET_KEY': 'prod-key-123'})
    assert prod_app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert prod_app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert prod_app.config['SESSION_COOKIE_SECURE'] is True

def test_debug_mode_disabled_in_production(monkeypatch, tmp_path):
    """
    Security Test 7: Verify that debug mode is strictly disabled in production even if FLASK_DEBUG=True.
    """
    db_path = str(tmp_path / "test_debug.db")
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('FLASK_DEBUG', 'True')
    monkeypatch.setenv('SECRET_KEY', 'prod-key-debug-test')

    prod_app = create_app({'DATABASE': db_path, 'SECRET_KEY': 'prod-key-debug-test'})
    assert prod_app.config['DEBUG'] is False
