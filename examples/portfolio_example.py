"""
Example: price a Bloomberg portfolio and calculate Key Rate Risk.

Run from the project root:
    python examples/portfolio_example.py
"""

from __future__ import annotations

from datetime import date

from bloomberg.exceptions import MarsApiError
from services.portfolio_service import PortfolioService
from services.risk_service import RiskService

VALUATION_DATE = "2024-04-18+00:00"
PORTFOLIO_NAME = "MARS_API"
PORTFOLIO_SOURCE = "PRTU"

PRICING_FIELDS = [
    "MktPx",
    "MktVal",
    "Notional",
    "NPV",
    "DV01",
    "AccrInt",
]


def main() -> None:
    # ------------------------------------------------------------------
    # Portfolio pricing
    # ------------------------------------------------------------------
    port_svc = PortfolioService()

    print(f"Pricing portfolio {PORTFOLIO_NAME!r} …")
    df = port_svc.price({
        "portfolioPricingRequest": {
            "pricingParameter": {
                "valuationDate": VALUATION_DATE,
                "requestedField": PRICING_FIELDS,
            },
            "portfolio": {
                "portfolioName": PORTFOLIO_NAME,
                "portfolioSource": PORTFOLIO_SOURCE,
            },
        }
    })

    print(df.to_string(index=False))
    print(f"\nTotal securities priced: {len(df)}")

    # ------------------------------------------------------------------
    # Key Rate Risk on first security
    # ------------------------------------------------------------------
    if df.empty:
        print("No securities to compute KRR for.")
        return

    deal_id = df["BloombergDealID"].iloc[0]
    print(f"\nCalculating KRR for {deal_id!r} …")

    risk_svc = RiskService()
    krr_df = risk_svc.key_rate_risk(
        valuation_date=date(2024, 4, 18),
        identifiers=[{"bloombergDealId": deal_id}],
        requested_fields=["NPV", "DV01"],
    )
    print(krr_df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except MarsApiError as e:
        print(f"Error: {e}")
