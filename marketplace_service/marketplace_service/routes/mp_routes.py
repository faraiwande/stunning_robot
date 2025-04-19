import logging
from datetime import datetime, timezone
from uuid import uuid4
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify, abort
from marketplace_service.models.mp_models import db, SellerReview, Seller, Listing, Payment

# Configure logging with file rotation
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    'marketplace_service.log', maxBytes=5*1024*1024, backupCount=3
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

routes_bp = Blueprint("routes", __name__)
executor = ThreadPoolExecutor(max_workers=2)

def validate_phone(phone):
    if not phone or not phone.startswith('263') or len(phone) != 12 or not phone.isdigit():
        logger.error(f"Invalid phone number format: {phone}")
        raise ValueError("Invalid phone number format. Must start with 263 and be 12 digits")

def verify_payment(reference, amount):
    logger.info(f"Verifying payment with reference: {reference} for amount: {amount}")
    return True

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        phone = kwargs.get('phone') or request.json.get('phone')
        if not phone:
            logger.warning("Seller authentication required but no phone provided")
            abort(401, description="Seller authentication required")

        logger.info(f"Checking seller with phone: {phone}")
        seller = db.session.get(Seller, phone)
        if not seller:
            logger.warning(f"Seller not found for phone: {phone}")
            abort(404, description="Seller not found")
        return f(*args, **kwargs)
    return decorated_function

@routes_bp.errorhandler(400)
def bad_request(error):
    logger.error(f"Bad request: {str(error)}")
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@routes_bp.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized access: {str(error)}")
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401

@routes_bp.errorhandler(404)
def not_found(error):
    logger.warning(f"Resource not found: {str(error)}")
    return jsonify({"error": "Not found", "message": str(error)}), 404

@routes_bp.errorhandler(500)
def server_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error", "message": "Please try again later"}), 500

@routes_bp.route("/health", methods=["GET"])
def health():
    logger.info("Health check endpoint accessed")
    return jsonify({
        "status": "ok",
        "message": "Marketplace Bot is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@routes_bp.route("/register", methods=["POST"])
def register_seller():
    data = request.get_json()
    logger.info(f"Attempting to register seller with data: {data}")

    try:
        validate_phone(data.get("phone"))
    except ValueError as e:
        logger.error(f"Phone validation failed: {str(e)}")
        return jsonify({"error": str(e)}), 400

    required_fields = ["phone", "business_name", "location", "payment_method"]
    if not all(field in data for field in required_fields):
        logger.error(f"Missing required fields in registration. Required: {required_fields}, Received: {data.keys()}")
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    if db.session.get(Seller, data["phone"]):
        logger.warning(f"Seller already exists with phone: {data['phone']}")
        return jsonify({"error": "Seller already exists"}), 400

    try:
        seller = Seller(
            phone=data["phone"],
            business_name=data["business_name"],
            location=data["location"],
            payment_method=data["payment_method"],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(seller)
        db.session.commit()
        logger.info(f"Successfully registered seller with phone: {data['phone']}")

        return jsonify({
            "message": "Seller registered successfully",
            "seller_phone": seller.phone
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering seller: {str(e)}")
        abort(500)

@routes_bp.route("/listings", methods=["POST"])
@seller_required
def create_listing():
    data = request.get_json()
    logger.info(f"Creating listing for seller: {data['phone']}")

    seller = db.session.get(Seller, data["phone"])

    if not seller.is_paid:
        logger.warning(f"Seller {data['phone']} attempted to create listing without payment")
        return jsonify({
            "error": "Payment required to post listings",
            "payment_url": "/pay"
        }), 403

    try:
        listing = Listing(
            id=str(uuid4()),
            seller_phone=data["phone"],
            product_name=data["product_name"],
            quantity=data["quantity"],
            price=data["price"],
            location=data["location"],
            description=data.get("description", ""),
            category=data["category"],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(listing)
        db.session.commit()
        logger.info(f"Successfully created listing {listing.id} for seller {data['phone']}")

        return jsonify({
            "message": "Listing created successfully",
            "listing_id": listing.id,
            "product": listing.product_name
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating listing: {str(e)}")
        abort(500)

@routes_bp.route("/pay", methods=["POST"])
@seller_required
def confirm_payment():
    data = request.get_json()
    logger.info(f"Payment confirmation request for phone: {data.get('phone')}")

    required_fields = ["phone", "amount", "reference"]
    if not all(data.get(field) for field in required_fields):
        logger.error(f"Missing payment fields. Required: {required_fields}, Received: {data.keys()}")
        return jsonify({"error": "Phone, amount, and reference are required"}), 400

    if not verify_payment(data["reference"], data["amount"]):
        logger.error(f"Payment verification failed for reference: {data['reference']}")
        return jsonify({"error": "Payment verification failed"}), 400

    try:
        executor.submit(process_payment_async, {
            'phone': data["phone"],
            'amount': data["amount"],
            'reference': data["reference"],
            'method': data.get("method", "EcoCash")
        })
        logger.info(f"Started async payment processing for reference: {data['reference']}")

        return jsonify({
            "message": "Payment processing started",
            "reference": data["reference"]
        }), 202
    except Exception as e:
        logger.error(f"Error submitting payment for processing: {str(e)}")
        abort(500)

def process_payment_async(payment_data):
    try:
        with routes_bp.app_context():
            logger.info(f"Processing payment async for phone: {payment_data['phone']}")

            seller = db.session.get(Seller, payment_data["phone"])
            seller.is_paid = True
            seller.last_payment_date = datetime.now(timezone.utc)

            payment = Payment(
                id=str(uuid4()),
                seller_phone=payment_data["phone"],
                amount=payment_data["amount"],
                method=payment_data["method"],
                reference=payment_data["reference"],
                status='confirmed',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(payment)
            db.session.commit()
            logger.info(f"Successfully processed payment {payment.id} for seller {payment_data['phone']}")
    except Exception as e:
        logger.error(f"Error in async payment processing: {str(e)}")

@routes_bp.route("/sellers/<phone>/reviews", methods=["POST"])
def add_seller_review(phone):
    data = request.get_json()
    logger.info(f"Adding review for seller: {phone}")

    if data.get("rating") not in (1, 2, 3, 4, 5):
        logger.error(f"Invalid rating value: {data.get('rating')}")
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

    try:
        review = SellerReview(
            id=str(uuid4()),
            seller_phone=phone,
            rating=data["rating"],
            comment=data.get("comment", ""),
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(review)
        db.session.commit()
        logger.info(f"Successfully added review {review.id} for seller {phone}")

        return jsonify({
            "message": "Review submitted successfully",
            "review_id": review.id
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding review: {str(e)}")
        abort(500)

@routes_bp.route("/sellers/<phone>/reviews", methods=["GET"])
def get_seller_reviews(phone):
    logger.info(f"Fetching reviews for seller: {phone}")

    try:
        reviews = db.session.query(SellerReview).filter_by(seller_phone=phone).all()

        if not reviews:
            logger.info(f"No reviews found for seller: {phone}")
            return jsonify({
                "average_rating": 0,
                "total_reviews": 0,
                "reviews": []
            }), 200

        total_reviews = len(reviews)
        average_rating = round(sum([r.rating for r in reviews]) / total_reviews, 2)
        logger.info(f"Found {total_reviews} reviews for seller {phone} with average rating {average_rating}")

        result = [{
            "id": r.id,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat()
        } for r in reviews]

        return jsonify({
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "reviews": result
        }), 200
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        abort(500)
