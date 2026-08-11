from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mocks/bank", tags=["mocks-bank"])

MOCK_ACCOUNTS = {
    "C001": {
        "customer_id": "C001",
        "accounts": [
            {
                "account_id": "HK-001-SAV",
                "currency": "HKD",
                "balance": 125000.50,
                "transactions": [
                    {"id": "T1", "amount": -320.00, "currency": "HKD", "description": "Grocery"},
                    {"id": "T2", "amount": 15000.00, "currency": "HKD", "description": "Salary"},
                ],
            },
            {
                "account_id": "HK-001-USD",
                "currency": "USD",
                "balance": 8200.00,
                "transactions": [
                    {"id": "T3", "amount": -50.00, "currency": "USD", "description": "Subscription"},
                ],
            },
        ],
    },
    "C002": {
        "customer_id": "C002",
        "accounts": [
            {
                "account_id": "HK-002-SAV",
                "currency": "HKD",
                "balance": 43000.00,
                "transactions": [],
            }
        ],
    },
}


@router.get("/accounts/{customer_id}")
def get_accounts(customer_id: str):
    data = MOCK_ACCOUNTS.get(customer_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return data