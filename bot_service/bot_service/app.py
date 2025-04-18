import os 
import logging
from flask import Flask
from flask_migrate import Migrate
from bot_service.flask_config import Config
from bot_service.models.bot_service_models import db

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        
        'DATABASE_URL', 'sqlite:///bot_service.db'
    )
    
    @app.route('/')
    def index():
        return {"message":"Welcome to the Bot Service API!"}, 200
    
    
     # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    if app.config.get("ENV") != "production":
        with app.app_context():
            logging.info("Creating database tables (non-production environment)...")
            db.create_all()
    
    return app