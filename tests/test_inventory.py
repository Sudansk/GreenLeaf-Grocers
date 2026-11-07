from app.models.product import Product
from app.services.inventory_service import InventoryService
from app.models.stock_movement import StockMovement

def test_inventory_overview_page(admin_client):
    res = admin_client.get('/inventory/')
    assert res.status_code == 200
    assert b'Inventory & Stock Control' in res.data
    assert b'Retail Valuation' in res.data

def test_low_stock_detection(admin_client, app):
    # In conftest, TEST-MLK-01 has quantity 5, reorder_level 10 -> Low stock!
    res = admin_client.get('/inventory/low-stock')
    assert res.status_code == 200
    assert b'Test Milk' in res.data
    assert b'TEST-MLK-01' in res.data

    with app.app_context():
        low_items = InventoryService.get_low_stock_products()
        names = [item['name'] for item in low_items]
        assert 'Test Milk' in names

def test_expiry_alerts_detection(admin_client, app):
    # In conftest, TEST-BRD-01 expires in 5 days, TEST-YOG-EXP expired 2 days ago
    res = admin_client.get('/inventory/expiry')
    assert res.status_code == 200
    assert b'Test Bread' in res.data
    assert b'Test Yogurt Expired' in res.data

    with app.app_context():
        expiring = InventoryService.get_expiring_products(days=15)
        names = [item['name'] for item in expiring]
        assert 'Test Bread' in names
        assert 'Test Yogurt Expired' in names

def test_stock_manual_adjustment(admin_client, app):
    with app.app_context():
        p = Product.get_by_sku('TEST-APP-01')
        pid = p['id']
        start_qty = p['quantity']

    # Restock 20 units
    res = admin_client.post('/inventory/adjust', data={
        'product_id': str(pid),
        'movement_type': 'RESTOCK',
        'quantity': '20',
        'reference': 'PO-TEST-101',
        'notes': 'Weekly restock shipment'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Stock adjusted successfully!' in res.data

    with app.app_context():
        updated = Product.get_by_id(pid)
        assert updated['quantity'] == start_qty + 20

        # Verify audit record
        movements = StockMovement.list_recent(limit=1, product_id=pid)
        assert movements[0]['movement_type'] == 'RESTOCK'
        assert movements[0]['reference_id'] == 'PO-TEST-101'
        assert movements[0]['quantity'] == 20

def test_stock_movement_audit_view(admin_client):
    res = admin_client.get('/inventory/movements')
    assert res.status_code == 200
    assert b'Stock Movement Audit Trail' in res.data
