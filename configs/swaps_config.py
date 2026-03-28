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

    For XCCY swaps ``base_currency`` holds the funding-leg currency (typically
    ``"USD"``).  When non-empty the service layer builds Leg 1 in
    ``base_currency`` and Leg 2 in ``currency``, and fetches the FX spot rate
    to convert the notional.
    """

    label:          str    # human-readable name shown in the template selector
    deal_type:      str    # MARS deal type string (e.g. "IR.OIS", "IR.NDS")
    currency:       str    # local currency code (both legs for OIS; Leg 2 for XCCY)
    float_index:    str    # Bloomberg float index ticker (e.g. "COOVIBR")
    notional:       float  # default notional (USD for XCCY, local for OIS)
    default_tenor:  str    # default tenor shown in the selector (e.g. "5Y")
    pay_frequency:  str    # MARS pay frequency label; "" = let API default
    day_count:      str    # day count convention; "" = let API default
    forward_curve:  str    # Bloomberg curve ID for the projection (floating) curve
    discount_curve: str    # Bloomberg curve ID for the discount curve
    base_currency:       str   = ""   # funding-leg currency for XCCY (empty for OIS)
    fx_ticker:           str   = ""   # Bloomberg FX ticker for spot rate (empty for OIS)
    leg1_forward_curve:  str   = ""   # XCCY Leg 1 (base ccy) projection curve
    leg1_discount_curve: str   = ""   # XCCY Leg 1 (base ccy) discount curve
    leg2_notional:       float = 0.0  # XCCY Leg 2 notional in local ccy; 0 = auto via API


# ---------------------------------------------------------------------------
# OIS Swap templates  (fixed leg vs. floating OIS leg, same currency)
# ---------------------------------------------------------------------------

OIS_SWAP_SPECS: dict[str, SwapSpec] = {
    "COP": SwapSpec(
        label="COP OIS",        deal_type="IR.OIS",
        currency="COP",         float_index="COOVIBR",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="At Maturity", day_count="ACT/360",
        forward_curve="S329",   discount_curve="S329",
    ),
    "USD": SwapSpec(
        label="USD SOFR",       deal_type="IR.OIS.SOFR",
        currency="USD",         float_index="SOFRRATE",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        forward_curve="S490",   discount_curve="S490",
    ),
    "BRL": SwapSpec(
        label="BRL CDI",        deal_type="IR.OIS",
        currency="BRL",         float_index="BZDIOVRA",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="At Maturity", day_count="",
        forward_curve="S89",    discount_curve="S89",
    ),
    "MXN": SwapSpec(
        label="MXN OIS",        deal_type="IR.OIS",
        currency="MXN",         float_index="MXIBTIEF",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Monthly", day_count="ACT/360",
        forward_curve="S583",   discount_curve="S583",
    ),
    "CLP": SwapSpec(
        label="CLP OIS",        deal_type="IR.OIS",
        currency="CLP",         float_index="CLICP",
        notional=10_000_000_000, default_tenor="5Y",
        pay_frequency="SemiAnnual", day_count="ACT/360",
        forward_curve="S193",   discount_curve="S193",
    ),
    "EUR": SwapSpec(
        label="EUR ESTR",       deal_type="IR.OIS.RFR",
        currency="EUR",         float_index="ESTRON",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        forward_curve="S514",   discount_curve="S514",
    ),
}


# ---------------------------------------------------------------------------
# XCCY Swap templates  (USD fixed/floating leg vs. local currency OIS leg)
# ---------------------------------------------------------------------------

XCCY_SWAP_SPECS: dict[str, SwapSpec] = {
    "USDCOP": SwapSpec(
        label="USD/COP NDS",    deal_type="IR.NDS",
        currency="COP",         float_index="COOVIBR",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        forward_curve="S329",   discount_curve="S329",
        base_currency="USD",    fx_ticker="USDCOP",
        leg1_forward_curve="S490", leg1_discount_curve="S490",
    ),
    "USDBRL": SwapSpec(
        label="USD/BRL NDS",    deal_type="IR.NDS",
        currency="BRL",         float_index="BZDIOVRA",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="At Maturity", day_count="",
        forward_curve="S89",    discount_curve="S89",
        base_currency="USD",    fx_ticker="USDBRL",
        leg1_forward_curve="S490", leg1_discount_curve="S490",
    ),
    "USDMXN": SwapSpec(
        label="USD/MXN NDS",    deal_type="IR.NDS",
        currency="MXN",         float_index="MXIBTIEF",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Monthly", day_count="ACT/360",
        forward_curve="S583",   discount_curve="S583",
        base_currency="USD",    fx_ticker="USDMXN",
        leg1_forward_curve="S490", leg1_discount_curve="S490",
    ),
    "USDCLP": SwapSpec(
        label="USD/CLP NDS",    deal_type="IR.NDS",
        currency="CLP",         float_index="CLICP",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="SemiAnnual", day_count="ACT/360",
        forward_curve="S193",   discount_curve="S193",
        base_currency="USD",    fx_ticker="USDCLP",
        leg1_forward_curve="S490", leg1_discount_curve="S490",
    ),
    "USDEUR": SwapSpec(
        label="USD/EUR NDS",    deal_type="IR.NDS",
        currency="EUR",         float_index="ESTRON",
        notional=10_000_000,    default_tenor="5Y",
        pay_frequency="Annual", day_count="ACT/360",
        forward_curve="S514",   discount_curve="S514",
        base_currency="USD",    fx_ticker="USDEUR",
        leg1_forward_curve="S490", leg1_discount_curve="S490",
    ),
}

# Ordered label lists for UI selectboxes
OIS_LABELS:  list[str] = [s.label for s in OIS_SWAP_SPECS.values()]
XCCY_LABELS: list[str] = [s.label for s in XCCY_SWAP_SPECS.values()]

# Reverse lookup: label → key
OIS_BY_LABEL:  dict[str, str] = {s.label: k for k, s in OIS_SWAP_SPECS.items()}
XCCY_BY_LABEL: dict[str, str] = {s.label: k for k, s in XCCY_SWAP_SPECS.items()}

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
