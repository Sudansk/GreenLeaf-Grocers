from app.routes.auth_routes import bp as auth_bp
from app.routes.dashboard_routes import bp as dashboard_bp
from app.routes.pos_routes import bp as pos_bp
from app.routes.product_routes import bp as product_bp
from app.routes.supplier_routes import bp as supplier_bp
from app.routes.inventory_routes import bp as inventory_bp
from app.routes.report_routes import bp as report_bp

__all__ = [
    'auth_bp', 'dashboard_bp', 'pos_bp', 'product_bp',
    'supplier_bp', 'inventory_bp', 'report_bp'
]
