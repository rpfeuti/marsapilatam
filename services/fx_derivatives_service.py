"""
FX Derivatives pricing service — Repository pattern.

Architecture:
    DerivativeQuery         — immutable value object describing a single pricing request
    DerivativeResult        — dataclass holding pricing metrics (greeks, premium, etc.)
    DerivativeRepository    — structural Protocol (interface)
    DerivativeLiveRepository — live Bloomberg MARS implementation (structure + price, no solve)
    DerivativeDemoRepository — offline repository loading JSON snapshots from demo_data/
    DerivativePricingService — thin orchestrator with from_settings() factory

Supports four MARS deal types:
    FX.VA  — Vanilla options  (deal-level params, no legs)
    FX.RR  — Risk Reversals   (2-leg structure)
    FX.KI  — Knock-In barriers (deal-level params + barrier fields)
    FX.KO  — Knock-Out barriers (deal-level params + barrier fields)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Protocol

from bloomberg import pricing_result as pr
from bloomberg.exceptions import PricingError, StructuringError
from bloomberg.webapi import MarsClient
from configs.derivatives_config import (
    FX_KI_SPECS,
    FX_KO_SPECS,
    FX_RR_SPECS,
    FX_VANILLA_SPECS,
    FxDerivativeSpec,
)
from configs.settings import settings

log = logging.getLogger(__name__)

_FX_PRICING_FIELDS = [
    "MktVal", "MktPx", "Premium",
    "Delta", "Gamma", "Vega", "Theta", "Rho",
    "Vol", "DV01", "Vanna", "Volga", "Phi",
]

_SPECS_BY_PRODUCT: dict[str, dict[str, FxDerivativeSpec]] = {
    "FX_VANILLA": FX_VANILLA_SPECS,
    "FX_RR":      FX_RR_SPECS,
    "FX_KI":      FX_KI_SPECS,
    "FX_KO":      FX_KO_SPECS,
}


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass(frozen=True)
class DerivativeQuery:
    """Immutable value object describing a single FX derivative pricing request."""

    key:            str
    product_type:   str          # "FX_VANILLA", "FX_RR", "FX_KI", "FX_KO"
    direction:      str          # "Buy" or "Sell"
    call_put:       str          # "Call" or "Put"  (Leg 1 for RR)
    notional:       float
    strike:         float
    expiry_date:    date
    valuation_date: date
    curve_date:     date
    exercise_type:  str = "European"
    # Risk Reversal — Leg 2
    leg2_call_put:  str   = ""
    leg2_strike:    float = 0.0
    leg2_direction: str   = ""
    # Barrier options
    barrier_direction: str   = ""
    barrier_level:     float = 0.0
    barrier_type:      str   = "American"


@dataclass
class DerivativeResult:
    """Holds the pricing output for a single FX derivative."""

    metrics: dict[str, str] = field(default_factory=dict)
    error:   str | None     = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ===========================================================================
# Repository Protocol
# ===========================================================================


class DerivativeRepository(Protocol):
    """Structural interface for derivative data sources."""

    def price(self, query: DerivativeQuery) -> DerivativeResult: ...


# ===========================================================================
# Pure helper functions — build MARS request bodies
# ===========================================================================


def _str(n: str, v: str) -> dict:
    return {"name": n, "value": {"stringVal": v}}


def _dbl(n: str, v: float) -> dict:
    return {"name": n, "value": {"doubleVal": v}}


def _sel(n: str, v: str) -> dict:
    return {"name": n, "value": {"selectionVal": {"value": v}}}


def _dat(n: str, v: str) -> dict:
    return {"name": n, "value": {"dateVal": v}}


def _build_vanilla_body(
    query: DerivativeQuery,
    spec: FxDerivativeSpec,
    session_id: str,
) -> dict[str, Any]:
    params: list[dict[str, Any]] = [
        _str("UnderlyingTicker", spec.underlying_ticker),
        _sel("Direction",       query.direction),
        _sel("CallPut",         query.call_put),
        _dbl("Notional",        query.notional),
        _str("NotionalCurrency", spec.notional_currency),
        _dbl("Strike",          query.strike),
        _dat("ExpiryDate",      str(query.expiry_date)),
        _sel("ExerciseType",    query.exercise_type),
    ]
    return {
        "sessionId": session_id,
        "tail": "FX.VA",
        "dealStructureOverride": {"param": params},
    }


def _build_rr_body(
    query: DerivativeQuery,
    spec: FxDerivativeSpec,
    session_id: str,
) -> dict[str, Any]:
    """Build structure body for a Risk Reversal (2 legs)."""
    common = [
        _str("UnderlyingTicker",  spec.underlying_ticker),
        _dbl("Notional",         query.notional),
        _str("NotionalCurrency", spec.notional_currency),
        _dat("ExpiryDate",       str(query.expiry_date)),
        _sel("ExerciseType",     query.exercise_type),
    ]
    leg1 = common + [
        _sel("Direction", query.direction),
        _sel("CallPut",   query.call_put),
        _dbl("Strike",    query.strike),
    ]
    leg2 = common + [
        _sel("Direction", query.leg2_direction or ("Sell" if query.direction == "Buy" else "Buy")),
        _sel("CallPut",   query.leg2_call_put or ("Put" if query.call_put == "Call" else "Call")),
        _dbl("Strike",    query.leg2_strike),
    ]
    return {
        "sessionId": session_id,
        "tail": "FX.RR",
        "dealStructureOverride": {
            "param": [],
            "leg": [{"param": leg1}, {"param": leg2}],
        },
    }


def _build_barrier_body(
    query: DerivativeQuery,
    spec: FxDerivativeSpec,
    session_id: str,
) -> dict[str, Any]:
    """Build structure body for a Knock-In or Knock-Out barrier option."""
    deal_type = "FX.KI" if query.product_type == "FX_KI" else "FX.KO"

    params: list[dict[str, Any]] = [
        _str("UnderlyingTicker",  spec.underlying_ticker),
        _sel("Direction",        query.direction),
        _sel("CallPut",          query.call_put),
        _dbl("Notional",         query.notional),
        _str("NotionalCurrency", spec.notional_currency),
        _dbl("Strike",           query.strike),
        _dat("ExpiryDate",       str(query.expiry_date)),
        _sel("BarrierDirection", query.barrier_direction),
        _sel("BarrierType",      query.barrier_type),
    ]

    if "Up" in query.barrier_direction:
        params.append(_dbl("BarrierUpperLevel", query.barrier_level))
    else:
        params.append(_dbl("BarrierLowerLevel", query.barrier_level))

    return {
        "sessionId": session_id,
        "tail": deal_type,
        "dealStructureOverride": {"param": params},
    }


def _build_structure_body(
    query: DerivativeQuery,
    spec: FxDerivativeSpec,
    session_id: str,
) -> dict[str, Any]:
    """Dispatch to the correct builder based on product type."""
    if query.product_type == "FX_VANILLA":
        return _build_vanilla_body(query, spec, session_id)
    if query.product_type == "FX_RR":
        return _build_rr_body(query, spec, session_id)
    return _build_barrier_body(query, spec, session_id)


def _build_pricing_body(
    deal_handle: str,
    session_id:  str,
    valuation:   date,
    curve_date:  date,
) -> dict[str, Any]:
    return {
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate":             str(valuation),
                "marketDataDate":            str(curve_date),
                "dealSession":               session_id,
                "requestedField":            _FX_PRICING_FIELDS,
                "useBbgRecommendedSettings": True,
            },
            "security": [
                {"identifier": {"dealHandle": deal_handle}, "position": 1},
            ],
        }
    }


# ===========================================================================
# Repository implementations
# ===========================================================================


class DerivativeLiveRepository:
    """Live Bloomberg MARS derivative pricing: structure → price (no solve)."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def price(self, query: DerivativeQuery) -> DerivativeResult:
        specs = _SPECS_BY_PRODUCT.get(query.product_type, FX_VANILLA_SPECS)
        spec  = specs[query.key]

        # --- Structure ---
        struc_body = _build_structure_body(query, spec, self._client.session_id)
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
        price_body = _build_pricing_body(
            deal_handle, self._client.session_id,
            query.valuation_date, query.curve_date,
        )
        price_resp = self._client.send("POST", "/marswebapi/v1/securitiesPricing", price_body)

        if "error" in price_resp:
            raise PricingError(
                price_resp.get("error_description", str(price_resp["error"]))
            )

        records = pr.to_records(price_resp)
        metrics = records[0] if records else {}
        return DerivativeResult(metrics=metrics)


