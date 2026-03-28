"""
Download current FX spot rates via BLPAPI and save as a JSON snapshot to
demo_data/fx_rates.json for offline/demo mode.

Run from the project root with a Bloomberg Terminal connection:
    python scripts/download_fx_rates_demo_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloomberg.blpapi_client import BlpapiClient
from bloomberg.exceptions import BlpapiError
from configs.settings import settings

DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data" / "fx_derivatives"

_FX_TICKERS: dict[str, tuple[str, bool]] = {
    "COP": ("USDCOP Curncy", False),
    "BRL": ("USDBRL Curncy", False),
    "MXN": ("USDMXN Curncy", False),
    "PEN": ("USDPEN Curncy", False),
    "CLP": ("USDCLP Curncy", False),
    "EUR": ("EURUSD Curncy", True),
}


def download_all() -> None:
    print("Connecting to Bloomberg Terminal (BLPAPI) ...")
    try:
        client = BlpapiClient(host=settings.blpapi_host, port=settings.blpapi_port)
    except BlpapiError as exc:
        print(f"ERROR: Cannot connect to Bloomberg Terminal: {exc}")
        sys.exit(1)

    tickers = [ticker for ticker, _ in _FX_TICKERS.values()]
    print(f"Fetching PX_LAST for {len(tickers)} tickers ...\n")

    raw = client.bdp(tickers, ["PX_LAST"])

    rates: dict[str, float] = {"USD": 1.0}
    for ccy, (ticker, invert) in _FX_TICKERS.items():
        field_data = raw.get(ticker, {})
        px = field_data.get("PX_LAST")
        if px is None:
            print(f"  WARNING: PX_LAST missing for {ticker}")
            continue
        try:
            px = float(px)
            rate = (1.0 / px) if invert else px
            rates[ccy] = round(rate, 6)
            print(f"  {ccy}: {rate:.6f}  ({ticker})")
        except (TypeError, ValueError, ZeroDivisionError):
            print(f"  WARNING: Invalid PX_LAST for {ticker}: {px!r}")

    out_path = DEMO_DATA_DIR / "fx_rates.json"
    out_path.write_text(json.dumps(rates, indent=2), encoding="utf-8")
    print(f"\nSaved {len(rates)} rates -> {out_path.name}")
    print("Done.")


if __name__ == "__main__":
    download_all()
