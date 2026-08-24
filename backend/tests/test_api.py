from app.api.mocks_fx import FX_XML, parse_fx_xml
from app.config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI
from urllib.parse import parse_qs, urlparse


def oauth_headers(client, customer_id="C001", scopes=None):
    scopes = scopes or ["accounts.read", "transactions.read", "payments.initiate"]
    authorize = client.post(
        "/oauth/authorize",
        data={
            "username": "demo",
            "password": "demo",
            "customer_id": customer_id,
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "response_type": "code",
            "state": "test-state",
            "scope": scopes,
        },
        follow_redirects=False,
    )
    assert authorize.status_code == 302, authorize.text
    code = parse_qs(urlparse(authorize.headers["location"]).query)["code"][0]
    exchanged = client.post(
        "/tpp/oauth/exchange",
        json={"code": code, "state": "test-state"},
    )
    assert exchanged.status_code == 200, exchanged.text
    token = exchanged.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def auth_headers(client):
    return oauth_headers(client)

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
    response = client.get("/aggregate/C002", headers=oauth_headers(client, customer_id="C001"))
    assert response.status_code == 403


def test_audit_logs_empty(client):
    response = client.get("/audit-logs")
    assert response.status_code == 200
    assert response.json() == []


def test_audit_logs_after_aggregate(client):
    headers = oauth_headers(client, customer_id="C001")
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C002", headers=headers)

    response = client.get("/audit-logs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    newest = body[0]
    assert newest["customer_id"] == "C002"
    assert newest["status_code"] == 403
    assert newest["endpoint"] == "/aggregate/C002"
    assert "latency_ms" in newest
    assert "created_at" in newest

    older = body[1]
    assert older["customer_id"] == "C001"
    assert older["status_code"] == 200


def test_audit_logs_limit(client):
    headers = oauth_headers(client, customer_id="C001")
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C001", headers=headers)
    client.get("/aggregate/C002", headers=headers)

    response = client.get("/audit-logs?limit=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["status_code"] == 403
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


def _authorize_code(client, customer_id="C001", scopes=None, state="test-state"):
    scopes = scopes or ["accounts.read", "transactions.read"]
    authorize = client.post(
        "/oauth/authorize",
        data={
            "username": "demo",
            "password": "demo",
            "customer_id": customer_id,
            "client_id": OAUTH_CLIENT_ID,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "response_type": "code",
            "state": state,
            "scope": scopes,
        },
        follow_redirects=False,
    )
    assert authorize.status_code == 302, authorize.text
    return parse_qs(urlparse(authorize.headers["location"]).query)["code"][0]


def test_oauth_token_rejects_bad_secret(client):
    code = _authorize_code(client)
    response = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": "wrong-secret",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_client"


def test_oauth_token_rejects_reused_code(client):
    code = _authorize_code(client)
    first = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
        },
    )
    assert first.status_code == 200
    second = client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "client_id": OAUTH_CLIENT_ID,
            "client_secret": OAUTH_CLIENT_SECRET,
        },
    )
    assert second.status_code == 400
    assert second.json()["error"] == "invalid_grant"


def test_tpp_exchange_rejects_state_mismatch(client):
    code = _authorize_code(client, state="expected")
    response = client.post(
        "/tpp/oauth/exchange",
        json={"code": code, "state": "other"},
    )
    assert response.status_code == 400


def test_aggregate_login_token_requires_consent(client):
    login = client.post("/auth/login", json={"username": "demo", "password": "demo"})
    token = login.json()["access_token"]
    response = client.get("/aggregate/C001", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_aggregate_missing_accounts_read_scope(client):
    headers = oauth_headers(client, scopes=["payments.initiate"])
    response = client.get("/aggregate/C001", headers=headers)
    assert response.status_code == 403
    assert "accounts.read" in response.json()["detail"]


def test_revoke_consent_then_aggregate_forbidden(client):
    headers = oauth_headers(client)
    listed = client.get("/consents", headers=headers)
    assert listed.status_code == 200
    consents = listed.json()
    assert consents
    active = next(row for row in consents if row["status"] == "active")
    revoked = client.delete(f"/consents/{active['id']}", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    response = client.get("/aggregate/C001", headers=headers)
    assert response.status_code == 403
    assert "revoked" in response.json()["detail"].lower()


def test_oauth_revoke_by_token(client):
    headers = oauth_headers(client)
    token = headers["Authorization"].split(" ", 1)[1]
    revoked = client.post("/oauth/revoke", json={"token": token})
    assert revoked.status_code == 200
    response = client.get("/aggregate/C001", headers=headers)
    assert response.status_code == 403


def test_phase1_products_public(client):
    response = client.get("/open-api/v1/products")
    assert response.status_code == 200
    body = response.json()
    assert body["phase"] == 1
    ids = {item["product_id"] for item in body["products"]}
    assert "HKD-SAVINGS" in ids
    assert "USD-CURRENT" in ids


def test_phase2_application_accepted(client):
    created = client.post(
        "/open-api/v1/applications",
        json={"product_id": "HKD-SAVINGS", "customer_id": "C001"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "accepted"
    fetched = client.get(f"/open-api/v1/applications/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["product_id"] == "HKD-SAVINGS"


def test_phase2_unknown_product(client):
    response = client.post("/open-api/v1/applications", json={"product_id": "NOPE"})
    assert response.status_code == 400


def test_phase3_accounts_require_token(client):
    response = client.get("/open-api/v1/accounts/C001")
    assert response.status_code == 401


def test_phase3_accounts_and_transactions(client):
    headers = oauth_headers(client, customer_id="C001")
    accounts = client.get("/open-api/v1/accounts/C001", headers=headers)
    assert accounts.status_code == 200
    body = accounts.json()
    assert body["phase"] == 3
    assert body["customer_id"] == "C001"
    txns = client.get("/open-api/v1/accounts/C001/transactions", headers=headers)
    assert txns.status_code == 200
    assert "transactions" in txns.json()


def test_phase4_payment_status_machine(client):
    headers = oauth_headers(client, customer_id="C001")
    created = client.post(
        "/open-api/v1/payments",
        headers=headers,
        json={
            "debtor_account_id": "HK-001-SAV",
            "creditor_name": "Demo Payee",
            "amount": 25,
            "currency": "HKD",
        },
    )
    assert created.status_code == 201
    payment_id = created.json()["id"]
    assert created.json()["status"] == "received"
    first = client.get(f"/open-api/v1/payments/{payment_id}", headers=headers)
    assert first.json()["status"] == "pending"
    second = client.get(f"/open-api/v1/payments/{payment_id}", headers=headers)
    assert second.json()["status"] == "completed"
    third = client.get(f"/open-api/v1/payments/{payment_id}", headers=headers)
    assert third.json()["status"] == "completed"


def test_phase4_rejects_foreign_account(client):
    headers = oauth_headers(client, customer_id="C001")
    response = client.post(
        "/open-api/v1/payments",
        headers=headers,
        json={
            "debtor_account_id": "HK-002-SAV",
            "creditor_name": "Demo Payee",
            "amount": 10,
            "currency": "HKD",
        },
    )
    assert response.status_code == 400
