import json
from app.models.product import Product
from app.models.sale import Sale
from app.models.stock_movement import StockMovement

def test_pos_terminal_renders(cashier_client):
    res = cashier_client.get('/pos/')
    assert res.status_code == 200
    assert b'Point of Sale (POS) Terminal' in res.data
    assert b'Active Cart' in res.data

def test_pos_api_products(cashier_client):
    res = cashier_client.get('/pos/api/products')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 4
    # Check item structure
    skus = [p['sku'] for p in data]
    assert 'TEST-APP-01' in skus

def test_pos_successful_checkout(cashier_client, app):
    with app.app_context():
        p = Product.get_by_sku('TEST-APP-01')
        pid = p['id']
        initial_qty = p['quantity']

    payload = {
        'customer_name': 'Alice Smith',
        'customer_phone': '555-9876',
        'discount_percent': 10.0,
        'payment_method': 'Cash',
        'items': [
            {'product_id': pid, 'quantity': 5, 'unit_price': 2.00}
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
    assert 'invoice_number' in data
    inv_num = data['invoice_number']

    with app.app_context():
        # Verify stock was atomically deducted
        updated_p = Product.get_by_id(pid)
        assert updated_p['quantity'] == initial_qty - 5

        # Verify sale record
        sale = Sale.get_by_invoice(inv_num)
        assert sale is not None
        assert sale['customer_name'] == 'Alice Smith'
        assert sale['subtotal'] == 10.00
        assert sale['discount_amount'] == 1.00
        assert sale['grand_total'] == 9.00
        assert sale['payment_method'] == 'Cash'

        # Verify sale items
        items = Sale.get_sale_items(sale['id'])
        assert len(items) == 1
        assert items[0]['quantity'] == 5
        assert items[0]['line_total'] == 10.00

        # Verify stock movement record
        movements = StockMovement.list_recent(limit=1, product_id=pid)
        assert len(movements) == 1
        assert movements[0]['movement_type'] == 'SALE'
        assert movements[0]['quantity'] == 5
        assert movements[0]['previous_quantity'] == initial_qty
        assert movements[0]['new_quantity'] == initial_qty - 5

def test_pos_insufficient_stock_rejection(cashier_client, app):
    with app.app_context():
        p = Product.get_by_sku('TEST-MLK-01')
        pid = p['id']
        stock_available = p['quantity']  # 5 in stock

    payload = {
        'customer_name': 'Bob Buyer',
        'items': [
            {'product_id': pid, 'quantity': stock_available + 10}  # Request 15
        ]
    }

    res = cashier_client.post(
        '/pos/checkout',
        data=json.dumps(payload),
        content_type='application/json'
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'Insufficient stock' in data['message']

    with app.app_context():
        # Stock must remain unchanged
        p_after = Product.get_by_id(pid)
        assert p_after['quantity'] == stock_available

def test_pos_view_printable_invoice(cashier_client, app):
    # First create a sale
    with app.app_context():
        p = Product.get_by_sku('TEST-APP-01')
        result = Sale.create_sale(
            cashier_id=2, customer_name='Test Buyer', customer_phone='',
            items=[{'product_id': p['id'], 'quantity': 2, 'unit_price': 2.00}],
            discount_percent=0.0, payment_method='Card'
        )
        inv = result['invoice_number']

    res = cashier_client.get(f'/pos/invoice/{inv}')
    assert res.status_code == 200
    assert inv.encode() in res.data
    assert b'TAX INVOICE' in res.data
    assert b'Test Buyer' in res.data
    assert b'Print Invoice' in res.data
