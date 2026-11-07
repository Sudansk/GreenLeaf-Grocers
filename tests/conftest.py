import os
import tempfile
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.product import Product

@pytest.fixture
def app():
    """Create and configure a clean temporary Flask application for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test-secret-key-greenleaf'
    })

    with app.app_context():
        db.init_db()
        # Seed test users
        admin_id = User.create('admin', 'admin123', 'Test Admin', 'admin')
        cashier_id = User.create('cashier', 'cashier123', 'Test Cashier', 'cashier')

        # Seed test supplier
        sup_id = Supplier.create('Fresh Farm Co', 'John Contact', 'john@farm.com', '555-1234', '123 Farm Way')

        # Seed test products
        today = datetime.now().date()
        # In stock normal product
        Product.create(
            name='Test Apples', sku='TEST-APP-01', category='Fresh Produce',
            cost_price=1.00, selling_price=2.00, quantity=50, reorder_level=10,
            expiry_date=today + timedelta(days=30), unit='kg', supplier_id=sup_id, user_id=admin_id
        )
        # Low stock product
        Product.create(
            name='Test Milk', sku='TEST-MLK-01', category='Dairy & Eggs',
            cost_price=2.00, selling_price=3.50, quantity=5, reorder_level=10,
            expiry_date=today + timedelta(days=20), unit='bottle', supplier_id=sup_id, user_id=admin_id
        )
        # Expiring soon product
        Product.create(
            name='Test Bread', sku='TEST-BRD-01', category='Bakery',
            cost_price=1.50, selling_price=3.00, quantity=15, reorder_level=5,
            expiry_date=today + timedelta(days=5), unit='loaf', supplier_id=sup_id, user_id=admin_id
        )
        # Expired product
        Product.create(
            name='Test Yogurt Expired', sku='TEST-YOG-EXP', category='Dairy & Eggs',
            cost_price=1.00, selling_price=2.50, quantity=8, reorder_level=5,
            expiry_date=today - timedelta(days=2), unit='tub', supplier_id=sup_id, user_id=admin_id
        )

    yield app

    # Cleanup
    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except PermissionError:
            pass

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def admin_client(client):
    """Client authenticated as Admin."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['full_name'] = 'Test Admin'
        sess['role'] = 'admin'
    return client

@pytest.fixture
def cashier_client(client):
    """Client authenticated as Cashier."""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'cashier'
        sess['full_name'] = 'Test Cashier'
        sess['role'] = 'cashier'
    return client
