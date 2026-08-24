from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import TokenPrincipal, get_current_principal
from app.db import get_db
from app.services.bank import get_customer_accounts, get_customer_transactions
from app.services.oauth import require_active_consent

router = APIRouter(prefix="/open-api/v1", tags=["open-api-phase3"])


@router.get("/accounts/{customer_id}")
def open_api_accounts(
    customer_id: str,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    require_active_consent(db, principal, customer_id, "accounts.read")
    data = get_customer_accounts(customer_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return {"phase": 3, **data}


@router.get("/accounts/{customer_id}/transactions")
def open_api_transactions(
    customer_id: str,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    require_active_consent(db, principal, customer_id, "transactions.read")
    data = get_customer_transactions(customer_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return {"phase": 3, **data}
