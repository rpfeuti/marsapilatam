"""
IR Swap and XCCY Swap pricing service — Repository pattern.

Architecture:
    SwapQuery           — immutable value object describing a single swap pricing request
    SwapResult          — dataclass holding pricing metrics and solved par rate
    SwapRepository      — structural Protocol (interface) for any data source
    SwapLiveRepository  — live Bloomberg MARS implementation (structure + price + solve)
    SwapDemoRepository  — offline, pre-saved JSON snapshot implementation
    SwapPricingService  — thin orchestrator with from_settings() factory

The service has no knowledge of Bloomberg credentials or filesystem paths;
those belong entirely in the repository implementations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal, Protocol

from bloomberg import pricing_result as pr
from bloomberg.exceptions import PricingError, StructuringError
from bloomberg.webapi import MarsClient
from configs.settings import settings
from configs.swaps_config import (
    OIS_SWAP_SPECS,
    XCCY_SWAP_SPECS,
    SwapSpec,
)

_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "demo_data" / "swaps"

_PRICING_FIELDS = [
    "MktVal", "DV01", "PV01", "MktPx", "AccruedInterest", "BpValue",
]

_TENOR_YEARS: dict[str, int] = {
    "1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5, "7Y": 7, "10Y": 10,
}


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass(frozen=True)
class SwapQuery:
    """
    Immutable value object describing a single swap pricing request.

    Frozen + hashable so it can be used directly as an st.cache_data key.
    The key identifies which SwapSpec to look up (e.g. "COP" or "USDCOP").
    swap_type distinguishes the spec dictionary to use ("OIS" or "XCCY").
    """

    key:            str
    swap_type:      Literal["OIS", "XCCY"]
    direction:      Literal["Receive", "Pay"]
    tenor:          str
    valuation_date: date
    curve_date:     date
    notional:       float
    discount_curve: str
    forward_curve:  str
    csa_ccy:        str
    coll_curve:     str
    float_index:    str    = ""
    pay_frequency:  str    = ""
    day_count:      str    = ""
    fixed_rate:     float | None = None  # None = solve for par rate


@dataclass
class SwapResult:
    """Holds the pricing output for a single swap."""

    metrics:  dict[str, str] = field(default_factory=dict)
    par_rate: float | None   = None
    error:    str | None     = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ===========================================================================
# Repository Protocol
# ===========================================================================


class SwapRepository(Protocol):
    """Structural interface for swap data sources."""

    def price(self, query: SwapQuery) -> SwapResult: ...


# ===========================================================================
# Pure helper functions
# ===========================================================================


def _maturity_from_tenor(effective: date, tenor: str) -> date:
    """Compute the maturity date from an effective date and a tenor string."""
    years = _TENOR_YEARS.get(tenor, 5)
    return date(effective.year + years, effective.month, effective.day)


def _build_leg_params(
    direction:      str,
    notional:       float,
    currency:       str,
    effective:      date,
    maturity:       date,
    fixed_rate:     float | None,
    float_index:    str | None,
    pay_frequency:  str,
    day_count:      str,
    discount_curve: str,
    forward_curve:  str,
) -> list[dict[str, Any]]:
    """Build MARS param list for a single swap leg."""

    def _str(n: str, v: str) -> dict:
        return {"name": n, "value": {"stringVal": v}}

    def _dbl(n: str, v: float) -> dict:
        return {"name": n, "value": {"doubleVal": v}}

    def _sel(n: str, v: str) -> dict:
        return {"name": n, "value": {"selectionVal": {"value": v}}}

    def _dat(n: str, v: str) -> dict:
        return {"name": n, "value": {"dateVal": v}}

    params: list[dict[str, Any]] = [
        _sel("Direction",    direction),
        _dbl("Notional",     notional),
        _str("Currency",     currency),
        _dat("EffectiveDate", str(effective)),
        _dat("MaturityDate",  str(maturity)),
        _sel("PayFrequency", pay_frequency),
        _sel("DayCount",     day_count),
    ]

    if fixed_rate is not None:
        params.append(_dbl("FixedRate", fixed_rate))
    if float_index:
        params.append(_str("FloatingIndex", float_index))
    if discount_curve:
        params.append(_str("DiscountCurve", discount_curve))
    if forward_curve:
        params.append(_str("ForwardCurve", forward_curve))

    return params


def _build_structure_body(
    query:     SwapQuery,
    spec:      SwapSpec,
    session_id: str,
    effective:  date,
    maturity:   date,
) -> dict[str, Any]:
    """Construct the full structureRequest body for the MARS API."""
    opposite = "Pay" if query.direction == "Receive" else "Receive"

    leg1 = _build_leg_params(
        direction=query.direction,
        notional=query.notional,
        currency=spec.currency,
        effective=effective,
        maturity=maturity,
        fixed_rate=query.fixed_rate if query.fixed_rate is not None else 0.0,
        float_index=None,
        pay_frequency=query.pay_frequency or spec.pay_frequency,
        day_count=query.day_count or spec.day_count,
        discount_curve=query.discount_curve,
        forward_curve="",
    )
    leg2 = _build_leg_params(
        direction=opposite,
        notional=query.notional,
        currency=spec.currency,
        effective=effective,
        maturity=maturity,
        fixed_rate=None,
        float_index=query.float_index or spec.float_index,
        pay_frequency=query.pay_frequency or spec.pay_frequency,
        day_count=query.day_count or spec.day_count,
        discount_curve=query.discount_curve,
        forward_curve=query.forward_curve,
    )

    deal_params: list[dict[str, Any]] = [
        {"name": "CSACollateralCurrency", "value": {"stringVal": query.csa_ccy}},
    ]

    return {
        "sessionId": session_id,
        "tail": spec.deal_type,
        "dealStructureOverride": {
            "param": deal_params,
            "leg": [{"param": leg1}, {"param": leg2}],
        },
    }


def _build_pricing_body(
    deal_handle: str,
    session_id:  str,
    valuation:   date,
    curve_date:  date,
) -> dict[str, Any]:
    """Construct the securitiesPricingRequest body."""
    return {
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate":            str(valuation),
                "marketDataDate":           str(curve_date),
                "dealSession":              session_id,
                "requestedField":           _PRICING_FIELDS,
                "useBbgRecommendedSettings": True,
            },
            "security": [
                {"identifier": {"dealHandle": deal_handle}, "position": 1}
            ],
        }
    }


def _build_solve_body(
    deal_handle: str,
    session_id:  str,
    valuation:   date,
    curve_date:  date,
) -> dict[str, Any]:
    """Construct the solveRequest body to find the par coupon (NPV = 0)."""
    return {
        "solveRequest": {
            "identifier":    {"dealHandle": deal_handle},
            "input":         {"name": "Premium", "value": {"doubleVal": 0}},
            "solveFor":      "Coupon",
            "solveForLeg":   1,
            "valuationDate": str(valuation),
            "dealSession":   session_id,
            "marketDataDate": str(curve_date),
        }
    }


def _parse_par_rate(solve_response: dict[str, Any]) -> float | None:
    """Extract the solved coupon value from a solveResponse dict."""
    try:
        val = solve_response["solvedValue"]["doubleVal"]
        return float(val)
    except (KeyError, TypeError, ValueError):
        return None


# ===========================================================================
# Repository implementations
# ===========================================================================


class SwapLiveRepository:
    """Live Bloomberg MARS swap pricing: structure → price → (optional) solve."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def price(self, query: SwapQuery) -> SwapResult:
        specs = OIS_SWAP_SPECS if query.swap_type == "OIS" else XCCY_SWAP_SPECS
        spec  = specs[query.key]

        effective = query.valuation_date
        maturity  = _maturity_from_tenor(effective, query.tenor)

        # --- Structure ---
        struc_body = _build_structure_body(
            query, spec, self._client.session_id, effective, maturity
        )
        struc_resp = self._client.send("POST", "/marswebapi/v1/deals/temporary", struc_body)

        if "error" in struc_resp:
            raise StructuringError(
                struc_resp.get("error_description", str(struc_resp["error"]))
            )
        try:
            deal_handle = struc_resp["results"][0]["structureResponse"]["dealHandle"]
        except (KeyError, IndexError) as exc:
            raise StructuringError(f"Unexpected structure response: {struc_resp}") from exc

        # --- Price ---
        price_body = _build_pricing_body(
            deal_handle, self._client.session_id, query.valuation_date, query.curve_date
        )
        price_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", price_body)

        if "error" in price_resp:
            raise PricingError(
                price_resp.get("error_description", str(price_resp["error"]))
            )

        records = pr.to_records(price_resp)
        metrics = records[0] if records else {}

        # --- Solve for par rate (if no fixed rate provided) ---
        par_rate: float | None = None
        if query.fixed_rate is None:
            solve_body = _build_solve_body(
                deal_handle, self._client.session_id, query.valuation_date, query.curve_date
            )
            solve_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", solve_body)
            if "error" not in solve_resp:
                try:
                    raw = solve_resp["results"][0]["solveResponse"]
                    par_rate = _parse_par_rate(raw)
                except (KeyError, IndexError):
                    pass

        return SwapResult(metrics=metrics, par_rate=par_rate)


