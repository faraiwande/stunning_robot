import os 
import logging
from flask import Flask, jsonify
from datetime import datetime, timezone
from llm_service.flask_config import Config

# Configure logging before creating the app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    try:
        logger.info("Initializing Flask application...")
        app = Flask(__name__)
        app.config.from_object(Config)

        def health():
            logger.info("health check endpoint accessed")
            return jsonify({
                "status": "ok",
                "message": "LLM Service API Running !",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 200



        logger.info("LLM Service initialized successfully")
        return app

    except Exception as e:
        logger.critical(f"Failed to initialize Flask LLM APIService : {str(e)}")
        raise