class DerivativeDemoRepository:
    """Offline repository — loads pre-saved JSON snapshots from demo_data/fx_derivatives/."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def price(self, query: DerivativeQuery) -> DerivativeResult:
        filename = f"{query.product_type}_{query.key}.json"
        path = self._data_dir / filename
        if not path.exists():
            return DerivativeResult(
                error=f"Demo snapshot not found: {filename}. "
                      "Run scripts/download_fx_deriv_demo_data.py to generate it."
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return DerivativeResult(metrics=payload["metrics"])
        except Exception as exc:
            log.warning("Failed to load demo snapshot %s: %s", filename, exc)
            return DerivativeResult(error=f"Failed to load demo snapshot: {exc}")


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class DerivativePricingService:
    """
    Thin orchestrator: delegates FX derivative pricing to the injected repository.

    Usage::

        svc    = DerivativePricingService.from_settings()
        result = svc.price(DerivativeQuery(key="EURUSD", product_type="FX_VANILLA", ...))
    """

    def __init__(self, repository: DerivativeRepository, client: MarsClient | None = None) -> None:
        self._repo   = repository
        self._client = client

    def price(self, query: DerivativeQuery) -> DerivativeResult:
        return self._repo.price(query)

    @classmethod
    def from_settings(cls) -> DerivativePricingService:
        if settings.demo_mode:
            data_dir = Path(__file__).resolve().parent.parent / "demo_data" / "fx_derivatives"
            return cls(DerivativeDemoRepository(data_dir), client=None)
        client = MarsClient(settings)
        return cls(DerivativeLiveRepository(client), client=client)
