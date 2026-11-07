import os
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, session
from app import db
from app.routes import auth_bp, dashboard_bp, pos_bp, product_bp, supplier_bp, inventory_bp, report_bp

def create_app(test_config=None):
    """Application factory for GreenLeaf Grocers."""
    # Load environment variables from .env file if present (skip during pytest execution to respect test fixtures)
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    default_db = os.path.join(app.root_path, '..', 'greenleaf.db')

    # Environment resolution
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    is_production = flask_env in ('production', 'prod')

    # 1. Secret Key Configuration:
    # Load SECRET_KEY from environment variable; remove any insecure hardcoded fallback.
    # In production, a missing SECRET_KEY is fatal. In development, generate an ephemeral random key if unset.
    secret_key = os.environ.get('SECRET_KEY')
    if test_config and 'SECRET_KEY' in test_config:
        secret_key = test_config['SECRET_KEY']
    elif not secret_key:
        if is_production:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: The SECRET_KEY environment variable is missing. "
                "In production, a strong, unpredictable SECRET_KEY must be configured via environment variables."
            )
        else:
            # Ephemeral random key for development instance (never a static hardcoded fallback)
            secret_key = secrets.token_hex(32)

    # 2. Session Cookie Settings:
    # HTTPOnly: True prevents JavaScript from reading session cookies (XSS mitigation).
    # SameSite: 'Lax' protects against cross-site request forgery while preserving navigation.
    # Secure: True in production (HTTPS only); False in local development for HTTP compatibility.
    cookie_secure_env = os.environ.get('SESSION_COOKIE_SECURE')
    if cookie_secure_env is not None:
        session_cookie_secure = cookie_secure_env.lower() in ('true', '1', 'yes')
    else:
        session_cookie_secure = is_production

    # 3. Debug Configuration:
    # Debug mode is strictly disabled in production. Configurable via FLASK_DEBUG in development.
    if is_production:
        debug_mode = False
    else:
        flask_debug_env = os.environ.get('FLASK_DEBUG')
        if flask_debug_env is not None:
            debug_mode = flask_debug_env.lower() in ('true', '1', 'yes')
        else:
            debug_mode = False

    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=default_db,
        DEBUG=debug_mode,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=session_cookie_secure,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Initialize DB extensions and teardown
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(report_bp)

    # Template filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"${float(val):,.2f}"
        except (ValueError, TypeError):
            return "$0.00"

    @app.template_filter('dateformat')
    def dateformat_filter(val, fmt='%b %d, %Y'):
        if not val:
            return 'N/A'
        try:
            if isinstance(val, str):
                # parse YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
                if ' ' in val:
                    dt = datetime.strptime(val.split('.')[0], '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.strptime(val, '%Y-%m-%d')
            else:
                dt = val
            return dt.strftime(fmt)
        except Exception:
            return str(val)

    # Context processor for global UI elements (user, alert counters in sidebar)
    @app.context_processor
    def inject_global_vars():
        alert_counts = {'low_stock': 0, 'expiring': 0}
        current_user = None
        if 'user_id' in session:
            current_user = {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role')
            }
            try:
                # Query quick badge counts without breaking if table not yet initialized
                low = db.query_db("SELECT COUNT(*) as cnt FROM products WHERE quantity <= reorder_level", one=True)
                exp = db.query_db("SELECT COUNT(*) as cnt FROM products WHERE expiry_date <= DATE('now', '+15 days')", one=True)
                if low:
                    alert_counts['low_stock'] = low['cnt']
                if exp:
                    alert_counts['expiring'] = exp['cnt']
            except Exception:
                pass

        return {
            'current_user': current_user,
            'alert_counts': alert_counts,
            'current_year': datetime.now().year,
            'today_date': datetime.now().strftime('%Y-%m-%d')
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app
