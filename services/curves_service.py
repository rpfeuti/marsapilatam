"""
CurvesService — download interest rate curves via the MARS XMarket platform.

Supports three curve representations:
- **Raw Curve**        — par rates at the market instruments' own maturities
- **Zero Coupon**      — zero rates interpolated at custom dates
- **Discount Factor**  — discount factors interpolated at custom dates

Requires a ``market_date`` to open an XMarket session at construction time.
In demo mode (no Bloomberg credentials) curves are served from pre-saved
JSON files in the ``demo_data/`` directory.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from bloomberg.exceptions import CurveError
from bloomberg.webapi import MarsClient
from configs.settings import CSA_CURVE_IDS, CURVE_API_FIELDS, CURVE_TYPES, DEMO_CURVES, settings

# Path to the pre-saved demo JSON files (relative to project root)
_DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"


class CurvesService:
    """
    Download Bloomberg curve data via the MARS XMarket data platform.

    Args:
        market_date: The historical market date for which to retrieve data.
                     An XMarket session is opened immediately.
                     Ignored in demo mode.
        client:      Optional pre-constructed :class:`MarsClient`.  Supply this
                     in tests or when you want to share a session.
    """

    def __init__(self, market_date: date, client: MarsClient | None = None) -> None:
        self._demo = settings.demo_mode
        if not self._demo:
            if client is not None:
                self._client = client
            else:
                self._client = MarsClient(settings, market_date=market_date)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_curve(
        self,
        curve_type: str,
        curve_id: str,
        curve_date: date,
        side: str = "Mid",
        requested_dates: list[date] | None = None,
        interpolation: str = "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    ) -> pd.DataFrame:
        """
        Download a single rate curve.

        In demo mode, serves pre-saved JSON data from ``demo_data/``.

        Args:
            curve_type:       One of ``"Raw Curve"``, ``"Zero Coupon"``, ``"Discount Factor"``.
            curve_id:         Bloomberg curve identifier (e.g. ``"S329"`` for COP OIS).
            curve_date:       Curve valuation date.
            side:             ``"Mid"``, ``"Bid"``, or ``"Ask"``.
            requested_dates:  Required for Zero Coupon and Discount Factor.
            interpolation:    MARS interpolation method string.

        Returns:
            DataFrame with columns depending on curve type.

        Raises:
            ValueError: For unsupported curve types.
            CurveError: If the API returns an error or the demo file is missing.
        """
        if curve_type not in CURVE_TYPES:
            raise ValueError(f"curve_type must be one of {CURVE_TYPES}, got {curve_type!r}")

        if self._demo:
            return self._load_demo(curve_id, curve_type)

        if curve_id.upper() in CSA_CURVE_IDS.values():
            raise NotImplementedError(
                f"CSA curve {curve_id!r} is available in the MARS API but not yet implemented."
            )

        body = self._build_body(
            curve_type, curve_id, curve_date, side, requested_dates or [], interpolation
        )
        response = self._client.send("POST", "/marswebapi/v1/dataDownload", body)

        if "error" in response:
            raise CurveError(response.get("error_description", str(response["error"])))

        return self._parse_response(response, curve_type)

    # ------------------------------------------------------------------
    # Demo mode helper
    # ------------------------------------------------------------------

    def _load_demo(self, curve_id: str, curve_type: str) -> pd.DataFrame:
        """Load a pre-saved curve from demo_data/ for the requested curve type."""
        entry = next((c for c in DEMO_CURVES if c["curve_id"] == curve_id), None)
        if entry is None:
            raise CurveError(
                f"Curve {curve_id!r} is not available in demo mode. "
                f"Available: {[c['curve_id'] for c in DEMO_CURVES]}"
            )
        path = _DEMO_DATA_DIR / entry["filename"]
        if not path.exists():
            raise CurveError(f"Demo data file not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        key_map = {
            "Raw Curve": "raw",
            "Zero Coupon": "zero",
            "Discount Factor": "discount",
        }
        key = key_map[curve_type]
        if key not in payload:
            raise CurveError(
                f"Curve type {curve_type!r} not found in demo file {entry['filename']}. "
                "Re-run scripts/download_demo_data.py to regenerate demo data."
            )
        return pd.DataFrame(payload[key])

    async def download_curve_async(
        self,
        curve_type: str,
        curve_id: str,
        curve_date: date,
        side: str = "Mid",
        requested_dates: list[date] | None = None,
        interpolation: str = "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    ) -> pd.DataFrame:
        """Async version of :meth:`download_curve`."""
        if curve_type not in CURVE_TYPES:
            raise ValueError(f"curve_type must be one of {CURVE_TYPES}, got {curve_type!r}")

        body = self._build_body(
            curve_type, curve_id, curve_date, side, requested_dates or [], interpolation
        )
        response = await self._client.send_async("POST", "/marswebapi/v1/dataDownload", body)

        if "error" in response:
            raise CurveError(response.get("error_description", str(response["error"])))

        return self._parse_response(response, curve_type)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_partial_body(
        self,
        curve_type: str,
        curve_date: date,
        requested_dates: list[date],
        interpolation: str,
    ) -> dict:
        curve_date_str = str(curve_date)
        match curve_type:
            case "Raw Curve":
                return {
                    "rawCurve": {
                        "curveDate": curve_date_str,
                        "settleDate": curve_date_str,
                        "parRate": [],
                    }
                }
            case "Zero Coupon":
                return {
                    "interpolatedCurve": {
                        "zeroRate": [{"date": str(d), "rate": 0} for d in requested_dates],
                        "interpolationMethodOverride": interpolation,
                    }
                }
            case "Discount Factor":
                return {
                    "interpolatedCurve": {
                        "discountFactor": [{"date": str(d), "factor": 0} for d in requested_dates],
                        "interpolationMethodOverride": interpolation,
                        "discountToDateType": "CUSTOM_DATE",
                        "discountToDate": curve_date_str,
                    }
                }
            case _:
                raise ValueError(f"Unsupported curve type: {curve_type!r}")

    def _build_body(
        self,
        curve_type: str,
        curve_id: str,
        curve_date: date,
        side: str,
        requested_dates: list[date],
        interpolation: str,
    ) -> dict:
        partial = self._build_partial_body(curve_type, curve_date, requested_dates, interpolation)
        session_id = self._client.xmarket_session_id
        return {
            "getDataRequest": {
                "sessionId": session_id,
                "keyAndData": [
                    {
                        "key": {"rateCurveKey": {"curveId": curve_id}},
                        "data": {
                            "marketData": {
                                "side": side,
                                "data": {"rateCurve": partial},
                            }
                        },
                    }
                ],
            }
        }

    def _parse_response(self, response: dict, curve_type: str) -> pd.DataFrame:
        try:
            market_data = (
                response["getDataResponse"]["keyAndData"][0]["data"]["marketData"]["data"]
            )
        except (KeyError, IndexError) as exc:
            raise CurveError(f"Unexpected curve response structure: {response}") from exc

        if "error" in market_data:
            raise CurveError(
                f"Curve not found or invalid — API error: {market_data['error']}"
            )

        api_curve_key = CURVE_API_FIELDS[curve_type][2]   # e.g. "rawCurve"
        api_rate_key = CURVE_API_FIELDS[curve_type][3]    # e.g. "parRate"

        try:
            data = market_data["rateCurve"][api_curve_key][api_rate_key]
        except KeyError as exc:
            raise CurveError(f"Missing expected key in curve response: {exc}") from exc

        return pd.DataFrame(data)
