"""
Download demo data for FX derivatives (Vanilla, Risk Reversal, Knock-In,
Knock-Out) across all 6 currency pairs and save as JSON snapshots to
demo_data/fx_derivatives/.

Run from the project root with live Bloomberg credentials in .env:
    python scripts/download_fx_deriv_demo_data.py
"""

from __future__ import annotations

import calendar
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configs.derivatives_config import (
    FX_KI_SPECS,
    FX_KO_SPECS,
    FX_RR_SPECS,
    FX_VANILLA_SPECS,
    FxDerivativeSpec,
)
from configs.settings import settings
from services.fx_derivatives_service import DerivativePricingService, DerivativeQuery
from services.fx_service import FxRateService

VALUATION_DATE = date(2026, 3, 26)
CURVE_DATE     = date(2026, 3, 26)
DEMO_DATA_DIR  = Path(__file__).resolve().parent.parent / "demo_data" / "fx_derivatives"

_ALL_SPECS: dict[str, dict[str, FxDerivativeSpec]] = {
    "FX_VANILLA": FX_VANILLA_SPECS,
    "FX_RR":      FX_RR_SPECS,
    "FX_KI":      FX_KI_SPECS,
    "FX_KO":      FX_KO_SPECS,
}


def _default_expiry(tenor: str = "3M") -> date:
    base = VALUATION_DATE
    months_map = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12}
    months = months_map.get(tenor, 3)
    target_month = base.month + months
    target_year = base.year + (target_month - 1) // 12
    target_month = (target_month - 1) % 12 + 1
    day = min(base.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, day)


def _get_spot(spec: FxDerivativeSpec, fx: FxRateService) -> float:
    if spec.base_currency == "USD":
        return fx.get_rate(spec.quote_currency) or 1.0
    return 1.0 / (fx.get_rate(spec.base_currency) or 1.0)


def download_all() -> None:
    if settings.demo_mode:
        print(
            "ERROR: Bloomberg credentials are not configured. "
            "Set BBG_CLIENT_ID, BBG_CLIENT_SECRET, and BBG_UUID in .env"
        )
        sys.exit(1)

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)

    svc = DerivativePricingService.from_settings()
    fx = FxRateService.from_settings()
    expiry = _default_expiry("3M")
    print(f"Deal session ready. Valuation: {VALUATION_DATE}, Expiry: {expiry}\n")

    for product_type, spec_dict in _ALL_SPECS.items():
        print(f"--- {product_type} ---")
        for key, spec in spec_dict.items():
            spot = _get_spot(spec, fx)
            print(f"  {key} ({spec.label})  spot={spot:.4f}")

            kwargs: dict = dict(
                key=key,
                product_type=product_type,
                direction="Buy",
                call_put="Call",
                notional=spec.notional,
                strike=round(spot, 4),
                expiry_date=expiry,
                valuation_date=VALUATION_DATE,
                curve_date=CURVE_DATE,
            )

            if product_type == "FX_RR":
                kwargs["strike"] = round(spot * 1.05, 4)
                kwargs["leg2_call_put"] = "Put"
                kwargs["leg2_strike"] = round(spot * 0.95, 4)
                kwargs["leg2_direction"] = "Sell"

            if product_type == "FX_KI":
                kwargs["barrier_direction"] = "Down & In"
                kwargs["barrier_level"] = round(spot * 0.90, 4)
                kwargs["barrier_type"] = "American"

            if product_type == "FX_KO":
                kwargs["barrier_direction"] = "Up & Out"
                kwargs["barrier_level"] = round(spot * 1.10, 4)
                kwargs["barrier_type"] = "American"

            query = DerivativeQuery(**kwargs)

            try:
                result = svc.price(query)
            except Exception as exc:
                print(f"    ERROR: {exc}")
                continue

            if not result.ok:
                print(f"    ERROR: {result.error}")
                continue

            print(f"    metrics: {list(result.metrics.keys())}")

            payload = {
                "key":            key,
                "product_type":   product_type,
                "label":          spec.label,
                "valuation_date": str(VALUATION_DATE),
                "metrics":        result.metrics,
            }

            filename = f"{product_type}_{key}.json"
            out_path = DEMO_DATA_DIR / filename
            out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            print(f"    Saved -> {filename}\n")

    print("Done.")


if __name__ == "__main__":
    download_all()
