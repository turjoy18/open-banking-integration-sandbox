from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import authenticate_user, principal_from_access_token
from app.db import get_db
from app.services.oauth import (
    TokenError,
    exchange_authorization_code,
    get_consent,
    issue_authorization_code,
    revoke_consent,
    validate_authorize_request,
)

router = APIRouter(prefix="/oauth", tags=["oauth"])

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

CUSTOMERS = ["C001", "C002"]


def _error_page(request: Request, message: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html><html><body>
    <p>{message}</p>
    </body></html>"""
    return HTMLResponse(content=html, status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/authorize", response_class=HTMLResponse)
def authorize_get(
    request: Request,
    db: Session = Depends(get_db),
    response_type: str | None = None,
    client_id: str | None = None,
    redirect_uri: str | None = None,
    scope: str | None = None,
    state: str | None = None,
):
    client, scopes, error = validate_authorize_request(
        db,
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
    )
    if error or client is None:
        return _error_page(request, error or "Invalid authorize request")
    return templates.TemplateResponse(
        request,
        "authorize.html",
        {
            "client_name": client.name,
            "client_id": client.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "requested_scopes": scopes,
            "customers": CUSTOMERS,
            "selected_customer": CUSTOMERS[0],
            "error": None,
        },
    )


@router.post("/authorize", response_class=HTMLResponse)
def authorize_post(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    customer_id: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form("code"),
    state: str | None = Form(None),
    scope: list[str] | None = Form(None),
):
    scope_raw = " ".join(scope or [])
    client, scopes, error = validate_authorize_request(
        db,
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope_raw,
    )
    context = {
        "client_name": client.name if client else client_id,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "requested_scopes": scopes or (scope or []),
        "customers": CUSTOMERS,
        "selected_customer": customer_id,
        "error": None,
    }
    if error or client is None:
        context["error"] = error
        return templates.TemplateResponse(
            request, "authorize.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )
    if not authenticate_user(username, password):
        context["error"] = "Incorrect username or password"
        return templates.TemplateResponse(
            request, "authorize.html", context, status_code=status.HTTP_401_UNAUTHORIZED
        )
    if customer_id not in CUSTOMERS:
        context["error"] = "Unknown customer"
        return templates.TemplateResponse(
            request, "authorize.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    auth_code = issue_authorization_code(
        db,
        client=client,
        customer_id=customer_id,
        scopes=scopes,
        redirect_uri=redirect_uri,
        state=state,
    )
    query = urlencode({"code": auth_code.code, "state": state or ""})
    return RedirectResponse(
        url=f"{redirect_uri}?{query}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/token")
def oauth_token(
    db: Session = Depends(get_db),
    grant_type: str = Form(...),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    try:
        return exchange_authorization_code(
            db,
            grant_type=grant_type,
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
        )
    except TokenError as exc:
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if exc.error == "invalid_client"
            else status.HTTP_400_BAD_REQUEST
        )
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.error, "error_description": exc.description},
        )


class RevokeRequest(BaseModel):
    consent_id: int | None = None
    token: str | None = None


@router.post("/revoke")
def oauth_revoke(body: RevokeRequest, db: Session = Depends(get_db)):
    consent_id = body.consent_id
    if consent_id is None and body.token:
        principal = principal_from_access_token(body.token)
        consent_id = principal.consent_id
    if consent_id is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_request", "error_description": "consent_id or token is required"},
        )
    consent = get_consent(db, consent_id)
    if consent is None:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok"},
        )
    revoked = revoke_consent(db, consent)
    return {"status": "revoked", "consent_id": revoked.id}
