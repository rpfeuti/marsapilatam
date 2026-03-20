"""
Example: price a single security by Bloomberg Deal ID.

Run from the project root:
    python examples/pricing_example.py
"""

from __future__ import annotations

from bloomberg.exceptions import MarsApiError
from services.security_service import SecurityService

VALUATION_DATE = "2024-04-18+00:00"
SECURITY_ID = "IBM 2.85 05/15/2040 Corp"
FIELDS = ["MktPx", "MktVal", "Notional", "YAS_YLD", "DV01"]


def main() -> None:
    svc = SecurityService()

    print(f"Pricing {SECURITY_ID} …")
    df = svc.price({
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate": VALUATION_DATE,
                "requestedField": FIELDS,
            },
            "security": [
                {"identifier": {"bloombergDealId": SECURITY_ID}}
            ],
        }
    })

    print(df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except MarsApiError as e:
        print(f"Error: {e}")
