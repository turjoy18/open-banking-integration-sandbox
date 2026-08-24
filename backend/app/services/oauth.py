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


class TokenError(Exception):
    def __init__(self, error: str, description: str):
        self.error = error
        self.description = description
        super().__init__(description)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def exchange_authorization_code(
    db: Session,
    *,
    grant_type: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict:
    if grant_type != "authorization_code":
        raise TokenError("unsupported_grant_type", "grant_type must be authorization_code")

    client = get_oauth_client(db, client_id)
    if client is None or client.client_secret != client_secret:
        raise TokenError("invalid_client", "Invalid client credentials")

    auth_code = db.query(AuthCode).filter(AuthCode.code == code).one_or_none()
    now = datetime.now(timezone.utc)
    if auth_code is None:
        raise TokenError("invalid_grant", "Unknown authorization code")
    if auth_code.used_at is not None:
        raise TokenError("invalid_grant", "Authorization code already used")
    if _aware(auth_code.expires_at) is not None and now >= _aware(auth_code.expires_at):
        raise TokenError("invalid_grant", "Authorization code expired")
    if auth_code.client_id != client_id:
        raise TokenError("invalid_grant", "Authorization code was not issued to this client")
    if auth_code.redirect_uri != redirect_uri:
        raise TokenError("invalid_grant", "redirect_uri does not match")

    consent = db.query(Consent).filter(Consent.id == auth_code.consent_id).one_or_none()
    if consent is None or consent.status != "active":
        raise TokenError("invalid_grant", "Consent is not active")
    if _aware(consent.expires_at) is not None and now >= _aware(consent.expires_at):
        consent.status = "expired"
        db.commit()
        raise TokenError("invalid_grant", "Consent has expired")

    auth_code.used_at = now
    db.commit()

    from app.auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

    token = create_access_token(
        auth_code.customer_id,
        extra_claims={
            "client_id": auth_code.client_id,
            "consent_id": consent.id,
            "scope": auth_code.scopes,
        },
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": auth_code.scopes,
        "consent_id": consent.id,
        "customer_id": auth_code.customer_id,
    }
