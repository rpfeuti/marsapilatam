"""
Download demo data for all 3 curve types (Raw, Zero Coupon, Discount Factor)
for all demo curves and save them as multi-type JSON snapshots to demo_data/.

Run from the project root with live Bloomberg credentials in .env:
    python scripts/download_demo_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configs.curves_config import CURVE_SIZE, DEMO_CURVES, CurveType
from configs.settings import settings
from services.curves_service import CurveQuery, XMarketCurveService

CURVE_DATE    = date(2026, 3, 18)
DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"

# Monthly date grid from day after CURVE_DATE up to CURVE_SIZE days out
_step: timedelta      = timedelta(days=30)
_date_grid: list[date] = []
_d    = CURVE_DATE + timedelta(days=1)
_limit = CURVE_DATE + timedelta(days=CURVE_SIZE)
while _d < _limit:
    _date_grid.append(_d)
    _d += _step


def download_all() -> None:
    if settings.demo_mode:
        print(
            "ERROR: Bloomberg credentials are not configured. "
            "Set BBG_CLIENT_ID, BBG_CLIENT_SECRET, and BBG_UUID in .env"
        )
        sys.exit(1)

    svc = XMarketCurveService.from_settings(market_date=CURVE_DATE)
    print(f"XMarket session opened for {CURVE_DATE}")
    print(f"Downloading {len(DEMO_CURVES)} curves x 3 types ...\n")

    for entry in DEMO_CURVES:
        print(f"  {entry.curve_id} ({entry.label})")

        raw_df = svc.get_curve(CurveQuery(
            curve_id=entry.curve_id,
            curve_type=CurveType.RAW,
            as_of=CURVE_DATE,
        ))
        print(f"    Raw Curve       -> {len(raw_df)} rows")

        zero_df = svc.get_curve(CurveQuery(
            curve_id=entry.curve_id,
            curve_type=CurveType.ZERO,
            as_of=CURVE_DATE,
            requested_dates=tuple(_date_grid),
        ))
        print(f"    Zero Coupon     -> {len(zero_df)} rows")

        disc_df = svc.get_curve(CurveQuery(
            curve_id=entry.curve_id,
            curve_type=CurveType.DISCOUNT,
            as_of=CURVE_DATE,
            requested_dates=tuple(_date_grid),
        ))
        print(f"    Discount Factor -> {len(disc_df)} rows")

        payload = {
            "curve_id":   entry.curve_id,
            "profile":    entry.profile,
            "label":      entry.label,
            "curve_date": str(CURVE_DATE),
            "raw":        raw_df.to_dict(orient="records"),
            "zero":       zero_df.to_dict(orient="records"),
            "discount":   disc_df.to_dict(orient="records"),
        }

        out_path = DEMO_DATA_DIR / entry.filename
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"    Saved -> {out_path.name}\n")

    print("Done.")


if __name__ == "__main__":
    download_all()
