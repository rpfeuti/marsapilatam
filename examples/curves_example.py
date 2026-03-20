"""
Example: download BRL OIS zero coupon curve from Bloomberg XMarket.

Run from the project root:
    python examples/curves_example.py
"""

from __future__ import annotations

from datetime import date

from bloomberg.exceptions import CurveError
from configs.settings import INTERPOLATION_METHODS
from services.curves_service import CurvesService

MARKET_DATE = date(2024, 4, 18)
CURVE_DATE = date(2024, 4, 18)
CURVE_ID = "S442"           # BRL OIS
CURVE_TYPE = "Zero Coupon"
SIDE = "Mid"
INTERPOLATION = INTERPOLATION_METHODS["Piecewise Linear (Simple)"]

# Generate monthly dates for one year
def monthly_dates(start: date, months: int = 12) -> list[date]:
    result = []
    for m in range(1, months + 1):
        year = start.year + (start.month + m - 1) // 12
        month = (start.month + m - 1) % 12 + 1
        result.append(date(year, month, start.day))
    return result


def main() -> None:
    svc = CurvesService(market_date=MARKET_DATE)
    dates = monthly_dates(CURVE_DATE, months=24)

    print(f"Downloading {CURVE_TYPE} curve {CURVE_ID!r} for {CURVE_DATE} …")
    df = svc.download_curve(
        curve_type=CURVE_TYPE,
        curve_id=CURVE_ID,
        curve_date=CURVE_DATE,
        side=SIDE,
        requested_dates=dates,
        interpolation=INTERPOLATION,
    )

    print(df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except CurveError as e:
        print(f"Curve error: {e}")
