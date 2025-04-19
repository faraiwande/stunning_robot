import pytest
from datetime import datetime, timezone
from marketplace_service.app import create_app
from marketplace_service.models.mp_models import db as _db, Seller

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })

    ctx = app.app_context()
    ctx.push()
    _db.create_all()
    yield app

    _db.session.remove()
    _db.drop_all()
    ctx.pop()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_seller():
    return {
        "phone": "263777000777",
        "business_name": "Test Store",
        "location": "Harare",
        "payment_method": "EcoCash"
    }

@pytest.fixture(autouse=True)
def setup_test_seller(client, test_seller):
    """Automatically register the seller before each test"""
    res = client.post("/register", json=test_seller)
    assert res.status_code in (201, 400)  # already exists or success
    return res

@pytest.fixture
def paid_seller(client, app):
    phone = "263777000555"
    seller_payload = {
        "phone": phone,
        "business_name": "Paid Seller",
        "location": "Masvingo",
        "payment_method": "EcoCash"
    }
    client.post("/register", json=seller_payload)

    # Mark as paid directly in DB
    with app.app_context():
        seller =  _db.session.get(Seller, phone)
        seller.is_paid = True
        seller.last_payment_date = datetime.now(timezone.utc)
        _db.session.commit()

    return seller_payload


