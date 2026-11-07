import os
from dotenv import load_dotenv
from app import create_app, db

# Load environment configuration from .env
load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Ensure database tables exist
    with app.app_context():
        db.init_db()

    port = int(os.environ.get('PORT', 5000))
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    is_production = flask_env in ('production', 'prod')

    # Security: Debug mode is configurable via FLASK_DEBUG, but strictly disabled in production
    if is_production:
        debug_mode = False
    else:
        flask_debug_env = os.environ.get('FLASK_DEBUG')
        if flask_debug_env is not None:
            debug_mode = flask_debug_env.lower() in ('true', '1', 'yes')
        else:
            debug_mode = True  # Default to True only during local development

    app.run(host='127.0.0.1', port=port, debug=debug_mode)
