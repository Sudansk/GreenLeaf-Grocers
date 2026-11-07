from functools import wraps
from flask import session, redirect, url_for, flash, abort, g
from app.models.user import User

def login_required(f):
    """Decorator to enforce login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to enforce admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash("Access denied: Admin privileges required.", "danger")
            return redirect(url_for('pos.index'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate(username, password):
    """Verify user credentials and return user row or None."""
    user = User.get_by_username(username)
    if not user:
        return None
    if not User.verify_password(user['password_hash'], password):
        return None
    if not user['is_active']:
        return None
    return user

def login_user(user):
    """Set session data for authenticated user."""
    session.clear()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['full_name'] = user['full_name']
    session['role'] = user['role']

def logout_user():
    """Clear user session."""
    session.clear()

def get_current_user():
    """Get currently logged-in user dict from session or DB."""
    if 'user_id' in session:
        return {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        }
    return None
