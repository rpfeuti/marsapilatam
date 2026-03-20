"""
Example: structure and price a CLP/USD FX vanilla option.

Run from the project root:
    python examples/fx_options_example.py
"""

from __future__ import annotations

from datetime import date, timedelta

from bloomberg.exceptions import MarsApiError
from instruments.fx_option import FxOption
from services.security_service import SecurityService

VALUATION_DATE = "2024-04-18+00:00"
GREEKS_FIELDS = [
    "Delta",
    "Gamma",
    "ImplVol",
    "MktPx",
    "MktVal",
    "Premium",
    "Rho",
    "Theta",
    "UndFwdPx",
    "Vanna",
    "Vega",
    "Volga",
]

today = date(2024, 4, 18)


def main() -> None:
    svc = SecurityService()

    option = FxOption(
        deal_type="FX.VA",
        call_put="Call",
        call_put_currency="USD",
        direction="Buy",
        exercise_type="European",
        underlying_ticker="CLPUSD",
        strike=1_000.0,
        notional=5_000_000.0,
        notional_currency="USD",
        expiry_date=today + timedelta(days=180),
        settlement_date=today + timedelta(days=182),
        settlement_type="Cash",
        settlement_currency="CLP",
    )

    # Structure
    print("Structuring CLP/USD call option …")
    deal_handle = svc.structure_instrument(option)
    print(f"  Deal handle: {deal_handle}")

    # Price
    print("Pricing (greeks) …")
    df = svc.price({
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate": VALUATION_DATE,
                "requestedField": GREEKS_FIELDS,
            },
            "security": [{"identifier": {"dealHandle": deal_handle}}],
        }
    })
    print(df.T.to_string(header=False))


if __name__ == "__main__":
    try:
        main()
    except MarsApiError as e:
        print(f"Error: {e}")
