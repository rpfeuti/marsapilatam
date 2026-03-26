"""
Domain constants and typed configurations for IR swap and XCCY swap pricing.

Separating these from the curve config keeps each domain module focused.
All API-level constants (deal types, float indices, curve IDs) are defined
here so the service layer and Streamlit page can stay free of magic strings.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwapSpec:
    """
    Complete specification for a single swap template.

    Combines MARS API deal parameters with sensible UI pre-fills so that
    selecting a template auto-populates the entire form.
    """

    label:          str    # human-readable name shown in the template selector
    deal_type:      str    # MARS deal type string (e.g. "IR.OIS", "FXFL", "IR.NDS")
    currency:       str    # local currency code (Leg 1 for OIS, Leg 2 for XCCY)
    float_index:    str    # Bloomberg float index ticker (e.g. "COOVIBR")
    notional:       float  # default notional in local currency units
    default_tenor:  str    # default tenor shown in the selector (e.g. "5Y")
    pay_frequency:  str    # MARS pay frequency label (e.g. "Monthly")
    day_count:      str    # day count convention (e.g. "ACT/360")
    discount_curve: str    # Bloomberg curve ID pre-filled for discount curve
    forward_curve:  str    # Bloomberg curve ID pre-filled for forward curve
    csa_ccy:        str    # CSA collateral currency (e.g. "USD")
    coll_curve:     str    # Bloomberg curve ID for collateral / CSA curve


# ---------------------------------------------------------------------------
# OIS Swap templates  (fixed leg vs. floating OIS leg, same currency)
# ---------------------------------------------------------------------------

OIS_SWAP_SPECS: dict[str, SwapSpec] = {
    "COP": SwapSpec(
        label="COP OIS",        deal_type="IR.OIS",
        currency="COP",         float_index="COOVIBR",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="At Maturity", day_count="ACT/360",
        discount_curve="S438",  forward_curve="S329",
        csa_ccy="USD",          coll_curve="S490",
    ),
    "USD": SwapSpec(
        label="USD SOFR",       deal_type="IR.OIS.SOFR",
        currency="USD",         float_index="SOFRRATE",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        discount_curve="S400",  forward_curve="S490",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "BRL": SwapSpec(
        label="BRL FXFL",       deal_type="FXFL",
        currency="BRL",         float_index="BZDIOVRA",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Quarterly", day_count="ACT/360",
        discount_curve="S304",  forward_curve="S89",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "MXN": SwapSpec(
        label="MXN OIS",        deal_type="IR.OIS",
        currency="MXN",         float_index="MXIBTIEF",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Monthly", day_count="ACT/360",
        discount_curve="S428",  forward_curve="S583",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "CLP": SwapSpec(
        label="CLP FXFL",       deal_type="FXFL",
        currency="CLP",         float_index="CLICP",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="SemiAnnual", day_count="ACT/360",
        discount_curve="S423",  forward_curve="S193",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "EUR": SwapSpec(
        label="EUR ESTR",       deal_type="IR.OIS.RFR",
        currency="EUR",         float_index="ESTRON",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        discount_curve="S403",  forward_curve="S514",
        csa_ccy="EUR",          coll_curve="S403",
    ),
}


# ---------------------------------------------------------------------------
# XCCY Swap templates  (USD fixed/floating leg vs. local currency OIS leg)
# ---------------------------------------------------------------------------

XCCY_SWAP_SPECS: dict[str, SwapSpec] = {
    "USDCOP": SwapSpec(
        label="USD/COP NDS",    deal_type="IR.NDS",
        currency="COP",         float_index="COOVIBR",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="At Maturity", day_count="ACT/360",
        discount_curve="S438",  forward_curve="S329",
        csa_ccy="USD",          coll_curve="S490",
    ),
    "USDBRL": SwapSpec(
        label="USD/BRL FXFL",   deal_type="FXFL",
        currency="BRL",         float_index="BZDIOVRA",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Quarterly", day_count="ACT/360",
        discount_curve="S304",  forward_curve="S89",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "USDMXN": SwapSpec(
        label="USD/MXN NDS",    deal_type="IR.NDS",
        currency="MXN",         float_index="MXIBTIEF",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Monthly", day_count="ACT/360",
        discount_curve="S428",  forward_curve="S583",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "USDCLP": SwapSpec(
        label="USD/CLP NDS",    deal_type="IR.NDS",
        currency="CLP",         float_index="CLICP",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="SemiAnnual", day_count="ACT/360",
        discount_curve="S423",  forward_curve="S193",
        csa_ccy="USD",          coll_curve="S400",
    ),
    "USDEUR": SwapSpec(
        label="USD/EUR FXFL",   deal_type="FXFL",
        currency="EUR",         float_index="ESTRON",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        discount_curve="S403",  forward_curve="S514",
        csa_ccy="EUR",          coll_curve="S403",
    ),
}

# Ordered label lists for UI selectboxes
OIS_LABELS:  list[str] = [s.label for s in OIS_SWAP_SPECS.values()]
XCCY_LABELS: list[str] = [s.label for s in XCCY_SWAP_SPECS.values()]

# Reverse lookup: label → key
OIS_BY_LABEL:  dict[str, str] = {s.label: k for k, s in OIS_SWAP_SPECS.items()}
XCCY_BY_LABEL: dict[str, str] = {s.label: k for k, s in XCCY_SWAP_SPECS.items()}

# Available tenor options for the UI
SWAP_TENORS: list[str] = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y"]

# Available pay direction options
SWAP_DIRECTIONS: list[str] = ["Receive", "Pay"]

# Available pay frequency options
SWAP_PAY_FREQUENCIES: list[str] = [
    "At Maturity", "Annual", "SemiAnnual", "Quarterly", "Monthly", "28 Days", "Weekly", "Daily",
]

# Available day count conventions
SWAP_DAY_COUNTS: list[str] = [
    "ACT/360", "ACT/365", "ACT/ACT", "30/360", "BUS/252", "DU/252",
]

# Solve-for options presented in the Valuation Settings column.
# The string must match the MARS API "solveFor" parameter exactly.
SWAP_SOLVE_TARGETS: list[str] = ["Coupon", "Spread"]


# ---------------------------------------------------------------------------
# Demo snapshot manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SwapDemoSnapshot:
    """Metadata for one pre-saved swap pricing result."""

    key:      str   # swap key (e.g. "COP" or "USDCOP")
    swap_type: str  # "OIS" or "XCCY"
    tenor:    str   # "5Y"
    filename: str   # relative filename under demo_data/swaps/


OIS_DEMO_SNAPSHOTS: list[SwapDemoSnapshot] = [
    SwapDemoSnapshot("COP",  "OIS",  "5Y", "COP_5Y.json"),
    SwapDemoSnapshot("USD",  "OIS",  "5Y", "USD_5Y.json"),
    SwapDemoSnapshot("BRL",  "OIS",  "5Y", "BRL_5Y.json"),
    SwapDemoSnapshot("MXN",  "OIS",  "5Y", "MXN_5Y.json"),
    SwapDemoSnapshot("CLP",  "OIS",  "5Y", "CLP_5Y.json"),
    SwapDemoSnapshot("EUR",  "OIS",  "5Y", "EUR_5Y.json"),
]

XCCY_DEMO_SNAPSHOTS: list[SwapDemoSnapshot] = [
    SwapDemoSnapshot("USDCOP", "XCCY", "5Y", "USDCOP_5Y.json"),
    SwapDemoSnapshot("USDBRL", "XCCY", "5Y", "USDBRL_5Y.json"),
    SwapDemoSnapshot("USDMXN", "XCCY", "5Y", "USDMXN_5Y.json"),
    SwapDemoSnapshot("USDCLP", "XCCY", "5Y", "USDCLP_5Y.json"),
    SwapDemoSnapshot("USDEUR", "XCCY", "5Y", "USDEUR_5Y.json"),
]
