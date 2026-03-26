"""
Download demo swap pricing results for all OIS and XCCY templates and save
them as JSON snapshots to demo_data/swaps/.

Run from the project root with live Bloomberg credentials in .env:
    python scripts/download_swap_demo_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configs.settings import settings
from configs.swaps_config import (
    OIS_SWAP_SPECS,
    XCCY_SWAP_SPECS,
)
from services.swaps_service import SwapPricingService, SwapQuery

VALUATION_DATE = date(2026, 3, 26)
CURVE_DATE     = date(2026, 3, 26)
DEMO_TENOR     = "5Y"
DEMO_DATA_DIR  = Path(__file__).resolve().parent.parent / "demo_data" / "swaps"


def download_all() -> None:
    if settings.demo_mode:
        print(
            "ERROR: Bloomberg credentials are not configured. "
            "Set BBG_CLIENT_ID, BBG_CLIENT_SECRET, and BBG_UUID in .env"
        )
        sys.exit(1)

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)

    svc = SwapPricingService.from_settings()
    print(f"Deal session ready. Valuation date: {VALUATION_DATE}\n")

    all_specs = [
        ("OIS",  OIS_SWAP_SPECS),
        ("XCCY", XCCY_SWAP_SPECS),
    ]

    for swap_type, spec_dict in all_specs:
        print(f"--- {swap_type} Swaps ---")
        for key, spec in spec_dict.items():
            print(f"  {key} ({spec.label})")
            query = SwapQuery(
                key=key,
                swap_type=swap_type,
                direction="Receive",
                tenor=DEMO_TENOR,
                valuation_date=VALUATION_DATE,
                curve_date=CURVE_DATE,
                notional=spec.notional,
                discount_curve=spec.discount_curve,
                forward_curve=spec.forward_curve,
                csa_ccy=spec.csa_ccy,
                coll_curve=spec.coll_curve,
                float_index=spec.float_index,
                pay_frequency=spec.pay_frequency,
                day_count=spec.day_count,
                fixed_rate=None,  # solve for par rate
            )
            result = svc.price(query)

            if not result.ok:
                print(f"    ERROR: {result.error}")
                continue

            par_str = f"{result.par_rate:.6f}" if result.par_rate is not None else "N/A"
            print(f"    Par rate: {par_str}  |  metrics: {list(result.metrics.keys())}")

            payload = {
                "key":            key,
                "swap_type":      swap_type,
                "label":          spec.label,
                "tenor":          DEMO_TENOR,
                "valuation_date": str(VALUATION_DATE),
                "par_rate":       result.par_rate,
                "metrics":        result.metrics,
            }

            filename = f"{key}_{DEMO_TENOR}.json"
            out_path = DEMO_DATA_DIR / filename
            out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            print(f"    Saved -> {out_path.name}\n")

    print("Done.")


if __name__ == "__main__":
    download_all()
