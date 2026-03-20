"""
Example: structure, price, and solve a COP OIS swap.

Workflow:
1. Build a Swap model
2. Structure the deal (creates a temporary deal in Bloomberg)
3. Price it (NPV, DV01, etc.)
4. Solve for the par fixed rate (NPV = 0)
5. Optionally save the deal permanently

Run from the project root:
    python examples/swaps_example.py
"""

from __future__ import annotations

from datetime import date

from bloomberg.exceptions import MarsApiError
from instruments.swap import Swap
from services.security_service import SecurityService

VALUATION_DATE = "2024-04-18+00:00"
PRICING_FIELDS = ["MktPx", "MktVal", "NPV", "DV01", "Notional"]


def main() -> None:
    svc = SecurityService()

    # 1. Define the swap
    swap = Swap(
        deal_type="IR.OIS",
        effective_date=date(2024, 4, 22),
        maturity_date=date(2025, 4, 22),
        settlement_currency="COP",
        leg1_direction="Pay",
        leg1_notional=10_000_000_000.0,
        leg1_currency="COP",
        leg1_fixed_rate=11.5,
        leg1_pay_frequency="Annual",
        leg1_day_count="Actual/365 Fixed",
        leg2_direction="Receive",
        leg2_notional=10_000_000_000.0,
        leg2_currency="COP",
        leg2_floating_index="COOVIBR",
        leg2_pay_frequency="Annual",
        leg2_day_count="Actual/365 Fixed",
    )

    # 2. Structure
    print("Structuring COP OIS swap …")
    deal_handle = svc.structure_instrument(swap)
    print(f"  Deal handle: {deal_handle}")

    # 3. Price
    print("Pricing …")
    df = svc.price({
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate": VALUATION_DATE,
                "requestedField": PRICING_FIELDS,
            },
            "security": [{"identifier": {"dealHandle": deal_handle}}],
        }
    })
    print(df.to_string(index=False))

    # 4. Solve for par rate (NPV = 0)
    print("\nSolving for par fixed rate …")
    solve_result = svc.solve({
        "solveRequest": {
            "pricingParameter": {
                "valuationDate": VALUATION_DATE,
                "requestedField": ["NPV"],
            },
            "security": {
                "identifier": {"dealHandle": deal_handle},
                "solveParameter": {
                    "legNumber": 1,
                    "solvableTarget": "FixedRate",
                    "targetValue": {"name": "NPV", "value": {"doubleVal": 0}},
                },
            },
        }
    })
    par_rate = solve_result.get("solvedValue", {})
    print(f"  Par fixed rate: {par_rate}")


if __name__ == "__main__":
    try:
        main()
    except MarsApiError as e:
        print(f"Error: {e}")
