import pytest
from datetime import datetime, timezone
from marketplace_service.models.mp_models import SellerReview, db

def test_review_submission(client, test_seller):
    payload = {
        "rating": 4,
        "comment": "Very good experience."
    }

    res = client.post(f"/sellers/{test_seller['phone']}/reviews", json=payload)
    assert res.status_code == 201
    assert "review_id" in res.json


def test_review_submission_invalid_rating(client, test_seller):
    payload = {
        "rating": 6,  # invalid
        "comment": "Invalid rating"
    }

    res = client.post(f"/sellers/{test_seller['phone']}/reviews", json=payload)
    assert res.status_code == 400
    assert "rating must be an integer" in res.json["error"].lower()


def test_get_reviews(client, app, test_seller):
    with app.app_context():
        db.session.add(SellerReview(
            id="test-review-id",
            seller_phone=test_seller["phone"],
            rating=5,
            comment="Excellent!",
            created_at=datetime.now(timezone.utc)
        ))
        db.session.commit()

    res = client.get(f"/sellers/{test_seller['phone']}/reviews")
    assert res.status_code == 200
    assert res.json["total_reviews"] >= 1
    assert res.json["average_rating"] >= 1
