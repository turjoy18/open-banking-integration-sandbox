from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.orm import Session

from app.db import AuthCode, Consent, OAuthClient, seed_oauth_client

KNOWN_SCOPES = frozenset({"accounts.read", "transactions.read", "payments.initiate"})
AUTH_CODE_TTL = timedelta(minutes=10)
CONSENT_TTL = timedelta(days=7)


def get_oauth_client(db: Session, client_id: str) -> OAuthClient | None:
    seed_oauth_client(db)
    return db.query(OAuthClient).filter(OAuthClient.client_id == client_id).one_or_none()


def parse_scopes(raw: str | None) -> list[str]:
    if not raw:
        return []
    seen: list[str] = []
    for part in raw.replace(",", " ").split():
        if part in KNOWN_SCOPES and part not in seen:
            seen.append(part)
    return seen


def validate_authorize_request(
    db: Session,
    *,
    response_type: str | None,
    client_id: str | None,
    redirect_uri: str | None,
    scope: str | None,
) -> tuple[OAuthClient | None, list[str], str | None]:
    if response_type != "code":
        return None, [], "response_type must be code"
    if not client_id:
        return None, [], "client_id is required"
    client = get_oauth_client(db, client_id)
    if client is None:
        return None, [], "Unknown client_id"
    if not redirect_uri or redirect_uri != client.redirect_uri:
        return None, [], "redirect_uri does not match the registered client"
    scopes = parse_scopes(scope)
    if not scopes:
        return None, [], "At least one known scope is required"
    return client, scopes, None


def issue_authorization_code(
    db: Session,
    *,
    client: OAuthClient,
    customer_id: str,
    scopes: list[str],
    redirect_uri: str,
    state: str | None,
) -> AuthCode:
    now = datetime.now(timezone.utc)
    consent = Consent(
        customer_id=customer_id,
        client_id=client.client_id,
        scopes=" ".join(scopes),
        status="active",
        created_at=now,
        expires_at=now + CONSENT_TTL,
    )
    db.add(consent)
    db.flush()

    auth_code = AuthCode(
        code=secrets.token_urlsafe(32),
        client_id=client.client_id,
        customer_id=customer_id,
        redirect_uri=redirect_uri,
        scopes=" ".join(scopes),
        state=state,
        consent_id=consent.id,
        expires_at=now + AUTH_CODE_TTL,
    )
    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)
    return auth_code
