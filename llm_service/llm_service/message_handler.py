import requests
import os
import json
import logging
from .redis_client import (
    get_user_state,
    set_user_state,
    clear_user_state,
    add_to_history
)

logger = logging.getLogger(__name__)

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://127.0.0.1:11434/api/chat")
LISTINGS_API_URL = os.getenv("LISTINGS_API_URL", "http://marketplace_api:5000/listings")
REGISTER_API_URL = os.getenv("REGISTER_API_URL", "http://marketplace_api:5000/register")
REVIEW_API_URL = os.getenv("REVIEW_API_URL", "http://marketplace_api:5000")



# --------------------------------------
# LLM Prompt Template
# --------------------------------------
PROMPT_TEMPLATE = """
You are a helpful assistant for a rural WhatsApp marketplace.

When a user sends a message, your job is to:
1. Determine the intent. One of: [register, sell, buy, review, product_info]
2. Extract any relevant fields from the message.
3. Normalize the location into a district format (e.g., “Gweru” → “Gweru Urban”).
4. Normalize the product name for matching (e.g., “broilers” → “chickens”).
5. Classify the product into a category (e.g., “chickens” → “livestock”).

Respond with valid JSON exactly like this:

{
  "intent": "<intent>",
  "fields": {
    "product_name": "...",
    "normalized_product": "...",
    "category": "...",
    "location": "...",
    // plus other fields as needed
  }
}

User message: "{message}"
"""

# --------------------------------------
# Ollama Configuration
# --------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434/api/chat")
ollama.base_url = OLLAMA_HOST


# Required fields per intent
REQUIRED_FIELDS = {
    "sell": ["product_name", "quantity", "price", "location", "category"],
    "register": ["business_name", "location", "payment_method"],
    "buy": ["product_name", "location"],
    "review": ["rating"]
}

def is_complete(intent, fields):
    return all(f in fields for f in REQUIRED_FIELDS.get(intent, []))

def notify_user(phone, message):
    try:
        res = requests.post(
            os.getenv("TWILIO_WEBHOOK_URL", "http://bot_service:5002/whatsapp"),
            data={
                "From": "whatsapp:+14155238886",  # Replace with your Twilio number
                "To": f"whatsapp:{phone}",
                "Body": message
            }
        )
        res.raise_for_status()
        logger.info(f"Broadcasted WhatsApp message to {phone}")
    except Exception as e:
        logger.error(f"Failed to notify {phone}: {str(e)}")

