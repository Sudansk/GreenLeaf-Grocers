from app.models.product import Product
from app.models.sale import Sale
from app.services.analytics_service import AnalyticsService

def test_analytics_kpi_metrics(app):
    with app.app_context():
        # Create a test sale
        p = Product.get_by_sku('TEST-APP-01')
        Sale.create_sale(
            cashier_id=1, customer_name='Jane Metric', customer_phone='',
            items=[{'product_id': p['id'], 'quantity': 10, 'unit_price': 2.00}],
            discount_percent=0.0, payment_method='Cash'
        )

        metrics = AnalyticsService.get_dashboard_metrics()
        assert metrics['total_revenue'] == 20.0
        assert metrics['total_sales_count'] == 1
        assert metrics['avg_bill_value'] == 20.0
        assert metrics['total_products'] >= 4
        assert metrics['low_stock_count'] >= 1
        assert metrics['stock_turnover'] >= 0.0

def test_pandas_top_selling_products(app):
    with app.app_context():
        p1 = Product.get_by_sku('TEST-APP-01')
        p2 = Product.get_by_sku('TEST-MLK-01')

        Sale.create_sale(
            cashier_id=1, customer_name='Top Test', customer_phone='',
            items=[
                {'product_id': p1['id'], 'quantity': 8, 'unit_price': 2.00},
                {'product_id': p2['id'], 'quantity': 2, 'unit_price': 3.50}
            ],
            discount_percent=0.0, payment_method='UPI'
        )

        top_df = AnalyticsService.get_top_selling_products(limit=5)
        assert not top_df.empty
        assert top_df.iloc[0]['product_name'] == 'Test Apples'
        assert top_df.iloc[0]['units_sold'] == 8

def test_pandas_slow_moving_products(app):
    with app.app_context():
        # Items with zero sales in period should be flagged as slow-moving
        slow_df = AnalyticsService.get_slow_moving_products(days=30, sales_threshold=2)
        assert not slow_df.empty
        # Products that have 0 sales should be present
        skus = slow_df['sku'].tolist()
        assert 'TEST-BRD-01' in skus

def test_plotly_chart_builders(app):
    with app.app_context():
        daily_df = AnalyticsService.get_daily_revenue_trend(days=30)
        daily_json = AnalyticsService.build_daily_revenue_chart(daily_df)
        assert 'data' in daily_json
        assert 'layout' in daily_json

        top_df = AnalyticsService.get_top_selling_products(limit=5)
        top_json = AnalyticsService.build_top_products_chart(top_df)
        assert 'data' in top_json

        cat_df = AnalyticsService.get_category_sales_share()
        cat_json = AnalyticsService.build_category_share_chart(cat_df)
        assert 'data' in cat_json

def test_dashboard_page_renders_with_plotly(admin_client):
    res = admin_client.get('/dashboard')
    assert res.status_code == 200
    assert b'Executive Analytics Dashboard' in res.data
    assert b'dailyRevenueChart' in res.data
    assert b'topProductsChart' in res.data
    assert b'categoryShareChart' in res.data
    assert b'Slow-Moving Products' in res.data
