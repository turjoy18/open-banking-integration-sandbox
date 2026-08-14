from app.api.mocks_fx import FX_XML, parse_fx_xml


def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"username": "demo", "password": "demo"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

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
    response = client.get("/aggregate/C001", headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "C001"
    assert "accounts" in body
    assert "fx_rates" in body
    assert "latency_ms" in body["meta"]


def test_aggregate_unknown_customer(client):
    response = client.get("/aggregate/C999", headers=auth_headers(client))
    assert response.status_code == 404


def test_audit_logs_empty(client):
    response = client.get("/audit-logs")
    assert response.status_code == 200
    assert response.json() == []


def test_audit_logs_after_aggregate(client):
    headers = auth_headers(client)
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C999", headers=headers)

    response = client.get("/audit-logs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    newest = body[0]
    assert newest["customer_id"] == "C999"
    assert newest["status_code"] == 404
    assert newest["endpoint"] == "/aggregate/C999"
    assert "latency_ms" in newest
    assert "created_at" in newest

    older = body[1]
    assert older["customer_id"] == "C001"
    assert older["status_code"] == 200


def test_audit_logs_limit(client):
    headers = auth_headers(client)
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C999", headers=headers)

    response = client.get("/audit-logs?limit=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["status_code"] == 404
    assert body[1]["status_code"] == 200


def test_audit_logs_invalid_limit(client):
    response = client.get("/audit-logs?limit=0")
    assert response.status_code == 422


def test_login_success(client):
    response = client.post(
        "/auth/login",
        json={"username": "demo", "password": "demo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0


def test_login_failure(client):
    response = client.post(
        "/auth/login",
        json={"username": "demo", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_aggregate_missing_token(client):
    response = client.get("/aggregate/C001")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_aggregate_invalid_token(client):
    response = client.get(
        "/aggregate/C001",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_aggregate_wrong_auth_scheme(client):
    response = client.get(
        "/aggregate/C001",
        headers={"Authorization": "Token some-value"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
