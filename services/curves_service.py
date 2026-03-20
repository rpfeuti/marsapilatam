"""
CurvesService — download and normalize interest rate curves via the MARS XMarket platform.

Supports three curve representations:
- **Raw Curve**        — par rates at the market instruments' own maturities
- **Zero Coupon**      — zero rates interpolated at custom dates
- **Discount Factor**  — discount factors interpolated at custom dates

In demo mode (no Bloomberg credentials) all curves are served from pre-saved
JSON snapshots in the ``demo_data/`` directory.  Run ``scripts/download_demo_data.py``
against live credentials to refresh those snapshots.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from bloomberg.exceptions import CurveError
from bloomberg.webapi import MarsClient
from configs.curves_config import (
    CSA_CURVE_IDS,
    CURVE_SPECS,
    DEMO_CURVES,
    CurveSpec,
    CurveType,
    Side,
)
from configs.settings import settings

_DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"

_DAYS_PER_UNIT: dict[str, int] = {"DAY": 1, "WEEK": 7, "MONTH": 30, "YEAR": 365}
_UNIT_ABBREV:   dict[str, str] = {"DAY": "D", "WEEK": "W", "MONTH": "M", "YEAR": "Y"}


def _parse_tenor(v: object) -> tuple[str, float]:
    """Parse a maturityTenor dict e.g. {"unit": "WEEK", "length": 1} into ("1W", 7.0).

    Non-dict inputs are stringified with 0.0 days — safe for already-normalised data.
    """
    if not isinstance(v, dict):
        return str(v), 0.0
    unit   = str(v.get("unit", "")).upper()
    length = int(v.get("length", 0))
    label  = f"{length}{_UNIT_ABBREV.get(unit, unit)}"
    days   = float(length) * _DAYS_PER_UNIT.get(unit, 1)
    return label, days


class CurvesService:
    """
    Download Bloomberg curve data via the MARS XMarket data platform.

    Args:
        market_date: The historical market date for which to retrieve data.
                     An XMarket session is opened immediately on construction.
                     Ignored in demo mode.
        client:      Optional pre-constructed :class:`MarsClient`. Useful in tests
                     or when sharing a session across multiple service calls.
    """

    def __init__(self, market_date: date, client: MarsClient | None = None) -> None:
        self._demo = settings.demo_mode
        if not self._demo:
            self._client = client or MarsClient(settings, market_date=market_date)

    # ------------------------------------------------------------------
    # Public API — synchronous
    # ------------------------------------------------------------------

    def download_curve(
        self,
        curve_type: CurveType | str,
        curve_id: str,
        curve_date: date,
        side: Side = "Mid",
        requested_dates: list[date] | None = None,
        interpolation: str = "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    ) -> pd.DataFrame:
        """
        Download and normalize a single rate curve.

        Args:
            curve_type:      ``CurveType`` enum member or its string value
                             (``"Raw Curve"``, ``"Zero Coupon"``, ``"Discount Factor"``).
            curve_id:        Bloomberg curve identifier (e.g. ``"S329"`` for COP OIS).
            curve_date:      Curve valuation date.
            side:            ``"Mid"``, ``"Bid"``, or ``"Ask"``.
            requested_dates: Required for Zero Coupon and Discount Factor.
            interpolation:   MARS interpolation method string.

        Returns:
            Normalized :class:`~pandas.DataFrame`.
            Raw Curve includes an extra ``maturityTenor`` (str label) and
            ``_tenor_days`` (float, for chart x-axis) column.

        Raises:
            ValueError:       For unknown ``curve_type`` values.
            NotImplementedError: For CSA curves that are not yet wired up.
            CurveError:       If the API returns an error or the demo file is missing.
        """
        spec = self._resolve_spec(curve_type)

        if self._demo:
            return self._load_demo(curve_id, spec)

        if curve_id.upper() in CSA_CURVE_IDS.values():
            raise NotImplementedError(
                f"CSA curve {curve_id!r} is available in the MARS API but not yet wired up."
            )

        body     = self._build_body(
            curve_type, curve_id, curve_date, side, requested_dates or [], interpolation
        )
        response = self._client.send("POST", "/marswebapi/v1/dataDownload", body)

        if "error" in response:
            raise CurveError(response.get("error_description", str(response["error"])))

        return self._parse_response(response, spec)

    # ------------------------------------------------------------------
    # Public API — asynchronous
    # ------------------------------------------------------------------

    async def download_curve_async(
        self,
        curve_type: CurveType | str,
        curve_id: str,
        curve_date: date,
        side: Side = "Mid",
        requested_dates: list[date] | None = None,
        interpolation: str = "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    ) -> pd.DataFrame:
        """Async version of :meth:`download_curve`."""
        spec = self._resolve_spec(curve_type)

        if self._demo:
            return self._load_demo(curve_id, spec)

        body     = self._build_body(
            curve_type, curve_id, curve_date, side, requested_dates or [], interpolation
        )
        response = await self._client.send_async("POST", "/marswebapi/v1/dataDownload", body)

        if "error" in response:
            raise CurveError(response.get("error_description", str(response["error"])))

        return self._parse_response(response, spec)

    # ------------------------------------------------------------------
    # Private: spec resolution (single validation point for both methods)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_spec(curve_type: CurveType | str) -> CurveSpec:
        """Convert a curve_type string or enum to a CurveSpec, raising ValueError if unknown."""
        try:
            ct = CurveType(curve_type)
            return CURVE_SPECS[ct]
        except (ValueError, KeyError):
            raise ValueError(
                f"Unknown curve_type: {curve_type!r}. "
                f"Valid values: {[ct.value for ct in CurveType]}"
            )

    # ------------------------------------------------------------------
    # Private: demo mode
    # ------------------------------------------------------------------

    def _load_demo(self, curve_id: str, spec: CurveSpec) -> pd.DataFrame:
        """Load a pre-saved curve snapshot from demo_data/ for the given spec."""
        entry = next((c for c in DEMO_CURVES if c.curve_id == curve_id), None)
        if entry is None:
            raise CurveError(
                f"Curve {curve_id!r} is not available in demo mode. "
                f"Available IDs: {[c.curve_id for c in DEMO_CURVES]}"
            )
        path = _DEMO_DATA_DIR / entry.filename
        if not path.exists():
            raise CurveError(f"Demo data file not found: {path}")

        payload = json.loads(path.read_text(encoding="utf-8"))

        if spec.demo_key not in payload:
            raise CurveError(
                f"Key {spec.demo_key!r} missing in demo file {entry.filename!r}. "
                "Re-run scripts/download_demo_data.py to regenerate the demo snapshots."
            )

        return self._normalize(pd.DataFrame(payload[spec.demo_key]))

    # ------------------------------------------------------------------
    # Private: request building
    # ------------------------------------------------------------------

    @staticmethod
    def _build_partial_body(
        curve_type: CurveType | str,
        curve_date: date,
        requested_dates: list[date],
        interpolation: str,
    ) -> dict:
        """Build the curve-type-specific inner body fragment."""
        ct = CurveType(curve_type)
        curve_date_str = str(curve_date)
        match ct:
            case CurveType.RAW:
                return {
                    "rawCurve": {
                        "curveDate": curve_date_str,
                        "settleDate": curve_date_str,
                        "parRate": [],
                    }
                }
            case CurveType.ZERO:
                return {
                    "interpolatedCurve": {
                        "zeroRate": [{"date": str(d), "rate": 0} for d in requested_dates],
                        "interpolationMethodOverride": interpolation,
                    }
                }
            case CurveType.DISCOUNT:
                return {
                    "interpolatedCurve": {
                        "discountFactor": [{"date": str(d), "factor": 0} for d in requested_dates],
                        "interpolationMethodOverride": interpolation,
                        "discountToDateType": "CUSTOM_DATE",
                        "discountToDate": curve_date_str,
                    }
                }

    def _build_body(
        self,
        curve_type: CurveType | str,
        curve_id: str,
        curve_date: date,
        side: str,
        requested_dates: list[date],
        interpolation: str,
    ) -> dict:
        partial = self._build_partial_body(curve_type, curve_date, requested_dates, interpolation)
        return {
            "getDataRequest": {
                "sessionId": self._client.xmarket_session_id,
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

    # ------------------------------------------------------------------
    # Private: response parsing and normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(response: dict, spec: CurveSpec) -> pd.DataFrame:
        """Extract the data rows from the API response envelope and normalise them."""
        try:
            market_data = (
                response["getDataResponse"]["keyAndData"][0]["data"]["marketData"]["data"]
            )
        except (KeyError, IndexError) as exc:
            raise CurveError(f"Unexpected curve response structure: {response}") from exc

        if "error" in market_data:
            raise CurveError(f"Curve not found or invalid — API error: {market_data['error']}")

        try:
            data = market_data["rateCurve"][spec.api_outer][spec.api_inner]
        except KeyError as exc:
            raise CurveError(f"Missing expected key in curve response: {exc}") from exc

        return CurvesService._normalize(pd.DataFrame(data))

    @staticmethod
    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        """Normalise raw API rows: convert maturityTenor dicts to string labels and day counts."""
        if "maturityTenor" not in df.columns:
            return df

        parsed           = df["maturityTenor"].apply(_parse_tenor)
        labels, days     = zip(*parsed)
        df               = df.copy()
        df["maturityTenor"] = list(labels)
        df["_tenor_days"]   = pd.array(list(days), dtype="float64")
        return df
