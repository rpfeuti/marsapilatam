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
    swap_type distinguishes the spec dictionary to use ("OIS" or "XCCY").
    """

    key:            str
    swap_type:      Literal["OIS", "XCCY"]
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
    leg1_forward_curve:  str          = ""     # XCCY: Leg 1 (base ccy) forward/projection curve
    leg1_discount_curve: str          = ""     # XCCY: Leg 1 (base ccy) discount curve
    leg2_notional:       float        = 0.0    # XCCY: Leg 2 notional in local ccy; 0 = auto


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
    opposite = "Pay" if query.direction == "Receive" else "Receive"
    freq     = query.pay_frequency or spec.pay_frequency
    dc       = query.day_count or spec.day_count

    is_xccy  = bool(spec.base_currency)
    leg1_ccy = spec.base_currency if is_xccy else spec.currency
    leg2_ccy = spec.currency

    leg1 = _build_leg_params(
        direction=query.direction,
        notional=query.notional,
        currency=leg1_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=query.fixed_rate if query.fixed_rate is not None else 0.0,
        float_index=None,
        pay_frequency=freq,
        day_count=dc,
    )
    leg2 = _build_leg_params(
        direction=opposite,
        notional=query.leg2_notional if query.leg2_notional >= 1 else query.notional,
        currency=leg2_ccy,
        effective=effective,
        maturity=maturity,
        fixed_rate=None,
        float_index=query.float_index or spec.float_index,
        pay_frequency=freq,
        day_count=dc,
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
) -> dict[str, Any]:
    """Construct the solveRequest body to find the target field (NPV = 0).

    Coupon targets Leg 1; Spread targets Leg 2.
    """
    leg_map = {"Coupon": 1, "Spread": 2}
    return {
        "solveRequest": {
            "identifier":    {"dealHandle": deal_handle},
            "input":         {"name": "Premium", "value": {"doubleVal": 0}},
            "solveFor":      solve_for,
            "solveForLeg":   leg_map.get(solve_for, 1),
            "valuationDate": str(valuation),
            "dealSession":   session_id,
            "marketDataDate": str(curve_date),
        }
    }


def _parse_par_rate(solve_response: dict[str, Any]) -> float | None:
    """Extract the solved value from a solveResponse dict.

    Bloomberg MARS uses the key "solveResult" (not "solvedValue").
    """
    try:
        val = solve_response["solveResult"]["value"]["doubleVal"]
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

        # --- Solve for par rate (if no fixed rate provided) ---
        par_rate: float | None = None
        if query.fixed_rate is None:
            solve_body = _build_solve_body(
                deal_handle, self._client.session_id,
                query.valuation_date, query.curve_date,
                solve_for=query.solve_for,
            )
            solve_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", solve_body)
            if "error" not in solve_resp:
                try:
                    raw = solve_resp["results"][0]["solveResponse"]
                    par_rate = _parse_par_rate(raw)
                except (KeyError, IndexError):
                    logging.getLogger(__name__).warning(
                        "Failed to extract par rate from solve response: %s", solve_resp,
                    )

        return SwapResult(metrics=metrics, par_rate=par_rate)

    def save_deal(self, query: SwapQuery) -> str:
        """Structure a temporary deal, then save it permanently via PATCH.

        1. POST /marswebapi/v1/deals/temporary  → dealHandle
        2. PATCH /marswebapi/v1/deals/temporary/{dealHandle} with saveRequest
        Returns the permanent deal ID.
        """
        specs = OIS_SWAP_SPECS if query.swap_type == "OIS" else XCCY_SWAP_SPECS
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
