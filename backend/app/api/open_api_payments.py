from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import TokenPrincipal, get_current_principal
from app.db import Payment, get_db
from app.services.bank import get_customer_accounts
from app.services.oauth import require_active_consent

router = APIRouter(prefix="/open-api/v1", tags=["open-api-phase4"])

_NEXT_STATUS = {
    "received": "pending",
    "pending": "completed",
    "completed": "completed",
    "failed": "failed",
}


class PaymentRequest(BaseModel):
    debtor_account_id: str
    creditor_name: str
    amount: float = Field(gt=0)
    currency: str = "HKD"


def _body(row: Payment) -> dict:
    return {
        "id": row.id,
        "phase": 4,
        "customer_id": row.customer_id,
        "debtor_account_id": row.debtor_account_id,
        "creditor_name": row.creditor_name,
        "amount": row.amount,
        "currency": row.currency,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _account_ids(customer_id: str) -> set[str]:
    data = get_customer_accounts(customer_id)
    if data is None:
        return set()
    return {account["account_id"] for account in data["accounts"]}


@router.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(
    body: PaymentRequest,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    require_active_consent(db, principal, principal.subject, "payments.initiate")
    if body.debtor_account_id not in _account_ids(principal.subject):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debtor account is not held by this customer",
        )
    now = datetime.now(timezone.utc)
    row = Payment(
        customer_id=principal.subject,
        debtor_account_id=body.debtor_account_id,
        creditor_name=body.creditor_name,
        amount=f"{body.amount:.2f}",
        currency=body.currency.upper(),
        status="received",
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _body(row)


@router.get("/payments/{payment_id}")
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    require_active_consent(db, principal, principal.subject, "payments.initiate")
    row = db.query(Payment).filter(Payment.id == payment_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if row.customer_id != principal.subject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment belongs to another customer")
    nxt = _NEXT_STATUS.get(row.status, row.status)
    if nxt != row.status:
        row.status = nxt
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
    return _body(row)


@router.get("/payments")
def list_payments(
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    require_active_consent(db, principal, principal.subject, "payments.initiate")
    rows = (
        db.query(Payment)
        .filter(Payment.customer_id == principal.subject)
        .order_by(Payment.id.desc())
        .all()
    )
    return [_body(row) for row in rows]
