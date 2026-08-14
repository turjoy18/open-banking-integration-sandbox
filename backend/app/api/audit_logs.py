from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import RequestLog, get_db

router = APIRouter(tags=["audit-logs"])


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(RequestLog)
        .order_by(RequestLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "endpoint": row.endpoint,
            "customer_id": row.customer_id,
            "status_code": row.status_code,
            "latency_ms": row.latency_ms,
            "summary": row.summary,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]