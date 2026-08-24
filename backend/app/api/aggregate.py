from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import TokenPrincipal, get_current_principal
from app.db import get_db
from app.services.aggregate import aggregate_customer

router = APIRouter(tags=["aggregate"])


@router.get("/aggregate/{customer_id}")
def get_aggregate(
    customer_id: str,
    db: Session = Depends(get_db),
    principal: TokenPrincipal = Depends(get_current_principal),
):
    return aggregate_customer(customer_id, db, principal)