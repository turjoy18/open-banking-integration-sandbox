from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI
from app.db import AuthCode, get_db
from app.services.oauth import TokenError, exchange_authorization_code

router = APIRouter(prefix="/tpp", tags=["tpp"])


class ExchangeRequest(BaseModel):
    code: str
    state: str | None = None


@router.post("/oauth/exchange")
def exchange_code(body: ExchangeRequest, db: Session = Depends(get_db)):
    """Confidential-client token exchange so the SPA never sees the TPP secret."""
    auth_code = db.query(AuthCode).filter(AuthCode.code == body.code).one_or_none()
    if auth_code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown authorization code")
    expected_state = auth_code.state or ""
    provided_state = body.state or ""
    if expected_state != provided_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state mismatch")

    try:
        return exchange_authorization_code(
            db,
            grant_type="authorization_code",
            code=body.code,
            redirect_uri=OAUTH_REDIRECT_URI,
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
        )
    except TokenError as exc:
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if exc.error == "invalid_client"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=exc.description)
