import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.mocks_bank import MOCK_ACCOUNTS
from app.api.mocks_fx import FX_XML, parse_fx_xml
from app.db import RequestLog


def aggregate_customer(customer_id: str, db: Session) -> dict:
    started = time.perf_counter()
    endpoint = f"/aggregate/{customer_id}"

    try:
        bank_data = MOCK_ACCOUNTS.get(customer_id)
        if bank_data is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        fx_rates = parse_fx_xml(FX_XML)
        latency_ms = int((time.perf_counter() - started) * 1000)

        payload = {
            "customer_id": customer_id,
            "accounts": bank_data["accounts"],
            "fx_rates": fx_rates,
            "meta": {"latency_ms": latency_ms},
        }

        db.add(
            RequestLog(
                endpoint=endpoint,
                customer_id=customer_id,
                status_code=200,
                latency_ms=latency_ms,
                summary=f"accounts={len(bank_data['accounts'])}; fx_pairs={len(fx_rates)}",
            )
        )
        db.commit()
        return payload

    except HTTPException as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        db.add(
            RequestLog(
                endpoint=endpoint,
                customer_id=customer_id,
                status_code=exc.status_code,
                latency_ms=latency_ms,
                summary=str(exc.detail),
            )
        )
        db.commit()
        raise