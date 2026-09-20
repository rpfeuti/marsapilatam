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

Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from __future__ import annotations

import json
import logging
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
    XCCY_NDSFX_SPECS,
    XCCY_SWAP_SPECS,
    SwapSpec,
)

_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "demo_data" / "swaps"

_PRICING_FIELDS = [
    "MktVal", "DV01", "PV01", "MktPx", "AccruedInterest",
]

# Fallback solve targets used in demo mode or when the API call fails.
# The dealSchema endpoint reports solvableTarget=true fields as "FixedRate",
# "Notional", "Spread", but the solve endpoint uses "Coupon" (alias for
# "FixedRate").  We store the solve-friendly names here and apply the same
# mapping in fetch_solvable_fields.
_DEMO_SOLVABLE: dict[str, list[str]] = {
    "IR.OIS":      ["Coupon", "Spread"],
    "IR.OIS.SOFR": ["Coupon", "Spread"],
    "IR.OIS.RFR":  ["Coupon", "Spread"],
    "IR.NDS":      ["Coupon", "Spread"],
    "IR.NDSFX":    ["Coupon", "Spread"],
}

# Schema field name → solve endpoint name
_SOLVE_NAME_MAP: dict[str, str] = {"FixedRate": "Coupon"}


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass(frozen=True)
class SwapQuery:
    """
    Immutable value object describing a single swap pricing request.

    Frozen + hashable so it can be used directly as an st.cache_data key.
    The key identifies which SwapSpec to look up (e.g. "COP" or "USDCOP").
    swap_type selects the spec dictionary ("OIS", "XCCY" / IR.NDS, or "NDSFX" / IR.NDSFX).
    """

    key:            str
    swap_type:      Literal["OIS", "XCCY", "NDSFX"]
    direction:      Literal["Receive", "Pay"]
    effective_date: date
    maturity_date:  date
    valuation_date: date
    curve_date:     date
    notional:       float
    forward_curve:  str
    discount_curve:      str          = ""
    float_index:         str          = ""
    pay_frequency:       str          = ""
    day_count:           str          = ""
    fixed_rate:          float | None = None   # None = solve for par rate
    spread:              float        = 0.0    # floating leg spread in bp
    solve_for:           str          = "Coupon"
    solve_for_leg:       int          = 1      # NDSFX: 2 = solve FixedRate on local leg (CLP, …)
    leg1_forward_curve:  str          = ""     # XCCY: Leg 1 (base ccy) forward/projection curve
    leg1_discount_curve: str          = ""     # XCCY: Leg 1 (base ccy) discount curve
    leg2_notional:       float        = 0.0    # XCCY: Leg 2 notional in local ccy; 0 = auto
    ndsfx_leg2_fixed_rate: float | None = None  # IR.NDSFX: set to MARS solve double to persist leg-2 FixedRate on save

@dataclass
class SwapResult:
    """Holds the pricing output for a single swap."""

    metrics:     dict[str, str] = field(default_factory=dict)
    par_rate:    float | None   = None
    solve_raw:   float | None   = None  # MARS solveResult.value.doubleVal (before display scaling)
    deal_handle: str | None     = None  # temporary dealHandle — reusable for scenario/stress pricing
    error:       str | None     = None

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
    spread:         float = 0.0,
) -> list[dict[str, Any]]:
    """Build MARS param list for a single swap leg.

    Curve overrides (DiscountCurve, ForwardCurve) are NOT passed here because
    Bloomberg MARS does not expose them in the dealStructureOverride leg schema.
    They are injected via the pricing request instead.
    """

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
    ]

    if pay_frequency:
        params.append(_sel("PayFrequency", pay_frequency))
    if day_count:
        params.append(_sel("DayCount", day_count))
    if fixed_rate is not None:
        params.append(_dbl("FixedRate", fixed_rate))
    if float_index:
        params.append(_str("FloatingIndex", float_index))
    if spread:
        params.append(_dbl("Spread", spread))

    return params


def _specs_for_query(query: SwapQuery) -> dict[str, SwapSpec]:
    """Resolve the spec map for *query* (OIS, XCCY IR.NDS, or IR.NDSFX)."""
    if query.swap_type == "OIS":
        return OIS_SWAP_SPECS
    if query.swap_type == "NDSFX":
        return XCCY_NDSFX_SPECS
    return XCCY_SWAP_SPECS


