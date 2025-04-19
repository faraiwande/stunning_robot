import os
import logging
from flask import Flask
from flasgger import Swagger
from flask_migrate import Migrate

from marketplace_service.routes import mp_routes
from marketplace_service.flask_config import Config
from marketplace_service.models.mp_models import db


migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'bot_service.db')
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)


    if app.config.get("ENV") != "production":
        with app.app_context():
            logging.info("Creating database tables (non-production environment)...")
            db.create_all()

    # Health Route
    @app.route('/')
    def index():
        return {"message": "Welcome to the Marketplace Service API!"}, 200

    # Register routes
    app.register_blueprint(mp_routes.routes_bp)
    Swagger(app)
    return app
