"""
Domain constants and typed configurations for FX derivative pricing.

Covers four MARS deal types:
  FX.VA  — Vanilla options
  FX.RR  — Risk Reversals (collars)
  FX.KI  — Knock-In barrier options
  FX.KO  — Knock-Out barrier options

All parameter names are verified against GET /marswebapi/v1/dealSchema.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FxDerivativeSpec:
    """
    Complete specification for a single FX derivative template.

    Combines MARS API deal parameters with sensible UI pre-fills so that
    selecting a currency pair auto-populates the form.
    """

    label:              str
    deal_type:          str    # MARS deal type ("FX.VA", "FX.RR", "FX.KI", "FX.KO")
    underlying_ticker:  str    # MARS FX pair code (e.g. "EURUSD")
    base_currency:      str    # foreign / base currency
    quote_currency:     str    # domestic / quote currency
    notional:           float
    notional_currency:  str
    default_tenor:      str    # default expiry tenor (e.g. "3M")


# ---------------------------------------------------------------------------
# Currency pair definitions (shared across all deal types)
# ---------------------------------------------------------------------------

_N = 1_000_000

_FX_PAIRS: dict[str, dict] = {
    "EURUSD": {"ticker": "EURUSD", "base": "EUR", "quote": "USD", "notional": _N, "nccy": "EUR"},
    "USDCOP": {"ticker": "USDCOP", "base": "USD", "quote": "COP", "notional": _N, "nccy": "USD"},
    "USDMXN": {"ticker": "USDMXN", "base": "USD", "quote": "MXN", "notional": _N, "nccy": "USD"},
    "USDPEN": {"ticker": "USDPEN", "base": "USD", "quote": "PEN", "notional": _N, "nccy": "USD"},
    "USDBRL": {"ticker": "USDBRL", "base": "USD", "quote": "BRL", "notional": _N, "nccy": "USD"},
    "USDCLP": {"ticker": "USDCLP", "base": "USD", "quote": "CLP", "notional": _N, "nccy": "USD"},
}


def _make_specs(deal_type: str, label_suffix: str) -> dict[str, FxDerivativeSpec]:
    """Generate FxDerivativeSpec entries for every currency pair."""
    return {
        key: FxDerivativeSpec(
            label=f"{p['base']}/{p['quote']} {label_suffix}",
            deal_type=deal_type,
            underlying_ticker=p["ticker"],
            base_currency=p["base"],
            quote_currency=p["quote"],
            notional=p["notional"],
            notional_currency=p["nccy"],
            default_tenor="3M",
        )
        for key, p in _FX_PAIRS.items()
    }


# ---------------------------------------------------------------------------
# Template dictionaries — one per MARS deal type
# ---------------------------------------------------------------------------

FX_VANILLA_SPECS: dict[str, FxDerivativeSpec] = _make_specs("FX.VA", "Vanilla")
FX_RR_SPECS:      dict[str, FxDerivativeSpec] = _make_specs("FX.RR", "Risk Reversal")
FX_KI_SPECS:      dict[str, FxDerivativeSpec] = _make_specs("FX.KI", "Knock-In")
FX_KO_SPECS:      dict[str, FxDerivativeSpec] = _make_specs("FX.KO", "Knock-Out")

# Ordered label lists for UI selectboxes
FX_VANILLA_LABELS: list[str] = [s.label for s in FX_VANILLA_SPECS.values()]
FX_RR_LABELS:      list[str] = [s.label for s in FX_RR_SPECS.values()]
FX_KI_LABELS:      list[str] = [s.label for s in FX_KI_SPECS.values()]
FX_KO_LABELS:      list[str] = [s.label for s in FX_KO_SPECS.values()]

# Reverse lookup: label → key
FX_VANILLA_BY_LABEL: dict[str, str] = {s.label: k for k, s in FX_VANILLA_SPECS.items()}
FX_RR_BY_LABEL:      dict[str, str] = {s.label: k for k, s in FX_RR_SPECS.items()}
FX_KI_BY_LABEL:      dict[str, str] = {s.label: k for k, s in FX_KI_SPECS.items()}
FX_KO_BY_LABEL:      dict[str, str] = {s.label: k for k, s in FX_KO_SPECS.items()}

# ---------------------------------------------------------------------------
# UI constants — verified against dealSchema SELECTION_VAL allowed values
# ---------------------------------------------------------------------------

FX_DIRECTIONS:       list[str] = ["Buy", "Sell"]
FX_CALL_PUT:         list[str] = ["Call", "Put"]
FX_EXERCISE_TYPES:   list[str] = ["European", "American"]
FX_BARRIER_DIRS_KI:  list[str] = ["Down & In", "Up & In"]
FX_BARRIER_DIRS_KO:  list[str] = ["Down & Out", "Up & Out"]
FX_BARRIER_TYPES:    list[str] = ["American", "European"]
