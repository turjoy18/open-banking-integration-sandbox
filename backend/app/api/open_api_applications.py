from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import ProductApplication, get_db
from app.services.products import PRODUCTS

router = APIRouter(prefix="/open-api/v1", tags=["open-api-phase2"])

_KNOWN_PRODUCTS = {item["product_id"] for item in PRODUCTS}


class ApplicationRequest(BaseModel):
    product_id: str
    customer_id: str | None = None


def _body(row: ProductApplication) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "customer_id": row.customer_id,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "phase": 2,
    }


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application(body: ApplicationRequest, db: Session = Depends(get_db)):
    if body.product_id not in _KNOWN_PRODUCTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown product_id")
    row = ProductApplication(
        product_id=body.product_id,
        customer_id=body.customer_id,
        status="accepted",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _body(row)


@router.get("/applications")
def list_applications(db: Session = Depends(get_db)):
    rows = db.query(ProductApplication).order_by(ProductApplication.id.desc()).all()
    return [_body(row) for row in rows]


@router.get("/applications/{application_id}")
def get_application(application_id: int, db: Session = Depends(get_db)):
    row = db.query(ProductApplication).filter(ProductApplication.id == application_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return _body(row)
