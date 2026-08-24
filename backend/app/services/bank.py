from app.api.mocks_bank import MOCK_ACCOUNTS


def get_customer_accounts(customer_id: str) -> dict | None:
    """ASPSP account information used by Open API and the TPP aggregator."""
    data = MOCK_ACCOUNTS.get(customer_id)
    if data is None:
        return None
    return {"customer_id": data["customer_id"], "accounts": data["accounts"]}


def get_customer_transactions(customer_id: str) -> dict | None:
    data = MOCK_ACCOUNTS.get(customer_id)
    if data is None:
        return None
    transactions = []
    for account in data["accounts"]:
        for item in account.get("transactions", []):
            transactions.append({**item, "account_id": account["account_id"]})
    return {"customer_id": customer_id, "transactions": transactions}
