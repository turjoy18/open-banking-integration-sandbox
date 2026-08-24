from fastapi import APIRouter

from app.services.products import PRODUCTS

router = APIRouter(prefix="/open-api/v1", tags=["open-api-phase1"])


@router.get("/products")
def list_products():
    return {"phase": 1, "products": PRODUCTS}
