"""
XMarket interest rate curve service — Repository pattern.

Architecture:
    CurveQuery          — immutable value object describing a single download request
    CurveRepository     — structural Protocol (interface) for any data source
    XMarketRepository   — live Bloomberg MARS XMarket implementation
    DemoRepository      — offline, pre-saved JSON snapshot implementation
    XMarketCurveService — thin orchestrator: delegates to repository, enriches result

The two concrete repositories are the only places that know about Bloomberg
credentials or the filesystem.  XMarketCurveService knows neither; it only
calls fetch() and applies normalisation.  Swapping demo ↔ live or injecting
a test double requires changing exactly one line at construction time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

import pandas as pd
from pydantic import ValidationError

from bloomberg.api_models import (
    DataDownloadRequest,
    DataDownloadResponse,
    GetDataRequest,
    KeyAndDataItem,
    _DataKey,
    _RateCurveKey,
)
from bloomberg.exceptions import CurveError
from bloomberg.webapi import MarsClient
from configs.curves_config import (
    CSA_CURVE_IDS,
    CURVE_SPECS,
    DEMO_CURVES,
    CurveSpec,
    CurveType,
    DemoCurve,
    Side,
)
from configs.settings import settings

_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "demo_data" / "curves"

# Tenor unit → approximate days, and → single-letter abbreviation for labels
_TENOR_DAYS:  dict[str, int] = {"DAY": 1, "WEEK": 7, "MONTH": 30, "YEAR": 365}
_TENOR_LABEL: dict[str, str] = {"DAY": "D", "WEEK": "W", "MONTH": "M", "YEAR": "Y"}


# ===========================================================================
# Value object
# ===========================================================================


@dataclass(frozen=True)
class CurveQuery:
    """
    Immutable value object that fully describes a single curve download request.

    Frozen + hashable means it can be used directly as a key in st.cache_data,
    replacing the previous flat list of individual scalar arguments.
    Accepts plain strings for curve_type — they are coerced to CurveType in
    __post_init__ so callers can use either form without ceremony.
    """

    curve_id:        str
    curve_type:      CurveType
    as_of:           date
    side:            Side             = "Mid"
    requested_dates: tuple[date, ...] = ()
    interpolation:   str              = "INTERPOLATION_METHOD_LINEAR_SIMPLE"

    def __post_init__(self) -> None:
        object.__setattr__(self, "curve_type", CurveType(self.curve_type))


# ===========================================================================
# Repository Protocol
# ===========================================================================


class CurveRepository(Protocol):
    """
    Structural interface for curve data sources.

    Any object with a matching fetch() signature satisfies this protocol
    without inheritance — plain duck typing, verified statically by mypy/pyright.
    """

    def fetch(self, query: CurveQuery) -> pd.DataFrame: ...


# ===========================================================================
# Pure helper functions (no state, easily unit-tested)
# ===========================================================================


def _decode_tenor(raw: object) -> tuple[str, float]:
    """Decode one raw maturityTenor API value into a (label, days) pair.

    API format: {"unit": "WEEK", "length": 2}  ->  ("2W", 14.0)
    Already-decoded strings pass through:         ->  ("2W",  0.0)
    """
    if not isinstance(raw, dict):
        return str(raw), 0.0
    unit   = str(raw.get("unit", "")).upper()
    length = int(raw.get("length", 0))
    return (
        f"{length}{_TENOR_LABEL.get(unit, unit)}",
        float(length) * _TENOR_DAYS.get(unit, 1),
    )


def _enrich_tenors(df: pd.DataFrame) -> pd.DataFrame:
    """Decode maturityTenor dicts and add a tenor_days column for charting.

    Only acts on Raw Curve data (which carries a maturityTenor column).
    Returns the DataFrame unchanged for Zero Coupon and Discount Factor.
    """
    if "maturityTenor" not in df.columns or df.empty:
        return df

    decoded            = df["maturityTenor"].apply(_decode_tenor)
    labels, days       = zip(*decoded)
    df                 = df.copy()
    df["maturityTenor"] = list(labels)
    df["tenor_days"]    = pd.array(list(days), dtype="float64")
    return df


def _build_api_request(
    spec:       CurveSpec,
    query:      CurveQuery,
    session_id: str | None,
) -> dict:
    """Build and serialise a DataDownloadRequest from a CurveSpec + CurveQuery."""
    as_of_str = str(query.as_of)

    if spec.api_outer == "rawCurve":
        rate_curve: dict = {
            spec.api_outer: {
                "curveDate":    as_of_str,
                "settleDate":   as_of_str,
                spec.api_inner: [],
            }
        }
    else:
        inner: dict = {
            spec.api_inner: [
                {"date": str(d), spec.value_col: 0} for d in query.requested_dates
            ],
            "interpolationMethodOverride": query.interpolation,
        }
        if spec.api_inner == "discountFactor":
            inner["discountToDateType"] = "CUSTOM_DATE"
            inner["discountToDate"]     = as_of_str
        rate_curve = {spec.api_outer: inner}

    return DataDownloadRequest(
        get_data_request=GetDataRequest(
            session_id=session_id,
            key_and_data=[
                KeyAndDataItem(
                    key=_DataKey(rate_curve_key=_RateCurveKey(curve_id=query.curve_id)),
                    data={"marketData": {
                        "side": query.side,
                        "data": {"rateCurve": rate_curve},
                    }},
                )
            ],
        )
    ).model_dump(by_alias=True)


def _extract_rows(response: dict, spec: CurveSpec) -> pd.DataFrame:
    """Validate the API response envelope and return curve rows as a DataFrame."""
    try:
        parsed      = DataDownloadResponse.model_validate(response)
        market_data = parsed.get_data_response.key_and_data[0].data.market_data
    except (ValidationError, IndexError) as exc:
        raise CurveError(f"Unexpected API response structure: {exc}") from exc

    if market_data.error:
        raise CurveError(f"API returned an error: {market_data.error}")

    try:
        rows = market_data.data.rate_curve[spec.api_outer][spec.api_inner]
    except KeyError as exc:
        raise CurveError(f"Unexpected response shape — missing key: {exc}") from exc

    return pd.DataFrame(rows)


def _find_snapshot(curve_id: str) -> DemoCurve:
    """Return the DemoCurve manifest entry for curve_id, or raise CurveError."""
    entry = next((c for c in DEMO_CURVES if c.curve_id == curve_id), None)
    if entry is None:
        raise CurveError(
            f"Curve {curve_id!r} is not available in demo mode. "
            f"Available IDs: {[c.curve_id for c in DEMO_CURVES]}"
        )
    return entry


def _load_snapshot(path: Path, spec: CurveSpec) -> pd.DataFrame:
    """Read a pre-saved JSON snapshot file and return rows for the requested spec."""
    if not path.exists():
        raise CurveError(f"Demo snapshot not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))

    if spec.demo_key not in payload:
        raise CurveError(
            f"Key {spec.demo_key!r} missing in {path.name!r}. "
            "Re-run scripts/download_curves_demo_data.py to regenerate demo snapshots."
        )

    return pd.DataFrame(payload[spec.demo_key])


# ===========================================================================
# Repository implementations
# ===========================================================================


class XMarketRepository:
    """Live Bloomberg MARS XMarket data source."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def fetch(self, query: CurveQuery) -> pd.DataFrame:
        if query.curve_id.upper() in CSA_CURVE_IDS.values():
            raise NotImplementedError(
                f"CSA curve {query.curve_id!r} is not yet wired up."
            )
        spec     = CURVE_SPECS[query.curve_type]
        payload  = _build_api_request(spec, query, self._client.xmarket_session_id)
        response = self._client.send("POST", "/marswebapi/v1/dataDownload", payload)

        if "error" in response:
            raise CurveError(response.get("error_description", str(response["error"])))

        return _extract_rows(response, spec)


