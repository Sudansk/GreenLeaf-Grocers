from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import authenticate, login_user, logout_user

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('pos.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('auth/login.html', username=username)

        user = authenticate(username, password)
        if user:
            login_user(user)
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user['role'] == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('pos.index'))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template('auth/login.html')

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.login'))
