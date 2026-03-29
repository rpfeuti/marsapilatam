"""
Refresh all demo data snapshots for a given reference date.

Run this script once from a machine with live Bloomberg MARS credentials to
regenerate every JSON file under demo_data/.  After running it, commit the
updated files and the app will use them in demo mode (e.g. on Streamlit Cloud).

Usage::

    python scripts/refresh_demo_data.py            # defaults to 2026-03-27
    python scripts/refresh_demo_data.py 2026-03-27

The script refreshes:
  - demo_data/curves/           (7 curves × RAW + ZERO + DISCOUNT)
  - demo_data/swaps/            (6 OIS + 6 XCCY, 5Y tenor)
  - demo_data/fx_derivatives/   (4 product types × 6 currency pairs)
  - demo_data/fx_derivatives/fx_rates.json
  - demo_data/sofr_schedules.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so local imports work
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from bloomberg.webapi import MarsClient                         # noqa: E402
from configs.curves_config import CURVE_SPECS, DEMO_CURVES, CurveType  # noqa: E402
from configs.derivatives_config import (                         # noqa: E402
    FX_KI_SPECS, FX_KO_SPECS, FX_RR_SPECS, FX_VANILLA_SPECS,
)
from configs.settings import settings                            # noqa: E402
from configs.swaps_config import (                               # noqa: E402
    OIS_DEMO_SNAPSHOTS, OIS_SWAP_SPECS,
    XCCY_DEMO_SNAPSHOTS, XCCY_SWAP_SPECS,
)
from services.bootstrap_service import BootstrapService, SOFR_TENORS  # noqa: E402
from services.curves_service import CurveQuery, XMarketRepository  # noqa: E402
from services.fx_derivatives_service import (                    # noqa: E402
    DerivativeLiveRepository, DerivativeQuery,
)
from services.swaps_service import SwapLiveRepository, SwapQuery  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEMO_CURVES_DIR  = PROJECT_ROOT / "demo_data" / "curves"
DEMO_SWAPS_DIR   = PROJECT_ROOT / "demo_data" / "swaps"
DEMO_FX_DIR      = PROJECT_ROOT / "demo_data" / "fx_derivatives"
SOFR_SCHED_PATH  = PROJECT_ROOT / "demo_data" / "sofr_schedules.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"  saved {path.relative_to(PROJECT_ROOT)}")


# ---------------------------------------------------------------------------
# 1. Curves
# ---------------------------------------------------------------------------

def refresh_curves(as_of: date) -> None:
    """Curves need their own MarsClient with market_date to get an XMarket session."""
    print("\n=== Curves ===")
    curve_client = MarsClient(settings, market_date=as_of)
    repo = XMarketRepository(curve_client)

    step  = timedelta(days=30)
    limit = as_of + timedelta(days=12_000)
    monthly_dates: tuple[date, ...] = tuple(
        as_of + timedelta(days=1) + step * i
        for i in range(400)
        if as_of + timedelta(days=1) + step * i < limit
    )

    for demo_curve in DEMO_CURVES:
        print(f"  {demo_curve.curve_id}  {demo_curve.profile}")
        snapshot: dict = {
            "curve_id":   demo_curve.curve_id,
            "profile":    demo_curve.profile,
            "label":      demo_curve.label,
            "curve_date": str(as_of),
        }
        for curve_type in CurveType:
            key   = CURVE_SPECS[curve_type].demo_key
            dates = () if curve_type == CurveType.RAW else monthly_dates
            query = CurveQuery(
                curve_id=demo_curve.curve_id,
                curve_type=curve_type,
                as_of=as_of,
                requested_dates=dates,
            )
            try:
                df = repo.fetch(query)
                snapshot[key] = df.to_dict(orient="records")
                print(f"    {curve_type}: {len(df)} rows")
            except Exception as exc:
                print(f"    {curve_type}: ERROR — {exc}")
                snapshot[key] = []

        dest = DEMO_CURVES_DIR / demo_curve.filename
        _save(dest, snapshot)


# ---------------------------------------------------------------------------
# 2. Swaps (OIS + XCCY)
# ---------------------------------------------------------------------------

def refresh_swaps(client: MarsClient, val_date: date) -> None:
    print("\n=== Swaps ===")
    repo = SwapLiveRepository(client)

    effective = val_date
    maturity  = _add_years(val_date, 5)

    # OIS swaps
    for snap in OIS_DEMO_SNAPSHOTS:
        spec = OIS_SWAP_SPECS[snap.key]
        print(f"  OIS  {snap.key}")
        query = SwapQuery(
            key=snap.key,
            swap_type="OIS",
            direction="Receive",
            effective_date=effective,
            maturity_date=maturity,
            valuation_date=val_date,
            curve_date=val_date,
            notional=spec.notional,
            forward_curve=spec.forward_curve,
            discount_curve=spec.discount_curve,
            float_index=spec.float_index,
            pay_frequency=spec.pay_frequency,
            day_count=spec.day_count,
            fixed_rate=None,
            solve_for="Coupon",
        )
        try:
            result = repo.price(query)
            payload = {
                "key":            snap.key,
                "swap_type":      snap.swap_type,
                "label":          spec.label,
                "tenor":          snap.tenor,
                "valuation_date": str(val_date),
                "par_rate":       result.par_rate,
                "metrics":        result.metrics,
            }
            _save(DEMO_SWAPS_DIR / snap.filename, payload)
        except Exception as exc:
            print(f"    ERROR — {exc}")

    # XCCY swaps
    for snap in XCCY_DEMO_SNAPSHOTS:
        spec = XCCY_SWAP_SPECS[snap.key]
        print(f"  XCCY {snap.key}")
        query = SwapQuery(
            key=snap.key,
            swap_type="XCCY",
            direction="Receive",
            effective_date=effective,
            maturity_date=maturity,
            valuation_date=val_date,
            curve_date=val_date,
            notional=spec.notional,
            forward_curve=spec.forward_curve,
            discount_curve=spec.discount_curve,
            float_index=spec.float_index,
            pay_frequency=spec.pay_frequency,
            day_count=spec.day_count,
            fixed_rate=None,
            solve_for="Coupon",
            leg1_forward_curve=spec.leg1_forward_curve,
            leg1_discount_curve=spec.leg1_discount_curve,
        )
        try:
            result = repo.price(query)
            payload = {
                "key":            snap.key,
                "swap_type":      snap.swap_type,
                "label":          spec.label,
                "tenor":          snap.tenor,
                "valuation_date": str(val_date),
                "par_rate":       result.par_rate,
                "metrics":        result.metrics,
            }
            _save(DEMO_SWAPS_DIR / snap.filename, payload)
        except Exception as exc:
            print(f"    ERROR — {exc}")


# ---------------------------------------------------------------------------
# 3. FX Derivatives
# ---------------------------------------------------------------------------

# ATM spot rates for 2026-03-27 (sourced from BLPAPI refresh).
# EURUSD is stored as EUR/USD (units of USD per EUR).
_SPOT_RATES: dict[str, float] = {
    "EURUSD": 1.1508,   # 1 / 0.8688
    "USDCOP": 3665.7,
    "USDMXN": 18.12,
    "USDPEN": 3.486,
    "USDBRL": 5.239,
    "USDCLP": 922.94,
}


def refresh_fx_derivatives(client: MarsClient, val_date: date) -> None:
    print("\n=== FX Derivatives ===")
    repo = DerivativeLiveRepository(client)

    expiry = val_date + timedelta(days=91)   # ~3M

    products = {
        "FX_VANILLA": FX_VANILLA_SPECS,
        "FX_RR":      FX_RR_SPECS,
        "FX_KI":      FX_KI_SPECS,
        "FX_KO":      FX_KO_SPECS,
    }

    for product_type, specs in products.items():
        for key, spec in specs.items():
            print(f"  {product_type}  {key}")
            spot = _SPOT_RATES.get(key, 1.0)

            if product_type == "FX_VANILLA":
                strike        = round(spot, 4)
                barrier_dir   = ""
                barrier_level = 0.0
                leg2_cp = leg2_dir = ""
                leg2_strike = 0.0
            elif product_type == "FX_RR":
                strike        = round(spot * 1.05, 4)
                leg2_strike   = round(spot * 0.95, 4)
                leg2_cp       = "Put"
                leg2_dir      = "Sell"
                barrier_dir   = ""
                barrier_level = 0.0
            elif product_type == "FX_KI":
                strike        = round(spot, 4)
                barrier_dir   = "Down & In"
                barrier_level = round(spot * 0.90, 4)
                leg2_cp = leg2_dir = ""
                leg2_strike = 0.0
            else:  # FX_KO
                strike        = round(spot, 4)
                barrier_dir   = "Down & Out"
                barrier_level = round(spot * 0.90, 4)
                leg2_cp = leg2_dir = ""
                leg2_strike = 0.0

            query = DerivativeQuery(
                key=key,
                product_type=product_type,
                direction="Buy",
                call_put="Call",
                notional=spec.notional,
                strike=strike,
                expiry_date=expiry,
                valuation_date=val_date,
                curve_date=val_date,
                exercise_type="European",
                leg2_call_put=leg2_cp,
                leg2_strike=leg2_strike,
                leg2_direction=leg2_dir,
                barrier_direction=barrier_dir,
                barrier_level=barrier_level,
                barrier_type="American",
            )
            try:
                result = repo.price(query)
                payload = {
                    "key":            key,
                    "product_type":   product_type,
                    "label":          spec.label,
                    "valuation_date": str(val_date),
                    "metrics":        result.metrics,
                }
                filename = f"{product_type}_{key}.json"
                _save(DEMO_FX_DIR / filename, payload)
            except Exception as exc:
                print(f"    ERROR — {exc}")


# ---------------------------------------------------------------------------
# 4. FX spot rates
# ---------------------------------------------------------------------------

def refresh_fx_rates(val_date: date) -> None:
    print("\n=== FX Rates ===")
    rates: dict[str, float] = {"USD": 1.0}

    # Try live BLPAPI (historical for val_date)
    try:
        from bloomberg.blpapi_client import BlpapiClient
        from bloomberg.exceptions import BlpapiError
        _FX_TICKERS = {
            "COP": ("USDCOP Curncy", False),
            "BRL": ("USDBRL Curncy", False),
            "MXN": ("USDMXN Curncy", False),
            "PEN": ("USDPEN Curncy", False),
            "CLP": ("USDCLP Curncy", False),
            "EUR": ("EURUSD Curncy", True),
        }
        tickers = [t for t, _ in _FX_TICKERS.values()]
        today   = date.today()
        hist    = val_date if val_date < today else None

        with BlpapiClient() as blp:
            raw = blp.bdh(tickers, ["PX_LAST"], hist) if hist else blp.bdp(tickers, ["PX_LAST"])

        for ccy, (ticker, invert) in _FX_TICKERS.items():
            px = (raw.get(ticker) or {}).get("PX_LAST")
            if px is not None:
                rates[ccy] = round(1.0 / float(px), 6) if invert else float(px)
        print(f"  fetched {len(rates)} rates from BLPAPI")
    except Exception as exc:
        print(f"  BLPAPI unavailable ({exc}), using hardcoded fallback rates")
        rates.update({"COP": 4_350.0, "BRL": 5.75, "MXN": 20.30,
                      "PEN": 3.77, "CLP": 975.0, "EUR": 0.918})

    _save(DEMO_FX_DIR / "fx_rates.json", rates)


# ---------------------------------------------------------------------------
# 5. SOFR schedules
# ---------------------------------------------------------------------------

def refresh_sofr_schedules(client: MarsClient, val_date: date) -> None:
    print("\n=== SOFR Schedules ===")
    svc = BootstrapService(client=client)
    schedules = asyncio.run(svc.fetch_schedules_async(SOFR_TENORS, effective_date=val_date))

    payload: dict = {
        "as_of": str(val_date),
        "schedules": {},
    }
    for tenor, sched in schedules.items():
        payload["schedules"][tenor] = [
            {
                "accrual_start": str(p.accrual_start),
                "accrual_end":   str(p.accrual_end),
                "payment_date":  str(p.payment_date),
                "day_count":     p.day_count,
                "year_fraction": p.year_fraction,
            }
            for p in sched.periods
        ]
    print(f"  fetched {len(schedules)} tenor schedules")
    _save(SOFR_SCHED_PATH, payload)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if settings.demo_mode:
        print("ERROR: No Bloomberg MARS credentials found in .env — cannot run in demo mode.")
        sys.exit(1)

    ref_date = date(2026, 3, 27)
    if len(sys.argv) > 1:
        ref_date = date.fromisoformat(sys.argv[1])

    print(f"Refreshing demo data for {ref_date} …")

    client = MarsClient(settings)

    refresh_curves(ref_date)
    refresh_swaps(client, ref_date)
    refresh_fx_derivatives(client, ref_date)
    refresh_fx_rates(ref_date)
    refresh_sofr_schedules(client, ref_date)

    print("\nDone. All demo_data files have been updated.")
    print("Commit the changes and deploy to Streamlit Cloud.")


if __name__ == "__main__":
    main()
