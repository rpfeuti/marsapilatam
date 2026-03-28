"""
Domain constants and typed configurations for the Bloomberg MARS XMarket curve integration.

Separating these from credentials config (settings.py) keeps this module importable
without triggering .env loading, and groups all curve-domain knowledge in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

# ---------------------------------------------------------------------------
# Curve type enum
# ---------------------------------------------------------------------------


class CurveType(StrEnum):
    """The three curve representations available via the MARS XMarket API."""

    RAW      = "Raw Curve"
    ZERO     = "Zero Coupon"
    DISCOUNT = "Discount Factor"


# ---------------------------------------------------------------------------
# Curve specification dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurveSpec:
    """
    Complete specification for a single curve type.

    Centralises all per-type knowledge that was previously scattered across
    magic-index tuple lookups, string comparisons, and display scaling.
    """

    date_col:  str    # column name for the date / maturity in the API response
    value_col: str    # column name for the rate / factor in the API response
    api_outer: str    # outer key in the API response  ("rawCurve" / "interpolatedCurve")
    api_inner: str    # inner key in the API response  ("parRate" / "zeroRate" / "discountFactor")
    demo_key:  str    # key in the demo JSON snapshot  ("raw" / "zero" / "discount")
    scale:     float  # display multiplier (100 for rates → %; 1 for discount factors)
    fmt:       str    # printf format string for the table value column
    y_label:   str    # y-axis / column label used in charts and table headers


CURVE_SPECS: dict[CurveType, CurveSpec] = {
    CurveType.RAW: CurveSpec(
        date_col="maturityDate",
        value_col="rate",
        api_outer="rawCurve",
        api_inner="parRate",
        demo_key="raw",
        scale=100.0,
        fmt=".4f",
        y_label="Rate (%)",
    ),
    CurveType.ZERO: CurveSpec(
        date_col="date",
        value_col="rate",
        api_outer="interpolatedCurve",
        api_inner="zeroRate",
        demo_key="zero",
        scale=100.0,
        fmt=".4f",
        y_label="Rate (%)",
    ),
    CurveType.DISCOUNT: CurveSpec(
        date_col="date",
        value_col="factor",
        api_outer="interpolatedCurve",
        api_inner="discountFactor",
        demo_key="discount",
        scale=1.0,
        fmt=".6f",
        y_label="Discount Factor",
    ),
}

# Ordered list for UI selectboxes
CURVE_TYPES: list[CurveType] = list(CurveType)


# ---------------------------------------------------------------------------
# Demo curve manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DemoCurve:
    """Metadata for a single pre-saved demo curve snapshot."""

    curve_id: str
    profile:  str
    label:    str
    filename: str


DEMO_CURVES: list[DemoCurve] = [
    DemoCurve("S329", "COP.OIS",      "Colombia OIS",    "S329_COP.OIS.json"),
    DemoCurve("S490", "USD.SOFR",     "USD SOFR",         "S490_USD.SOFR.json"),
    DemoCurve("S89",  "BRL.BM&F",     "Brazil Pre x DI",  "S89_BRL.BMandF.json"),
    DemoCurve("S583", "MXN.OIS.TIIE", "Mexico OIS TIIE",  "S583_MXN.OIS.TIIE.json"),
    DemoCurve("S193", "CLP.6m",       "Chile CLP 6m",     "S193_CLP.6m.json"),
    DemoCurve("S514", "EUR.OIS.ESTR", "EUR OIS ESTR",     "S514_EUR.OIS.ESTR.json"),
    DemoCurve("S374", "PEN.OIS",      "Peru OIS",         "S374_PEN.OIS.json"),
]


# ---------------------------------------------------------------------------
# Curve request parameters
# ---------------------------------------------------------------------------

Side = Literal["Mid", "Bid", "Ask"]

CURVE_SIDES: list[str] = ["Mid", "Bid", "Ask"]

# UI label → MARS API interpolation method string
INTERPOLATION_METHODS: dict[str, str] = {
    "Piecewise Linear (Simple)": "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    "Smooth Forward (Cont)":     "INTERPOLATION_METHOD_SMOOTH_FWD",
    "Step Forward (Cont)":       "INTERPOLATION_METHOD_STEP_FWD",
    "Piecewise Linear (Cont)":   "INTERPOLATION_METHOD_LINEAR_CONT",
}

INTERPOLATION_INTERVALS: list[str] = ["Daily", "Weekly", "Monthly"]

# Maximum number of days in the interpolated date grid (~33 years)
CURVE_SIZE: int = 12_000


# ---------------------------------------------------------------------------
# CSA OIS curve IDs (currency → Bloomberg curve ID)
# ---------------------------------------------------------------------------

CSA_CURVE_IDS: dict[str, str] = {
    "USD": "S400", "CAD": "S401", "CHF": "S418", "EUR": "S403",
    "GBP": "S405", "JPY": "S404", "SEK": "S417", "AED": "S436",
    "ARS": "S419", "AUD": "S406", "BGN": "S422", "BRL": "S442",
    "CLP": "S423", "CLF": "S440", "CNY": "S407", "CNH": "S432",
    "COP": "S438", "COU": "S441", "CZK": "S424", "DKK": "S408",
    "HKD": "S409", "HUF": "S410", "ILS": "S426", "INR": "S412",
    "ISK": "S411", "KRW": "S421", "MXN": "S428", "MYR": "S427",
    "NOK": "S413", "NZD": "S402", "PEN": "S439", "PHP": "S433",
    "PLN": "S414", "QAR": "S437", "RUB": "S415", "SAR": "S429",
    "SGD": "S416", "THB": "S431", "TRY": "S420", "TWD": "S434",
    "UYU": "S445", "UYI": "S446", "ZAR": "S430",
}


# ---------------------------------------------------------------------------
# Instrument constants (used by swap and bond services)
# ---------------------------------------------------------------------------

# Bloomberg OIS float index tickers referenced in deal structuring
FLOAT_INDICES: list[str] = [
    "BZDIOVRA",
    "CLICP",
    "COOVIBR",
    "ESTRON",
    "MXIBTIEF",
    "SOFRRATE",
]

# Coupon frequency (times per year) → SWPM pay frequency label
BOND_TO_SWPM_PAY_FREQUENCY: dict[int, str] = {
    0:   "At Maturity",
    1:   "Annual",
    2:   "SemiAnnual",
    4:   "Quarterly",
    12:  "Monthly",
    28:  "28 Days",
    52:  "Weekly",
    360: "Daily",
}
