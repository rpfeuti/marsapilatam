"""
Example: download BRL OIS zero coupon curve from Bloomberg XMarket.

Run from the project root:
    python examples/curves_example.py
"""

from __future__ import annotations

from datetime import date

from bloomberg.exceptions import CurveError
from configs.curves_config import INTERPOLATION_METHODS, CurveType
from services.curves_service import CurveQuery, XMarketCurveService

MARKET_DATE   = date(2024, 4, 18)
CURVE_DATE    = date(2024, 4, 18)
CURVE_ID      = "S442"           # BRL OIS
CURVE_TYPE    = CurveType.ZERO
SIDE          = "Mid"
INTERPOLATION = INTERPOLATION_METHODS["Piecewise Linear (Simple)"]


def monthly_dates(start: date, months: int = 12) -> tuple[date, ...]:
    result: list[date] = []
    for m in range(1, months + 1):
        year  = start.year + (start.month + m - 1) // 12
        month = (start.month + m - 1) % 12 + 1
        result.append(date(year, month, start.day))
    return tuple(result)


def main() -> None:
    svc   = XMarketCurveService.from_settings(market_date=MARKET_DATE)
    query = CurveQuery(
        curve_id=CURVE_ID,
        curve_type=CURVE_TYPE,
        as_of=CURVE_DATE,
        side=SIDE,
        requested_dates=monthly_dates(CURVE_DATE, months=24),
        interpolation=INTERPOLATION,
    )

    print(f"Downloading {CURVE_TYPE} curve {CURVE_ID!r} for {CURVE_DATE} ...")
    df = svc.get_curve(query)
    print(df.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except CurveError as e:
        print(f"Curve error: {e}")
