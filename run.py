
import os
from dotenv import load_dotenv
from app import create_app, db

# Load environment configuration
load_dotenv()

# Create Flask application
app = create_app()

# Initialize database whenever the application starts.
# This also runs when Gunicorn imports run:app.
with app.app_context():
    db.init_db()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    is_production = flask_env in ('production', 'prod')

    if is_production:
        debug_mode = False
    else:
        flask_debug_env = os.environ.get('FLASK_DEBUG')
        if flask_debug_env is not None:
            debug_mode = flask_debug_env.lower() in ('true', '1', 'yes')
        else:
            debug_mode = True

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
