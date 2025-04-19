from datetime import datetime
from uuid import uuid4
from flask import Blueprint, request, jsonify
from marketplace_service.models.mp_models import Seller, Listing, Payment, db

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Marketplace Bot is running"}), 200


@routes_bp.route("/register", methods=["POST"])
def register_seller():
    data = request.get_json()
    phone = data.get("phone")
    name = data.get("business_name")
    location = data.get("location")
    payment_method = data.get("payment_method")

    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    seller = Seller.query.get(phone)
    if seller:
        return jsonify({"message": "Seller already registered"}), 200

    new_seller = Seller(
        phone=phone,
        business_name=name,
        location=location,
        payment_method=payment_method,
        created_at=datetime.utcnow()
    )
    db.session.add(new_seller)
    db.session.commit()

    return jsonify({"message": "Seller registered successfully"}), 201


@routes_bp.route("/listings", methods=["POST"])
def create_listing():
    data = request.get_json()
    phone = data.get("phone")
    product_name = data.get("product_name")
    quantity = data.get("quantity")
    price = data.get("price")
    location = data.get("location")
    description = data.get("description")
    category = data.get("category")

    seller = Seller.query.get(phone)
    if not seller:
        return jsonify({"error": "Seller not found"}), 404

    if not seller.is_paid:
        return jsonify({"error": "Payment required to post listings"}), 403

    listing = Listing(
        id=str(uuid4()),
        seller_phone=phone,
        product_name=product_name,
        quantity=quantity,
        price=price,
        location=location,
        description=description,
        category=category,
        created_at=datetime.utcnow()
    )
    db.session.add(listing)
    db.session.commit()

    return jsonify({"message": "Listing created successfully", "listing_id": listing.id}), 201


@routes_bp.route("/pay", methods=["POST"])
def confirm_payment():
    data = request.get_json()
    phone = data.get("phone")
    amount = data.get("amount")
    method = data.get("method", "EcoCash")
    reference = data.get("reference")

    seller = Seller.query.get(phone)
    if not seller:
        return jsonify({"error": "Seller not found"}), 404

    seller.is_paid = True
    seller.last_payment_date = datetime.utcnow()

    payment = Payment(
        id=str(uuid4()),
        seller_phone=phone,
        amount=amount,
        method=method,
        reference=reference,
        status='confirmed',
        created_at=datetime.utcnow()
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({"message": "Payment confirmed and seller upgraded"}), 200


@routes_bp.route("/sellers/<phone>/reviews", methods=["POST"])
def add_seller_review(phone):
    data = request.get_json()
    rating = data.get("rating")
    comment = data.get("comment")

    if rating is None or not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400

    seller = Seller.query.get(phone)
    if not seller:
        return jsonify({"error": "Seller not found"}), 404

    review = SellerReview(
        id=str(uuid4()),
        seller_phone=phone,
        rating=rating,
        comment=comment,
        created_at=datetime.utcnow()
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review submitted successfully"}), 201


@routes_bp.route("/sellers/<phone>/reviews", methods=["GET"])
def get_seller_reviews(phone):
    seller = Seller.query.get(phone)
    if not seller:
        return jsonify({"error": "Seller not found"}), 404

    reviews = SellerReview.query.filter_by(seller_phone=phone).all()
    result = [{
        "rating": r.rating,
        "comment": r.comment,
        "created_at": r.created_at.isoformat()
    } for r in reviews]

    return jsonify({"reviews": result}), 200