class SwapDemoRepository:
    """Offline swap data source backed by pre-saved JSON snapshots."""

    def __init__(self, snapshots_dir: Path) -> None:
        self._dir = snapshots_dir

    def price(self, query: SwapQuery) -> SwapResult:
        filename = f"{query.key}_{query.tenor}.json"
        path     = self._dir / filename

        if not path.exists():
            return SwapResult(
                error=f"Demo snapshot not found: {filename}. "
                      "Re-run scripts/download_swap_demo_data.py to regenerate."
            )

        payload  = json.loads(path.read_text(encoding="utf-8"))
        metrics  = payload.get("metrics", {})
        par_rate_raw = payload.get("par_rate")
        par_rate = float(par_rate_raw) if par_rate_raw is not None else None

        return SwapResult(metrics=metrics, par_rate=par_rate)


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class SwapPricingService:
    """
    Thin orchestrator: delegates swap pricing to the injected repository.

    SwapPricingService has no knowledge of Bloomberg credentials or filesystem
    paths — those belong in the repository implementations.

    Usage via factory (application code)::

        svc    = SwapPricingService.from_settings()
        result = svc.price(SwapQuery(key="COP", swap_type="OIS", ...))

    Usage with a custom repository (tests)::

        svc = SwapPricingService(repository=MyMockRepository())
    """

    def __init__(self, repository: SwapRepository) -> None:
        self._repo = repository

    def price(self, query: SwapQuery) -> SwapResult:
        """Price the swap described by *query* and return the result."""
        return self._repo.price(query)

    @classmethod
    def from_settings(cls) -> SwapPricingService:
        """
        Factory: select the correct repository based on application settings.

        Constructs a SwapDemoRepository when credentials are absent, and a
        SwapLiveRepository backed by a live MarsClient otherwise.
        """
        if settings.demo_mode:
            return cls(SwapDemoRepository(_SNAPSHOTS_DIR))
        return cls(SwapLiveRepository(MarsClient(settings)))
