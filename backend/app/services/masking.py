import re


def mask_account_id(account_id: str) -> str:
    if not account_id:
        return "****"
    if len(account_id) <= 4:
        return "*" * len(account_id)
    return f"{account_id[:2]}***{account_id[-2:]}"


def mask_amount(value) -> str:
    return "***"


_ACCOUNT_ID_RE = re.compile(r"\b([A-Z]{2}-[A-Z0-9-]+)\b")


def mask_summary(text: str | None) -> str | None:
    """Keep audit useful without raw account numbers or balances."""
    if text is None:
        return None
    masked = _ACCOUNT_ID_RE.sub(lambda match: mask_account_id(match.group(1)), text)
    masked = re.sub(r"\b\d+\.\d{2}\b", "***", masked)
    return masked
