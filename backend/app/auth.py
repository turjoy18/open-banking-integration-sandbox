import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

import app.config  # noqa: F401 — load .env before reading JWT_SECRET_KEY

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Demo-only credentials (PoC — not production)
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo"

security = HTTPBearer(auto_error=False)


@dataclass
class TokenPrincipal:
    subject: str
    client_id: str | None
    consent_id: int | None
    scopes: list[str]


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> bool:
    return username == DEMO_USERNAME and password == DEMO_PASSWORD


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        consent_raw = payload.get("consent_id")
        consent_id = int(consent_raw) if consent_raw is not None else None
        scope_raw = payload.get("scope") or ""
        scopes = [part for part in str(scope_raw).split() if part]
        return TokenPrincipal(
            subject=username,
            client_id=payload.get("client_id"),
            consent_id=consent_id,
            scopes=scopes,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    principal: TokenPrincipal = Depends(get_current_principal),
) -> str:
    return principal.subject