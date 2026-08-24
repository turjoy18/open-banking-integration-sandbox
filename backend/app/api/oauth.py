from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import authenticate_user
from app.db import get_db
from app.services.oauth import (
    TokenError,
    exchange_authorization_code,
    issue_authorization_code,
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
