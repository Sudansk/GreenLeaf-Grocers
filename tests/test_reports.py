from datetime import datetime

def test_reports_hub(admin_client):
    res = admin_client.get('/reports/')
    assert res.status_code == 200
    assert b'Reports & Business Intelligence Hub' in res.data
    assert b'Daily Sales Report' in res.data
    assert b'Monthly Sales Report' in res.data
    assert b'Product Profitability' in res.data

def test_daily_sales_report_and_csv(admin_client):
    today = datetime.now().strftime('%Y-%m-%d')
    res = admin_client.get(f'/reports/daily?date={today}')
    assert res.status_code == 200
    assert b'Daily Sales Performance Report' in res.data

    csv_res = admin_client.get(f'/reports/daily/csv?date={today}')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Invoice Number' in csv_res.data

def test_monthly_sales_report_and_csv(admin_client):
    this_month = datetime.now().strftime('%Y-%m')
    res = admin_client.get(f'/reports/monthly?month={this_month}')
    assert res.status_code == 200
    assert b'Monthly Sales Performance Report' in res.data

    csv_res = admin_client.get(f'/reports/monthly/csv?month={this_month}')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Transactions' in csv_res.data

def test_product_performance_report_and_csv(admin_client):
    res = admin_client.get('/reports/product-performance')
    assert res.status_code == 200
    assert b'Product Sales Performance & Margins' in res.data

    csv_res = admin_client.get('/reports/product-performance/csv')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Gross Profit' in csv_res.data

def test_low_stock_report_and_csv(admin_client):
    res = admin_client.get('/reports/low-stock')
    assert res.status_code == 200
    assert b'Low-Stock & Reorder Report' in res.data

    csv_res = admin_client.get('/reports/low-stock/csv')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Reorder Level' in csv_res.data

def test_expiry_report_and_csv(admin_client):
    res = admin_client.get('/reports/expiry?days=15')
    assert res.status_code == 200
    assert b'Expiry & Perishable Quality Control Report' in res.data

    csv_res = admin_client.get('/reports/expiry/csv')
    assert csv_res.status_code == 200
    assert 'text/csv' in csv_res.content_type
    assert b'Expiry Date' in csv_res.data
