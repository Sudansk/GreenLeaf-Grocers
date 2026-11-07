from werkzeug.security import generate_password_hash, check_password_hash
from app.db import query_db, execute_db

class User:
    @staticmethod
    def create(username, password, full_name, role='cashier'):
        """Create a new user with securely hashed password."""
        hashed = generate_password_hash(password, method='scrypt')
        user_id, _ = execute_db(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username.strip().lower(), hashed, full_name.strip(), role)
        )
        return user_id

    @staticmethod
    def get_by_id(user_id):
        """Fetch user by id."""
        return query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)

    @staticmethod
    def get_by_username(username):
        """Fetch user by username (case-insensitive)."""
        return query_db("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),), one=True)

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify password against stored hash."""
        return check_password_hash(stored_hash, password)

    @staticmethod
    def list_all():
        """List all active users."""
        return query_db("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id ASC")

    @staticmethod
    def update_password(user_id, new_password):
        """Update user password."""
        hashed = generate_password_hash(new_password, method='scrypt')
        execute_db("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
