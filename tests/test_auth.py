def test_login_page_renders(client):
    res = client.get('/login')
    assert res.status_code == 200
    assert b'GreenLeaf Grocers' in res.data
    assert b'Sign In' in res.data

def test_admin_login_success(client):
    res = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back, Test Admin!' in res.data
    assert b'Executive Analytics Dashboard' in res.data

def test_cashier_login_redirects_to_pos(client):
    res = client.post('/login', data={'username': 'cashier', 'password': 'cashier123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back, Test Cashier!' in res.data
    assert b'Point of Sale (POS) Terminal' in res.data

def test_login_failure_invalid_credentials(client):
    res = client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Invalid username or password' in res.data

def test_role_based_access_control(cashier_client):
    # Cashier cannot access admin dashboard
    res = cashier_client.get('/dashboard', follow_redirects=True)
    assert res.status_code == 200
    # Redirected to POS terminal
    assert b'Point of Sale (POS) Terminal' in res.data

    # Cashier cannot access product create
    res = cashier_client.get('/products/create', follow_redirects=True)
    assert res.status_code == 200
    assert b'Access denied: Admin privileges required.' in res.data

    # Cashier cannot access reports hub
    res = cashier_client.get('/reports/', follow_redirects=True)
    assert res.status_code == 200
    assert b'Access denied: Admin privileges required.' in res.data

def test_logout(admin_client):
    res = admin_client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'You have been logged out successfully.' in res.data
    # Accessing dashboard after logout redirects to login
    res = admin_client.get('/dashboard', follow_redirects=True)
    assert b'Please log in to access this page.' in res.data
