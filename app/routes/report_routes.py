from datetime import datetime
from flask import Blueprint, render_template, request, Response
from app.services.auth_service import admin_required
from app.services.report_service import ReportService

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@admin_required
def index():
    """Main Reports Hub."""
    today = datetime.now().strftime('%Y-%m-%d')
    this_month = datetime.now().strftime('%Y-%m')
    
    daily = ReportService.get_daily_sales_report(today)
    monthly = ReportService.get_monthly_sales_report(this_month)
    low_stock = ReportService.get_low_stock_report()
    expiry = ReportService.get_expiry_report()

    return render_template(
        'reports/index.html',
        today=today,
        this_month=this_month,
        daily=daily,
        monthly=monthly,
        low_stock_count=len(low_stock),
        expiry_count=len(expiry)
    )

@bp.route('/daily')
@admin_required
def daily():
    """Daily sales report."""
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    data = ReportService.get_daily_sales_report(target_date)
    return render_template('reports/daily.html', data=data, target_date=target_date)

@bp.route('/daily/csv')
@admin_required
def daily_csv():
    """Export daily sales to CSV."""
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    csv_data = ReportService.export_daily_sales_csv(target_date)
    filename = f"greenleaf_daily_sales_{target_date}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@bp.route('/monthly')
@admin_required
def monthly():
    """Monthly sales report."""
    year_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    data = ReportService.get_monthly_sales_report(year_month)
    return render_template('reports/monthly.html', data=data, year_month=year_month)

@bp.route('/monthly/csv')
@admin_required
def monthly_csv():
    """Export monthly sales to CSV."""
    year_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    csv_data = ReportService.export_monthly_sales_csv(year_month)
    filename = f"greenleaf_monthly_sales_{year_month}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@bp.route('/product-performance')
@admin_required
def product_performance():
    """Product performance and profitability report."""
    records = ReportService.get_product_performance_report()
    return render_template('reports/product_performance.html', records=records)

@bp.route('/product-performance/csv')
@admin_required
def product_performance_csv():
    """Export product performance report to CSV."""
    csv_data = ReportService.export_product_performance_csv()
    filename = f"greenleaf_product_performance_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@bp.route('/low-stock')
@admin_required
def low_stock():
    """Low-stock report."""
    records = ReportService.get_low_stock_report()
    return render_template('reports/low_stock.html', records=records)

@bp.route('/low-stock/csv')
@admin_required
def low_stock_csv():
    """Export low stock report to CSV."""
    csv_data = ReportService.export_low_stock_csv()
    filename = f"greenleaf_low_stock_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@bp.route('/expiry')
@admin_required
def expiry():
    """Expiry report."""
    days = int(request.args.get('days', 15))
    records = ReportService.get_expiry_report(days=days)
    return render_template('reports/expiry.html', records=records, days=days)

@bp.route('/expiry/csv')
@admin_required
def expiry_csv():
    """Export expiry report to CSV."""
    csv_data = ReportService.export_expiry_csv()
    filename = f"greenleaf_expiry_report_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
