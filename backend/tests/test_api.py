from app.api.mocks_fx import FX_XML, parse_fx_xml


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mock_bank_known_customer(client):
    response = client.get("/mocks/bank/accounts/C001")
    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "C001"
    assert len(body["accounts"]) >= 1


def test_mock_bank_unknown_customer(client):
    response = client.get("/mocks/bank/accounts/C999")
    assert response.status_code == 404


def test_mock_fx_returns_xml(client):
    response = client.get("/mocks/fx/rates")
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "USDHKD" in response.text


def test_parse_fx_xml():
    rates = parse_fx_xml(FX_XML)
    assert rates["USDHKD"] == 7.85
    assert "EURHKD" in rates


def test_aggregate_success(client):
    response = client.get("/aggregate/C001")
    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "C001"
    assert "accounts" in body
    assert "fx_rates" in body
    assert "latency_ms" in body["meta"]


def test_aggregate_unknown_customer(client):
    response = client.get("/aggregate/C999")
    assert response.status_code == 404