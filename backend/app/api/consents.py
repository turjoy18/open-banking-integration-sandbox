from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import TokenPrincipal, get_current_principal
from app.db import get_db
from app.services.oauth import get_consent, list_consents_for_customer, revoke_consent

router = APIRouter(tags=["consents"])


def serialize_consent(consent) -> dict:
    return {
        "id": consent.id,
        "customer_id": consent.customer_id,
        "client_id": consent.client_id,
        "scopes": consent.scopes,
        "status": consent.status,
        "created_at": consent.created_at.isoformat() if consent.created_at else None,
        "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
        "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
    }


@router.get("/consents")
def list_consents(
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    rows = list_consents_for_customer(db, principal.subject)
    return [serialize_consent(row) for row in rows]


@router.delete("/consents/{consent_id}")
def delete_consent(
    consent_id: int,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    consent = get_consent(db, consent_id)
    if consent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")
    if consent.customer_id != principal.subject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot revoke another customer's consent")
    return serialize_consent(revoke_consent(db, consent))