class DemoRepository:
    """Offline data source backed by pre-saved JSON snapshots on disk."""

    def __init__(self, snapshots_dir: Path) -> None:
        self._dir = snapshots_dir

    def fetch(self, query: CurveQuery) -> pd.DataFrame:
        spec  = CURVE_SPECS[query.curve_type]
        entry = _find_snapshot(query.curve_id)
        return _load_snapshot(self._dir / entry.filename, spec)


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class XMarketCurveService:
    """
    Thin orchestrator: delegates data fetching to the injected repository and
    applies response enrichment (_enrich_tenors) to every result.

    XMarketCurveService has no knowledge of Bloomberg credentials, filesystem
    paths, or demo mode — all of that lives in the repository implementations.

    Usage via factory (application code)::

        svc = XMarketCurveService.from_settings(market_date)
        df  = svc.get_curve(CurveQuery(curve_id="S329", curve_type=CurveType.RAW, as_of=date.today()))

    Usage with custom repository (tests)::

        svc = XMarketCurveService(repository=MyMockRepository())
    """

    def __init__(self, repository: CurveRepository) -> None:
        self._repo = repository

    def get_curve(self, query: CurveQuery) -> pd.DataFrame:
        """Fetch and normalise the curve described by *query*."""
        return _enrich_tenors(self._repo.fetch(query))

    @classmethod
    def from_settings(cls, market_date: date) -> XMarketCurveService:
        """
        Factory: select the correct repository based on application settings.

        Constructs a DemoRepository when credentials are absent, and an
        XMarketRepository backed by a live MarsClient otherwise.
        """
        if settings.demo_mode:
            return cls(DemoRepository(_SNAPSHOTS_DIR))
        return cls(XMarketRepository(MarsClient(settings, market_date=market_date)))