def _build_ndsfx_structure_body(
    query: SwapQuery,
    spec: SwapSpec,
    session_id: str,
    effective: date,
    maturity: date,
) -> dict[str, Any]:
    """IR.NDSFX: fixed vs fixed (no FloatingIndex on either leg)."""
    if not spec.base_currency:
        raise StructuringError("NDSFX spec must define base_currency.")

    opposite = "Pay" if query.direction == "Receive" else "Receive"
    freq     = query.pay_frequency or spec.pay_frequency
    # Bond conventions (query) apply to USD leg only; local leg uses market spec (e.g. CLP ACT/360).
    leg1_dc = query.day_count or spec.day_count
    leg2_dc = spec.day_count

    leg1_ccy = spec.base_currency
    leg2_ccy = spec.currency

    leg1_fixed = float(query.fixed_rate) if query.fixed_rate is not None else 0.01
    leg2_fixed = (
        float(query.ndsfx_leg2_fixed_rate)
        if query.ndsfx_leg2_fixed_rate is not None
        else 0.01
    )

    leg1_notional = query.notional
    leg2_notional = query.leg2_notional if query.leg2_notional >= 1 else query.notional

    leg1 = _build_leg_params(
        direction=query.direction,
        notional=leg1_notional,
        currency=leg1_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=leg1_fixed,
        float_index=None,
        pay_frequency=freq,
        day_count=leg1_dc,
    )
    leg2 = _build_leg_params(
        direction=opposite,
        notional=leg2_notional,
        currency=leg2_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=leg2_fixed,
        float_index=None,
        pay_frequency=freq,
        day_count=leg2_dc,
        spread=0.0,
    )

    return {
        "sessionId": session_id,
        "tail": spec.deal_type,
        "dealStructureOverride": {
            "param": [],
            "leg": [{"param": leg1}, {"param": leg2}],
        },
    }


def _build_structure_body(
    query:     SwapQuery,
    spec:      SwapSpec,
    session_id: str,
    effective:  date,
    maturity:   date,
) -> dict[str, Any]:
    """Construct the full dealStructureOverride body for the MARS API.

    For XCCY swaps (``spec.base_currency`` is set):
      * Leg 1 = base currency (USD), notional = query.notional
      * Leg 2 = local currency,      notional = query.notional
    For OIS swaps both legs use ``spec.currency`` and ``query.notional``.
    The MARS API handles FX conversion internally for NDS deals.
    """
    if spec.deal_type == "IR.NDSFX":
        return _build_ndsfx_structure_body(query, spec, session_id, effective, maturity)

    opposite = "Pay" if query.direction == "Receive" else "Receive"
    freq     = query.pay_frequency or spec.pay_frequency
    dc       = query.day_count or spec.day_count

    is_xccy  = bool(spec.base_currency)
    leg1_ccy = spec.base_currency if is_xccy else spec.currency
    leg2_ccy = spec.currency

    # XCCY: USD (or base) leg may follow bond conventions; local float leg follows template spec.
    if is_xccy:
        leg1_freq = query.pay_frequency or spec.pay_frequency
        leg1_dc   = query.day_count or spec.day_count
        leg2_freq = spec.pay_frequency
        leg2_dc   = spec.day_count
    else:
        leg1_freq = leg2_freq = freq
        leg1_dc = leg2_dc = dc

    leg1 = _build_leg_params(
        direction=query.direction,
        notional=query.notional,
        currency=leg1_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=query.fixed_rate if query.fixed_rate is not None else 0.0,
        float_index=None,
        pay_frequency=leg1_freq,
        day_count=leg1_dc,
    )
    leg2 = _build_leg_params(
        direction=opposite,
        notional=query.leg2_notional if query.leg2_notional >= 1 else query.notional,
        currency=leg2_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=None,
        float_index=query.float_index or spec.float_index,
        pay_frequency=leg2_freq,
        day_count=leg2_dc,
        spread=query.spread,
    )

    deal_params: list[dict[str, Any]] = []

    return {
        "sessionId": session_id,
        "tail": spec.deal_type,
        "dealStructureOverride": {
            "param": deal_params,
            "leg": [{"param": leg1}, {"param": leg2}],
        },
    }


