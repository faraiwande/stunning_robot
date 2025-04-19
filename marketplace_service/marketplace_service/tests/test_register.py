def test_register_seller(client):
    payload = {
        "phone": "263777000111",
        "business_name": "Test Market",
        "location": "Harare",
        "payment_method": "EcoCash"
    }
    res = client.post("/register", json=payload)
    assert res.status_code == 201
    assert res.json["message"] == "Seller registered successfully"


def test_register_duplicate_phone(client):
    payload = {
        "phone": "263777000666",
        "business_name": "Test One",
        "location": "Mutoko",
        "payment_method": "EcoCash"
    }
    client.post("/register", json=payload)  # First registration
    res = client.post("/register", json=payload)  # Duplicate attempt
    assert res.status_code == 400
    assert "seller already exists" in res.json["error"].lower()
