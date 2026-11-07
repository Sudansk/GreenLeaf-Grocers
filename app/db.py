import sqlite3
import os
from datetime import datetime, date
from flask import g, current_app

# Register standard adapters/converters for Python 3.12+
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat(sep=' '))
sqlite3.register_converter("date", lambda b: b.decode("utf-8"))
sqlite3.register_converter("timestamp", lambda b: b.decode("utf-8"))

def get_db():
    """Get database connection for current application context."""
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE', 'greenleaf.db')
        # Ensure parent directory exists if path contains directories
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Close the database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initialize database from schema.sql."""
    if app:
        with app.app_context():
            db = get_db()
            with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r', encoding='utf-8') as f:
                db.executescript(f.read())
            db.commit()
    else:
        db = get_db()
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    """Helper to run SELECT queries returning dict-like Rows."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    """Helper to run INSERT, UPDATE, DELETE queries."""
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cur.lastrowid
    rowcount = cur.rowcount
    cur.close()
    return last_id, rowcount

def init_app(app):
    """Register database teardown with Flask app."""
    app.teardown_appcontext(close_db)
