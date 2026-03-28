"""
FX spot rate service — Bloomberg Desktop API (BLPAPI) implementation.

Fetches current USD cross rates via BlpapiClient.bdp() using the //blp/refdata
service (same terminal connection used by Bloomberg Professional).  Results are
cached in the service instance with a 1-hour TTL so the page does not hammer
the terminal on every re-render.

In demo mode (no Bloomberg credentials) a table of hardcoded reference rates
is returned instead, so the UI works fully offline without a terminal.

Bloomberg FX ticker conventions
--------------------------------
Most pairs are quoted as USD base: USDXXX Curncy → PX_LAST = units of XXX per 1 USD.
EUR is an exception — EURUSD Curncy → PX_LAST = units of USD per 1 EUR (inverted).
The ``_FX_TICKERS`` mapping captures the ``invert`` flag for each currency.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from bloomberg.blpapi_client import BlpapiClient
from bloomberg.exceptions import BlpapiError
from configs.settings import settings

log = logging.getLogger(__name__)

# Bloomberg tickers and inversion flag for USD cross rates.
# invert=True  → PX_LAST is USD-per-foreign (e.g. EURUSD), so rate = 1 / PX_LAST
# invert=False → PX_LAST is already units-of-local per USD (e.g. USDCOP)
_FX_TICKERS: dict[str, tuple[str, bool]] = {
    "COP": ("USDCOP Curncy", False),
    "BRL": ("USDBRL Curncy", False),
    "MXN": ("USDMXN Curncy", False),
    "PEN": ("USDPEN Curncy", False),
    "CLP": ("USDCLP Curncy", False),
    "EUR": ("EURUSD Curncy", True),   # EURUSD = USD per EUR → invert to get EUR per USD
}

_TTL_SECS = 3600  # re-fetch at most once per hour

# Fallback rates used in demo mode (no terminal) or when the BLPAPI call fails.
_HARDCODED_RATES: dict[str, float] = {
    "COP": 4_300.0,
    "BRL": 5.70,
    "MXN": 17.20,
    "PEN": 3.72,
    "CLP": 960.0,
    "EUR": 0.92,
    "USD": 1.0,
}

_FX_RATES_PATH = Path(__file__).resolve().parent.parent / "demo_data" / "fx_derivatives" / "fx_rates.json"


def _load_demo_rates() -> dict[str, float]:
    """Load rates from demo_data/fx_rates.json, falling back to hardcoded values."""
    if _FX_RATES_PATH.exists():
        try:
            return json.loads(_FX_RATES_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Failed to load %s: %s — using hardcoded rates.", _FX_RATES_PATH.name, exc)
    return dict(_HARDCODED_RATES)


_DEMO_RATES: dict[str, float] = _load_demo_rates()


class FxRateService:
    """
    USD cross-rate provider backed by Bloomberg Desktop API (BLPAPI).

    Designed to be stored in ``st.session_state`` (one instance per browser
    session).  Rates are fetched in a single batched ``bdp()`` call and cached
    locally for ``_TTL_SECS`` seconds.

    In demo mode (``client=None``) the hardcoded ``_DEMO_RATES`` are returned
    without any network activity.
    """

    def __init__(self, client: BlpapiClient | None = None) -> None:
        self._client     = client
        self._rates:     dict[str, float] = {}
        self._fetched_at: float           = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_rate(self, local_ccy: str) -> float | None:
        """Return the current USD/{local_ccy} spot rate, or None if unavailable.

        Rate is cached for _TTL_SECS seconds.  Falls back to _DEMO_RATES when
        the BLPAPI call fails.
        """
        if self._client is None:
            return _DEMO_RATES.get(local_ccy.upper())

        now = time.monotonic()
        if not self._rates or (now - self._fetched_at) > _TTL_SECS:
            self._refresh_rates()

        return self._rates.get(local_ccy.upper())

    def default_leg2_notional(self, usd_notional: float, local_ccy: str) -> float:
        """Return usd_notional * spot_rate, rounded to the nearest integer."""
        rate = self.get_rate(local_ccy)
        if rate is None or rate <= 0:
            return usd_notional
        return round(usd_notional * rate)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_settings(cls) -> FxRateService:
        """
        Factory: returns a demo instance when credentials are absent, or a
        live instance backed by a BlpapiClient otherwise.

        BlpapiError (terminal not running) is caught here and falls back to
        demo mode so the app still starts when the terminal is offline.
        """
        if settings.demo_mode:
            return cls(client=None)
        try:
            client = BlpapiClient(host=settings.blpapi_host, port=settings.blpapi_port)
            return cls(client=client)
        except BlpapiError as exc:
            log.warning(
                "BLPAPI unavailable (%s) — FX rates will use demo fallback values.", exc
            )
            return cls(client=None)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _refresh_rates(self) -> None:
        """Fetch all FX rates in a single batched bdp() call and update cache."""
        tickers = [ticker for ticker, _ in _FX_TICKERS.values()]
        try:
            if self._client is None:
                self._rates = dict(_DEMO_RATES)
                self._fetched_at = time.monotonic()
                return
            raw = self._client.bdp(tickers, ["PX_LAST"])
        except BlpapiError as exc:
            log.warning("FX rate fetch failed (%s) — using demo fallback rates.", exc)
            self._rates = dict(_DEMO_RATES)
            self._fetched_at = time.monotonic()
            return

        rates: dict[str, float] = {"USD": 1.0}
        for ccy, (ticker, invert) in _FX_TICKERS.items():
            field_data = raw.get(ticker, {})
            px = field_data.get("PX_LAST")
            if px is None:
                log.warning("PX_LAST missing for %s — skipping.", ticker)
                continue
            try:
                px = float(px)
                rates[ccy] = (1.0 / px) if invert else px
            except (TypeError, ValueError, ZeroDivisionError):
                log.warning("Invalid PX_LAST value for %s: %r", ticker, px)

        self._rates      = rates if len(rates) > 1 else dict(_DEMO_RATES)
        self._fetched_at = time.monotonic()
        log.debug("FX rates refreshed — %d currencies loaded.", len(self._rates))
