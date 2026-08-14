from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.services.aggregate import aggregate_customer

router = APIRouter(tags=["aggregate"])


@router.get("/aggregate/{customer_id}")
def get_aggregate(
    customer_id: str,
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
):
    return aggregate_customer(customer_id, db)