def handle_message(phone, message):
    message = message.strip().lower()
    logger.info(f"Message from {phone}: {message}")
    add_to_history(phone, "user", message)

    # Step 1: YES/NO confirmation
    if message == "yes":
        state = get_user_state(phone)
        if state and state.get("awaiting_confirmation"):
            fields = state["fields"]
            intent = state["intent"]

            try:
                if intent == "sell":
                    payload = {
                        "phone": phone,
                        "product_name": fields["product_name"],
                        "quantity": fields["quantity"],
                        "price": fields["price"],
                        "location": fields["location"],
                        "category": fields["category"],
                        "description": fields.get("description", "")
                    }
                    url = LISTINGS_API_URL

                elif intent == "register":
                    payload = {
                        "phone": phone,
                        "business_name": fields["business_name"],
                        "location": fields["location"],
                        "payment_method": fields["payment_method"]
                    }
                    url = REGISTER_API_URL

                elif intent == "review":
                    rating = fields["rating"]
                    if not isinstance(rating, int) or rating not in range(1, 6):
                        return "⚠️ Rating must be an integer between 1 and 5."

                    payload = {
                        "rating": rating,
                        "comment": fields.get("comment", "")
                    }
                    url = f"{REVIEW_API_URL}/review/{phone}"

                else:
                    logger.warning(f"Unsupported intent for confirmation: {intent}")
                    return "❌ Sorry, I can’t confirm this action."

                logger.info(f"Posting {intent} for {phone}: {payload}")
                res = requests.post(url, json=payload)
                res.raise_for_status()

                clear_user_state(phone)
                success_msg = f"✅ Your {intent} information has been saved!"
                add_to_history(phone, "bot", success_msg)
                return success_msg

            except Exception as e:
                logger.exception(f"Error posting {intent} for {phone}")
                error_msg = f"⚠️ Something went wrong posting your {intent}. Try again later."
                add_to_history(phone, "bot", error_msg)
                return error_msg

    elif message == "no":
        clear_user_state(phone)
        cancel_msg = "❌ Okay, I’ve cancelled that request. Start over anytime."
        add_to_history(phone, "bot", cancel_msg)
        return cancel_msg

    # Step 2: Send message to LLM
    try:
        res = requests.post(LLM_SERVICE_URL, json={"phone": phone, "message": message})
        res.raise_for_status()
        result = res.json()

        intent = result.get("intent")
        fields = result.get("fields") or {}

        if not intent:
            logger.warning(f"No intent detected for user {phone}")
            return "🤔 I couldn’t understand that. Try again?"

        existing = get_user_state(phone)
        combined_fields = {**existing.get("fields", {}), **fields}

        if is_complete(intent, combined_fields):
            if intent == "buy":
                product = combined_fields["product_name"]
                location = combined_fields["location"]

                try:
                    search_url = f"{LISTINGS_API_URL}/search"
                    res = requests.get(search_url, params={
                        "product_name": product,
                        "location": location
                    })
                    res.raise_for_status()
                    matches = res.json().get("matches", [])

                    if not matches:
                        no_match_msg = f"❌ No sellers currently found for {product} in {location}. We'll let you know when one is available!"
                        add_to_history(phone, "bot", no_match_msg)
                        return no_match_msg

                    match_summary = "\n".join([
                        f"- {m['product_name']} at ${m['price']} ({m['location']}) — seller: {m['seller_phone']}"
                        for m in matches
                    ])
                    buyer_msg = (
                        f"✅ Found {len(matches)} match(es) for {product} in {location}:\n{match_summary}"
                    )
                    add_to_history(phone, "bot", buyer_msg)

                    for m in matches:
                        seller_phone = m["seller_phone"]
                        seller_msg = (
                            f"📢 A buyer is looking for {product} in {location}.\n"
                            f"Your listing for {m['product_name']} at ${m['price']} is a match.\n"
                            f"Reply if you're available!"
                        )
                        notify_user(seller_phone, seller_msg)

                    return buyer_msg

                except Exception as e:
                    logger.exception(f"Error finding matches for buyer {phone}")
                    error_msg = "😓 Sorry, something went wrong while searching for sellers. Please try again later."
                    add_to_history(phone, "bot", error_msg)
                    return error_msg

            # For register/sell/review — set state and ask for confirmation
            state = {
                "intent": intent,
                "fields": combined_fields,
                "awaiting_confirmation": True
            }
            set_user_state(phone, state)

            confirmation = (
                f"You're trying to {intent} with:\n"
                f"{json.dumps(combined_fields, indent=2)}\n"
                "Reply YES to confirm or NO to cancel."
            )
            add_to_history(phone, "bot", confirmation)
            return confirmation

        else:
            missing = [f for f in REQUIRED_FIELDS[intent] if f not in combined_fields]
            next_field = missing[0] if missing else "more info"

            state = {
                "intent": intent,
                "fields": combined_fields,
                "awaiting_confirmation": False
            }
            set_user_state(phone, state)

            follow_up = f"Thanks! Can you tell me your {next_field}?"
            add_to_history(phone, "bot", follow_up)
            return follow_up

    except Exception as e:
        logger.exception(f"LLM error for {phone}")
        error_msg = "😓 Sorry, something went wrong. Try again in a moment."
        add_to_history(phone, "bot", error_msg)
        return error_msg




