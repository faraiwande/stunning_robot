import os
import logging
import json
from flask import Flask, request, jsonify
from datetime import datetime, timezone
from llm_service.flask_config import Config
import ollama

from llm_service.message_handler import handle_message  # <-- import your handler
from llm_service.redis_client import get_history, clear_history, clear_user_state

# --------------------------------------
# Setup Logging
# --------------------------------------
LOG_FILE = "llm_service.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# --------------------------------------
# Flask App Factory
# --------------------------------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/health", methods=["GET"])
    def health_check():
        logger.info("Health check accessed")
        return {
            "status": "ok",
            "service": "llm_service",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, 200

    @app.route("/parse", methods=["POST"])
    def parse():
        data = request.get_json(force=True)
        msg = data.get("message", "").strip()
        if not msg:
            return jsonify({"error": "No message provided"}), 400

        prompt = PROMPT_TEMPLATE.format(message=msg)
        logger.info("LLM prompt sent for parsing")
        try:
            resp = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
            raw = resp["message"]["content"]
            logger.info(f"LLM raw response: {raw}")
            parsed = json.loads(raw)
            return jsonify(parsed), 200
        except Exception as e:
            logger.exception("LLM parsing failed")
            return jsonify({"error": str(e)}), 500

    @app.route("/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        try:
            incoming = request.form
            phone = incoming.get("From", "").split(":")[-1]
            message = incoming.get("Body", "").strip()
            logger.info(f"Incoming WhatsApp message from {phone}: '{message}'")

            if not phone or not message:
                logger.warning("Missing phone or message in request")
                return "Missing phone or message", 400

            # Delegate to your message handler
            response = handle_message(phone, message)
            logger.info(f"Response to {phone}: '{response}'")

            return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response}</Message>
</Response>
""", 200, {'Content-Type': 'application/xml'}

        except Exception as e:
            logger.exception("Error in WhatsApp webhook")
            return "Internal Server Error", 500

    @app.route("/history/<phone>", methods=["GET"])
    def view_history(phone):
        try:
            logger.info(f"History requested for {phone}")
            return jsonify({"phone": phone, "messages": get_history(phone)}), 200
        except Exception as e:
            logger.exception("Error retrieving history")
            return jsonify({"error": "Could not fetch history"}), 500

    @app.route("/reset/<phone>", methods=["POST"])
    def reset_user(phone):
        try:
            clear_user_state(phone)
            clear_history(phone)
            logger.info(f"State and history reset for {phone}")
            return jsonify({"status": "reset", "phone": phone}), 200
        except Exception as e:
            logger.exception("Error resetting user state")
            return jsonify({"error": "Reset failed"}), 500

    logger.info("LLM Flask App initialized")
    return app


