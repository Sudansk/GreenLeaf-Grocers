from flask import Blueprint, render_template, redirect, url_for, session
from app.services.auth_service import login_required, admin_required
from app.services.analytics_service import AnalyticsService

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    # If cashier logs in, redirect directly to POS terminal
    if session.get('role') != 'admin':
        return redirect(url_for('pos.index'))

    # Metrics & Analytics using Pandas
    metrics = AnalyticsService.get_dashboard_metrics()
    daily_df = AnalyticsService.get_daily_revenue_trend(days=30)
    top_df = AnalyticsService.get_top_selling_products(limit=10)
    category_df = AnalyticsService.get_category_sales_share()
    payment_df = AnalyticsService.get_payment_method_stats()
    slow_moving_df = AnalyticsService.get_slow_moving_products(days=30, sales_threshold=2)

    # Plotly interactive charts
    revenue_chart_json = AnalyticsService.build_daily_revenue_chart(daily_df)
    top_products_chart_json = AnalyticsService.build_top_products_chart(top_df)
    category_chart_json = AnalyticsService.build_category_share_chart(category_df)
    payment_chart_json = AnalyticsService.build_payment_method_chart(payment_df)

    return render_template(
        'dashboard/index.html',
        metrics=metrics,
        revenue_chart=revenue_chart_json,
        top_products_chart=top_products_chart_json,
        category_chart=category_chart_json,
        payment_chart=payment_chart_json,
        slow_moving_items=slow_moving_df.to_dict(orient='records')[:8]
    )
