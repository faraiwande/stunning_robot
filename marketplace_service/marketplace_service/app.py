import os
import logging
from flask import Flask
from flask_migrate import Migrate

from marketplace_service.routes import mp_routes
from marketplace_service.flask_config import Config
from marketplace_service.models.mp_models import db

# Configure logging before creating the app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marketplace_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

migrate = Migrate()

def create_app():
    try:
        logger.info("Initializing Flask application...")
        app = Flask(__name__)
        app.config.from_object(Config)

        # Database configuration
        db_uri = os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bot_service.db')
        )
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        logger.info(f"Database URI configured: {db_uri.split('//')[0]}//*****")  # Mask sensitive info

        # Initialize extensions
        logger.info("Initializing database extensions...")
        db.init_app(app)
        migrate.init_app(app, db)
        logger.info("Database extensions initialized successfully")

        # Database table creation for non-production environments
        if app.config.get("ENV") != "production":
            with app.app_context():
                logger.info("Non-production environment detected, creating database tables...")
                try:
                    db.create_all()
                    logger.info("Database tables created successfully")
                except Exception as e:
                    logger.error(f"Error creating database tables: {str(e)}")
                    raise

        # Health Route
        @app.route('/')
        def index():
            logger.info("Root endpoint accessed")
            return {"message": "Welcome to the Marketplace Service API!"}, 200

        # Register routes
        logger.info("Registering application blueprints...")
        app.register_blueprint(mp_routes.routes_bp)
        

        logger.info("Flask application initialized successfully")
        return app

    except Exception as e:
        logger.critical(f"Failed to initialize Flask application: {str(e)}")
        raise

# Configure logging for SQLAlchemy if needed
if os.environ.get('FLASK_ENV') == 'development':
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)