def _build_pricing_body(
    deal_handle:    str,
    session_id:     str,
    valuation:      date,
    curve_date:     date,
    discount_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Construct the securitiesPricingRequest body.

    *discount_overrides* maps currency codes to Bloomberg curve IDs and injects
    ``interestRateCurveOverrides`` so each leg is discounted with the chosen
    curve.  The projection curve is handled automatically by
    ``useBbgRecommendedSettings`` together with the FloatingIndex in the deal
    structure.
    """
    security: dict[str, Any] = {"identifier": {"dealHandle": deal_handle}, "position": 1}
    if discount_overrides:
        security["marketDataOverrides"] = {
            "interestRateCurveOverrides": [
                {"category": "DISCOUNT_CURVE", "currency": ccy, "overrideCurveId": curve_id}
                for ccy, curve_id in discount_overrides.items()
            ]
        }
    return {
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate":             str(valuation),
                "marketDataDate":            str(curve_date),
                "dealSession":               session_id,
                "requestedField":            _PRICING_FIELDS,
                "useBbgRecommendedSettings": True,
            },
            "security": [security],
        }
    }


def _build_solve_body(
    deal_handle: str,
    session_id:  str,
    valuation:   date,
    curve_date:  date,
    solve_for:   str = "Coupon",
    solve_for_leg: int | None = None,
) -> dict[str, Any]:
    """Construct the solveRequest body to find the target field (NPV = 0).

    Coupon targets Leg 1; Spread targets Leg 2.  *solve_for_leg* overrides when set
    (e.g. NDSFX solves FixedRate on leg 2).
    """
    leg_map = {"Coupon": 1, "Spread": 2}
    leg = solve_for_leg if solve_for_leg is not None else leg_map.get(solve_for, 1)
    return {
        "solveRequest": {
            "identifier":    {"dealHandle": deal_handle},
            "input":         {"name": "Premium", "value": {"doubleVal": 0}},
            "solveFor":      solve_for,
            "solveForLeg":   leg,
            "valuationDate": str(valuation),
            "dealSession":   session_id,
            "marketDataDate": str(curve_date),
        }
    }


def _parse_par_rate(solve_response: dict[str, Any]) -> float | None:
    """Extract the solved value from a solveResponse dict.

    Primary shape: ``solveResult.value.doubleVal``. Some responses omit the outer
    ``solveResult`` wrapper or nest ``value`` differently — try fallbacks.
    """
    if not isinstance(solve_response, dict):
        return None

    def _from_value_obj(v: Any) -> float | None:
        if not isinstance(v, dict):
            return None
        raw = v.get("doubleVal")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    sr = solve_response.get("solveResult")
    if isinstance(sr, dict):
        v = sr.get("value")
        out = _from_value_obj(v)
        if out is not None:
            return out

    v = solve_response.get("value")
    out = _from_value_obj(v)
    if out is not None:
        return out

    # Rare: doubleVal at top level
    raw = solve_response.get("doubleVal")
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass
    return None


# ===========================================================================
# Repository implementations
# ===========================================================================


class SwapLiveRepository:
    """Live Bloomberg MARS swap pricing: structure → price → (optional) solve."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def price(self, query: SwapQuery) -> SwapResult:
        specs = _specs_for_query(query)
        spec  = specs[query.key]

        effective = query.effective_date
        maturity  = query.maturity_date

        # --- Structure ---
        struc_body = _build_structure_body(
            query, spec, self._client.session_id, effective, maturity,
        )
        struc_resp = self._client.send("POST", "/marswebapi/v1/deals/temporary", struc_body)

        if "error" in struc_resp:
            raise StructuringError(
                struc_resp.get("error_description", str(struc_resp["error"]))
            )
        try:
            sr = struc_resp["results"][0]["structureResponse"]
            deal_handle = sr["dealHandle"]
        except (KeyError, IndexError) as exc:
            raise StructuringError(f"Unexpected structure response: {struc_resp}") from exc

        if not deal_handle:
            notifications = sr.get("returnStatus", {}).get("notifications", [])
            errors = [n["message"] for n in notifications if n.get("type") == "S_ERROR"]
            msg = errors[0] if errors else "Unknown structuring failure"
            raise StructuringError(msg)

        # --- Price ---
        discount_overrides: dict[str, str] = {}
        if spec.base_currency and query.leg1_discount_curve:
            discount_overrides[spec.base_currency] = query.leg1_discount_curve
        if query.discount_curve:
            discount_overrides[spec.currency] = query.discount_curve

        price_body = _build_pricing_body(
            deal_handle, self._client.session_id, query.valuation_date, query.curve_date,
            discount_overrides=discount_overrides or None,
        )
        price_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", price_body)

        if "error" in price_resp:
            raise PricingError(
                price_resp.get("error_description", str(price_resp["error"]))
            )

        records = pr.to_records(price_resp)
        metrics = records[0] if records else {}

        # --- Solve for par rate ---
        # XCCY IR.NDS: solve when no fixed_rate (par on float leg).
        # IR.NDSFX: solve local FixedRate (leg 2) when USD leg has YTM (fixed_rate set).
        # XCCY IR.NDS + fixed_rate set + solve_for Spread: par spread on float leg (leg 2) for NPV=0.
        par_rate: float | None = None
        solve_raw: float | None = None
        need_solve = False
        if query.swap_type == "NDSFX":
            need_solve = query.fixed_rate is not None
        elif query.swap_type == "XCCY" and query.fixed_rate is not None and query.solve_for == "Spread":
            need_solve = True
        elif query.fixed_rate is None:
            need_solve = True

        if need_solve:
            solve_body = _build_solve_body(
                deal_handle, self._client.session_id,
                query.valuation_date, query.curve_date,
                solve_for=query.solve_for,
                solve_for_leg=query.solve_for_leg if query.swap_type == "NDSFX" else None,
            )
            solve_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", solve_body)
            if "error" not in solve_resp:
                try:
                    first = solve_resp["results"][0]
                except (KeyError, IndexError):
                    first = {}
                raw = first.get("solveResponse")
                if raw is None and isinstance(first.get("pricingResultResponse"), dict):
                    # Some MARS builds return solve output under pricingResultResponse
                    prr = first["pricingResultResponse"]
                    extra = prr.get("additionalResult") or []
                    for p in extra:
                        if not isinstance(p, dict):
                            continue
                        val = p.get("value")
                        if isinstance(val, dict) and "doubleVal" in val:
                            raw = {"value": val}
                            break
                if raw is not None:
                    par_rate = _parse_par_rate(raw if isinstance(raw, dict) else {})
                    solve_raw = par_rate
                if par_rate is None:
                    logging.getLogger(__name__).warning(
                        "Failed to extract par rate from solve response: %s", solve_resp,
                    )

        return SwapResult(metrics=metrics, par_rate=par_rate, solve_raw=solve_raw, deal_handle=deal_handle)

    def save_deal(self, query: SwapQuery) -> str:
        """Structure a temporary deal, then save it permanently via PATCH.

        1. POST /marswebapi/v1/deals/temporary  → dealHandle
        2. PATCH /marswebapi/v1/deals/temporary/{dealHandle} with saveRequest
        Returns the permanent deal ID.
        """
        specs = _specs_for_query(query)
        spec = specs[query.key]

        struc_body = _build_structure_body(
            query, spec, self._client.session_id,
            query.effective_date, query.maturity_date,
        )
        struc_resp = self._client.send("POST", "/marswebapi/v1/deals/temporary", struc_body)

        if "error" in struc_resp:
            raise StructuringError(struc_resp.get("error_description", str(struc_resp["error"])))
        try:
            deal_handle = struc_resp["results"][0]["structureResponse"]["dealHandle"]
        except (KeyError, IndexError) as exc:
            raise StructuringError(f"Unexpected structure response: {struc_resp}") from exc

        save_resp = self._client.send(
            "PATCH",
            f"/marswebapi/v1/deals/temporary/{deal_handle}",
            {},
        )
        if "error" in save_resp:
            raise StructuringError(save_resp.get("error_description", str(save_resp["error"])))
        try:
            return save_resp["results"][0]["saveResponse"]["dealId"]
        except (KeyError, IndexError):
            return deal_handle


class SwapDemoRepository:
    """Offline swap data source backed by pre-saved JSON snapshots."""

    def __init__(self, snapshots_dir: Path) -> None:
        self._dir = snapshots_dir

    def price(self, query: SwapQuery) -> SwapResult:
        if query.swap_type == "NDSFX":
            filename = f"{query.key}_NDSFX_5Y.json"
        elif (
            query.swap_type == "XCCY"
            and query.solve_for == "Spread"
            and query.fixed_rate is not None
        ):
            filename = f"{query.key}_NDS_SPREAD.json"
        else:
            filename = f"{query.key}_5Y.json"
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
        sr_raw = payload.get("solve_raw")
        solve_raw = float(sr_raw) if sr_raw is not None else par_rate

        return SwapResult(metrics=metrics, par_rate=par_rate, solve_raw=solve_raw)


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

    def __init__(self, repository: SwapRepository, client: MarsClient | None = None) -> None:
        self._repo   = repository
        self._client = client

    def price(self, query: SwapQuery) -> SwapResult:
        """Price the swap described by *query* and return the result."""
        return self._repo.price(query)

    def save_deal(self, query: SwapQuery) -> str:
        """Save the deal permanently on Bloomberg and return the deal ID."""
        if not isinstance(self._repo, SwapLiveRepository):
            raise StructuringError("Save is only available in live mode.")
        return self._repo.save_deal(query)

    def _fetch_deal_structure(self, deal_type: str) -> dict:
        """Call ``GET /marswebapi/v1/dealSchema`` and return the ``dealStructure`` dict."""
        if self._client is None:
            return {}
        resp = self._client.send("GET", "/marswebapi/v1/dealSchema", {"tail": deal_type})
        return resp.get("schemaResponse", {}).get("dealStructure", {})

    def fetch_leg_params(self, deal_type: str) -> list[dict]:
        """Return the full list of leg parameter definitions from the deal schema."""
        try:
            return self._fetch_deal_structure(deal_type).get("leg", [])
        except Exception:
            return []

    def fetch_solvable_fields(self, deal_type: str) -> list[str]:
        """Return the list of solvable-target field names for *deal_type*.

        Calls ``GET /marswebapi/v1/dealSchema`` and collects every parameter
        (deal-level and per-leg) whose ``solvableTarget`` flag is ``true``.
        Schema names are mapped to solve-endpoint names via ``_SOLVE_NAME_MAP``
        (e.g. ``FixedRate`` → ``Coupon``).  ``Notional`` is excluded since
        it is rarely a useful solve target.
        Falls back to ``_DEMO_SOLVABLE`` when running in demo mode or when the
        API call fails.
        """
        if self._client is None:
            return list(_DEMO_SOLVABLE.get(deal_type, ["Coupon"]))
        try:
            structure = self._fetch_deal_structure(deal_type)
            solvable: list[str] = []
            for p in structure.get("param", []):
                if p.get("solvableTarget"):
                    name = _SOLVE_NAME_MAP.get(p["name"], p["name"])
                    if name != "Notional" and name not in solvable:
                        solvable.append(name)
            for leg in structure.get("leg", []):
                for p in leg.get("param", []):
                    if p.get("solvableTarget"):
                        name = _SOLVE_NAME_MAP.get(p["name"], p["name"])
                        if name != "Notional" and name not in solvable:
                            solvable.append(name)
            return solvable or list(_DEMO_SOLVABLE.get(deal_type, ["Coupon"]))
        except Exception:
            return list(_DEMO_SOLVABLE.get(deal_type, ["Coupon"]))

    @classmethod
    def from_settings(cls) -> SwapPricingService:
        """
        Factory: select the correct repository based on application settings.

        Constructs a SwapDemoRepository when credentials are absent, and a
        SwapLiveRepository backed by a live MarsClient otherwise.
        """
        if settings.demo_mode:
            return cls(SwapDemoRepository(_SNAPSHOTS_DIR), client=None)
        client = MarsClient(settings)
        return cls(SwapLiveRepository(client), client=client)
