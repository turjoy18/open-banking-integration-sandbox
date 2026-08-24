import os

from app.api.mocks_fx import FX_XML, parse_fx_xml


def load_fx_rates() -> tuple[dict[str, float], str]:
    """Return (rates, fx_status) where status is ok, stale, or unavailable."""
    forced = os.getenv("FX_FORCE_STATUS", "").strip().lower()
    if forced == "unavailable":
        return {}, "unavailable"
    rates = parse_fx_xml(FX_XML)
    if forced == "stale":
        return rates, "stale"
    return rates, "ok"


def hkd_reporting_total(accounts: list[dict], rates: dict[str, float], fx_status: str) -> tuple[float, str]:
    total = 0.0
    missing_pair = False
    for account in accounts:
        currency = str(account.get("currency") or "HKD").upper()
        balance = float(account.get("balance") or 0)
        if currency == "HKD":
            total += balance
            continue
        pair = f"{currency}HKD"
        if fx_status == "unavailable" or pair not in rates:
            missing_pair = True
            continue
        total += balance * rates[pair]
    status = fx_status
    if fx_status == "unavailable" or missing_pair:
        status = "unavailable" if fx_status == "unavailable" or missing_pair else status
        if missing_pair and fx_status != "unavailable":
            status = "unavailable"
    return round(total, 2), status
