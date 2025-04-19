def test_listing_requires_payment(client):
    client.post("/register", json={
        "phone": "263777000222",
        "business_name": "Unpaid Seller",
        "location": "Gweru",
        "payment_method": "EcoCash"
    })

    res = client.post("/listings", json={
        "phone": "263777000222",
        "product_name": "Tomatoes",
        "quantity": "10kg",
        "price": 5.00,
        "location": "Gweru",
        "description": "Fresh red tomatoes",
        "category": "vegetables"
    })
    assert res.status_code == 403
    assert "Payment required" in res.json["error"]

def test_listing_after_payment(client, paid_seller):
    res = client.post("/listings", json={
        "phone": paid_seller["phone"],
        "product_name": "Maize",
        "quantity": "20kg",
        "price": 8.00,
        "location": "Masvingo",
        "description": "Dried yellow maize",
        "category": "grains"
    })
    assert res.status_code == 201
    assert "Listing created successfully" in res.json["message"]

