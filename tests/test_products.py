from datetime import datetime, timedelta
from app.models.product import Product

def test_list_products(admin_client):
    res = admin_client.get('/products/')
    assert res.status_code == 200
    assert b'Test Apples' in res.data
    assert b'TEST-APP-01' in res.data
    assert b'Test Milk' in res.data

def test_create_product(admin_client, app):
    tomorrow = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    res = admin_client.post('/products/create', data={
        'name': 'Organic Strawberries',
        'sku': 'PROD-STR-NEW',
        'category': 'Fresh Produce',
        'cost_price': '2.00',
        'selling_price': '4.50',
        'quantity': '25',
        'reorder_level': '5',
        'expiry_date': tomorrow,
        'unit': 'pack',
        'supplier_id': '1'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Organic Strawberries' in res.data
    assert b'added successfully' in res.data

    with app.app_context():
        p = Product.get_by_sku('PROD-STR-NEW')
        assert p is not None
        assert p['name'] == 'Organic Strawberries'
        assert p['quantity'] == 25

def test_prevent_duplicate_sku(admin_client):
    tomorrow = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    res = admin_client.post('/products/create', data={
        'name': 'Duplicate Apples',
        'sku': 'TEST-APP-01',  # Already exists in conftest
        'category': 'Fresh Produce',
        'cost_price': '1.00',
        'selling_price': '2.00',
        'quantity': '10',
        'reorder_level': '5',
        'expiry_date': tomorrow,
        'unit': 'kg'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'already exists' in res.data

def test_update_product(admin_client, app):
    tomorrow = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    with app.app_context():
        p = Product.get_by_sku('TEST-APP-01')
        pid = p['id']

    res = admin_client.post(f'/products/edit/{pid}', data={
        'name': 'Updated Honeycrisp Apples',
        'sku': 'TEST-APP-01',
        'category': 'Fresh Produce',
        'cost_price': '1.20',
        'selling_price': '2.80',
        'reorder_level': '12',
        'expiry_date': tomorrow,
        'unit': 'kg'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'updated successfully' in res.data

    with app.app_context():
        updated = Product.get_by_id(pid)
        assert updated['name'] == 'Updated Honeycrisp Apples'
        assert updated['selling_price'] == 2.80
        assert updated['reorder_level'] == 12

def test_product_detail_view(admin_client, app):
    with app.app_context():
        p = Product.get_by_sku('TEST-APP-01')
        pid = p['id']
    res = admin_client.get(f'/products/{pid}')
    assert res.status_code == 200
    assert b'Product Overview & Movement History' in res.data
    assert b'TEST-APP-01' in res.data
