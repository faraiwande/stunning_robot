def test_confirm_payment(client, test_seller):
    payload = {
        "phone": test_seller["phone"],
        "amount": 5.00,
        "method": "EcoCash",
        "reference": "PAY000123"
    }

    res = client.post("/pay", json=payload)
    assert res.status_code == 202
    assert "processing started" in res.json["message"].lower()


def test_invalid_payment(client, test_seller):
    payload = {
        "phone": test_seller["phone"],
        "amount": None,
        "method": "EcoCash",
        "reference": ""
    }

    res = client.post("/pay", json=payload)
    assert res.status_code == 400
    assert "phone, amount, and reference are required" in res.json["error"].lower()
