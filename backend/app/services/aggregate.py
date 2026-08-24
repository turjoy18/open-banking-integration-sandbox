import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth import TokenPrincipal
from app.db import RequestLog
from app.services.bank import get_customer_accounts
from app.services.fx import hkd_reporting_total, load_fx_rates
from app.services.masking import mask_summary
from app.services.oauth import require_active_consent


def aggregate_customer(customer_id: str, db: Session, principal: TokenPrincipal) -> dict:
    started = time.perf_counter()
    endpoint = f"/aggregate/{customer_id}"

    try:
        require_active_consent(db, principal, customer_id, "accounts.read")
        bank_data = get_customer_accounts(customer_id)
        if bank_data is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        fx_rates, fx_status = load_fx_rates()
        hkd_total, fx_status = hkd_reporting_total(bank_data["accounts"], fx_rates, fx_status)
        latency_ms = int((time.perf_counter() - started) * 1000)

        payload = {
            "customer_id": customer_id,
            "accounts": bank_data["accounts"],
            "fx_rates": fx_rates,
            "meta": {
                "latency_ms": latency_ms,
                "fx_status": fx_status,
                "hkd_total": hkd_total,
                "reporting_currency": "HKD",
            },
        }

        db.add(
            RequestLog(
                endpoint=endpoint,
                customer_id=customer_id,
                status_code=200,
                latency_ms=latency_ms,
                summary=mask_summary(
                    f"accounts={len(bank_data['accounts'])}; fx_status={fx_status}"
                ),
                tpp_id=principal.client_id,
                consent_id=principal.consent_id,
                purpose="account_aggregation",
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
                summary=mask_summary(str(exc.detail)),
                tpp_id=principal.client_id,
                consent_id=principal.consent_id,
                purpose="account_aggregation",
            )
        )
        db.commit()
        raise