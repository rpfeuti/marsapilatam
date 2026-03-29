"""
Page — Interest Rate Curves

Downloads rate curves from Bloomberg's XMarket platform and displays them
as an interactive Plotly chart plus a raw data table.

Supported curve types (defined in configs/curves_config.py):
- Raw Curve        — par rates at instrument maturities
- Zero Coupon      — interpolated zero rates at custom date grid
- Discount Factor  — interpolated discount factors at custom date grid

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

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from bloomberg.exceptions import CurveError, MarsApiError
from configs.curves_catalog import CURVES_BY_LABEL
from configs.curves_config import (
    CURVE_SIDES,
    CURVE_SIZE,
    CURVE_SPECS,
    CURVE_TYPES,
    DEMO_CURVES,
    INTERPOLATION_INTERVALS,
    INTERPOLATION_METHODS,
    CurveType,
)
from configs.i18n import t
from configs.settings import settings
from services.curves_service import CurveQuery, XMarketCurveService

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

st.title(t("curves.title"))
st.caption(t("curves.caption"))

# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service — one instance per market_date per browser session
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=t("curves.spinner_session"))
def get_service(market_date: date) -> XMarketCurveService:
    return XMarketCurveService.from_settings(market_date)


# ---------------------------------------------------------------------------
# Cached data download — CurveQuery is frozen+hashable, so it's a safe key
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=t("curves.spinner_download"))
def fetch_curve(_svc: XMarketCurveService, query: CurveQuery, market_date: date | None = None) -> pd.DataFrame:
    return _svc.get_curve(query)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _lrow(label: str, ratio: tuple[int, int] = (1, 2)) -> st.delta_generator.DeltaGenerator:
    """Render a label in the left mini-column, return the right mini-column for the widget."""
    c_lbl, c_inp = st.columns(ratio)
    c_lbl.markdown(
        f"<p style='margin-top:8px;font-size:0.85em;color:#aaa'>{label}</p>",
        unsafe_allow_html=True,
    )
    return c_inp


# ---------------------------------------------------------------------------
# Curve controls (main page)
# ---------------------------------------------------------------------------

_demo_ids   = {c.curve_id for c in DEMO_CURVES}
_labels_map = (
    {lbl: cid for lbl, cid in CURVES_BY_LABEL.items() if cid in _demo_ids}
    if IS_DEMO
    else CURVES_BY_LABEL
)

_labels        = list(_labels_map.keys())
_default_label = next((lbl for lbl in _labels if "USD.SOFR" in lbl), _labels[0])

col_params, col_dates = st.columns(2)

with col_params:
    st.markdown(f"**{t('curves.sidebar_header')}**")

    curve_label = _lrow(t("curves.curve_label")).selectbox(
        "", options=_labels, index=_labels.index(_default_label),
        help=t("curves.curve_help_demo") if IS_DEMO else t("curves.curve_help"),
        label_visibility="collapsed",
    )
    curve_id = _labels_map[curve_label]

    curve_type: CurveType = _lrow(t("curves.curve_type_label")).selectbox(
        "", options=CURVE_TYPES, label_visibility="collapsed",
    )

    side = _lrow(t("curves.side_label")).selectbox(
        "", options=CURVE_SIDES, disabled=IS_DEMO, label_visibility="collapsed",
    )

    is_raw = curve_type == CurveType.RAW
    interpolation_label = _lrow(t("curves.interpolation_label")).selectbox(
        "", options=list(INTERPOLATION_METHODS.keys()),
        disabled=is_raw, label_visibility="collapsed",
    )
    interpolation = INTERPOLATION_METHODS[interpolation_label]

    interval = _lrow(t("curves.interval_label")).selectbox(
        "", options=INTERPOLATION_INTERVALS,
        disabled=is_raw, help=t("curves.interval_help"),
        label_visibility="collapsed",
    )

with col_dates:
    st.markdown(f"**{t('curves.curve_id_caption', curve_id=curve_id)}**")

    as_of = _lrow(t("curves.curve_date_label")).date_input(
        "", value=date(2026, 3, 18) if IS_DEMO else date.today(),
        disabled=IS_DEMO, key="curves_as_of", label_visibility="collapsed",
    )
    market_date = as_of

    st.markdown("")
    run = st.button(t("curves.button_load"), type="primary", use_container_width=True)

    if IS_DEMO:
        st.divider()
        st.markdown(t("common.demo_cta_sidebar"))

# ---------------------------------------------------------------------------
# MARS API capabilities reference
# ---------------------------------------------------------------------------

_API_DOCS = """
## Bloomberg MARS API — Interest Rate Curves Analytics

Bloomberg's Multi-Asset Risk System (MARS) provides enterprise programmatic access to Bloomberg's
complete suite of Interest Rate Curves — the same curves that power pricing, risk, and valuation
workflows on the Bloomberg Terminal. While standard enterprise channels deliver fixed, standardized
data sets in predefined formats, MARS API exposes a fully customizable channel: users can specify
any curve, any output type, any date grid, and any interpolation method, and receive results in
real-time or for any historical date. Curves downloaded via MARS API can be directly used to
override Bloomberg standard curves in downstream pricing and scenario analysis workflows under
the same license — making them a foundational input for consistent, end-to-end quantitative workflows.

### Why MARS API for curves vs alternatives

| Feature | Curves Toolkit (CTK / Excel) | MARS API |
|---|---|---|
| Swap Curves | Yes | Yes |
| Cross-Currency Basis Curves | Yes | Yes |
| Treasury Curves | No | Yes |
| Sovereign Curves | No | Yes |
| Sector & Issuer Curves | No | Yes |
| Collateral / CSA Curves | No | Yes |
| Ultimate Forward Rate (UFR) | No | Yes |
| Enterprise programmatic channel | No | Yes |
| Override curves in pricing workflows | No | Yes |
| Custom interpolation & tenor grids | Limited | Yes |
| Historical back-dating | Limited | Yes |
| Integration with scenario analysis | No | Yes |

### Supported curve types

**Swap Curves** — OIS and IBOR-based interest rate swap curves, used to discount and project
cash flows for interest rate derivatives. Available for all major currencies including USD (SOFR),
EUR (ESTR), GBP (SONIA), COP, BRL, MXN, CLP, and many others.

**Cross-Currency Basis Curves** — Capture the funding cost differential between two currencies.
Essential for pricing cross-currency swaps, XCCY basis products, and FX-hedged bond analysis.

**Treasury Curves** — Government bond benchmark curves, used as risk-free reference rates for
spread calculations, relative value analysis, and regulatory capital computations.

**Sovereign Curves** — Curves for sovereign issuers, used in credit risk, spread analysis,
and emerging market pricing across Latin America, EMEA, and Asia.

**Sector & Issuer Curves** — Corporate sector or individual issuer-specific curves, enabling
accurate credit spread analysis and relative value comparisons within a peer group.

**Collateral Curves (CSA)** — CSA-adjusted discount curves accounting for collateral posting
agreements under ISDA terms. Required for correct OIS-discounted derivatives pricing where
the CSA specifies a specific collateral currency or rate index.

**Ultimate Forward Rate (UFR) Curves** — Extrapolated long-end curves following Solvency II /
EIOPA methodology, used for discounting insurance liabilities and regulatory capital calculations
where observable market data is unavailable beyond the Last Liquid Point.

### Output types

**Raw (par rates)** — The rates at the actual instrument maturities used to construct the curve
(deposits, futures, FRAs, swaps). Useful for understanding the input instruments and their
quoted rates at each tenor.

**Zero Coupon (spot rates)** — Bootstrapped zero rates, interpolated at any set of requested
dates. Zero rates are the foundation for discounting individual cash flows and computing
forward rates between any two dates.

**Discount Factors** — Present value factors derived from zero rates, interpolated at any date.
Used directly in cash flow valuation and duration calculations.

### Endpoint

**`POST /marswebapi/v1/dataDownload`**

Download a curve snapshot for any XMarket curve, specifying the output type, market side,
and optionally a custom date grid for interpolated outputs.

```json
{
  "dataDownloadRequest": {
    "header": {
      "type": "XMarket",
      "curveId": "S329",
      "side": "Mid"
    },
    "curveAttributes": {
      "curveType": "ZeroCoupon"
    },
    "requestedDates": [
      "2026-01-15", "2026-06-15", "2027-01-15", "2028-01-15",
      "2030-01-15", "2035-01-15", "2040-01-15", "2050-01-15"
    ]
  }
}
```

### Key request parameters

| Parameter | Required | Description |
|---|---|---|
| `curveId` | Yes | XMarket curve identifier (e.g. `S329` for COP OIS, `S50` for USD SOFR) |
| `side` | Yes | `Mid`, `Bid`, or `Ask` |
| `curveType` | Yes | `Raw`, `ZeroCoupon`, or `DiscountFactor` |
| `requestedDates` | No | Custom date array for interpolated zero / discount factor outputs |
| `valuationDate` | No | Historical back-date — retrieve the curve as it was on any past date |

### Typical use cases

- **Swap pricing** — download the discount and projection curves for a currency and override
  the default curves in a `securitiesPricingRequest` for custom pricing scenarios
- **ALM / liability duration** — retrieve monthly zero-coupon curves to discount insurance or
  pension liability cash flows at each reporting date
- **Curve history** — pull the same curve at multiple historical dates to analyse rate movements,
  shifts in the term structure, and basis dynamics over time
- **Regulatory reporting** — download UFR-extrapolated curves for Solvency II technical
  provision discounting or EIOPA stress testing
- **Model calibration** — extract discount factors and forward rates as inputs to proprietary
  valuation models or to validate third-party pricing systems against Bloomberg data
- **Cross-currency analysis** — download both a domestic OIS curve and the XCCY basis curve
  to compute the all-in cross-currency funding cost for a structured transaction
"""

# ---------------------------------------------------------------------------
# Guard: stop until the user clicks Load
# ---------------------------------------------------------------------------

if not run:
    st.info(t("curves.info_idle"))
    st.divider()
    with st.expander("About the MARS API", expanded=True):
        st.markdown(_API_DOCS)
    st.stop()

if not IS_DEMO and not is_raw and as_of >= market_date + timedelta(days=CURVE_SIZE):
    st.error(t("curves.error_date_range"))
    st.stop()

# ---------------------------------------------------------------------------
# Build the query value object
# ---------------------------------------------------------------------------

if is_raw:
    requested_dates: tuple[date, ...] = ()
else:
    step_map = {"Daily": 1, "Weekly": 7, "Monthly": 30}
    step     = timedelta(days=step_map[interval])
    d        = as_of + timedelta(days=1)
    limit    = as_of + timedelta(days=CURVE_SIZE)
    dates: list[date] = []
    while d < limit:
        dates.append(d)
        d += step
    requested_dates = tuple(dates)

query = CurveQuery(
    curve_id=curve_id,
    curve_type=curve_type,
    as_of=as_of,
    side=side,
    requested_dates=requested_dates,
    interpolation=interpolation,
)

# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

try:
    svc = get_service(market_date)
    df  = fetch_curve(svc, query, market_date=market_date)
except CurveError as e:
    st.error(t("curves.error_curve", error=e))
    st.stop()
except MarsApiError as e:
    st.error(t("curves.error_api", error=e))
    st.stop()

if df.empty:
    st.warning(t("curves.warning_empty"))
    st.stop()

# ---------------------------------------------------------------------------
# Display scaling — applied once; spec drives chart and table consistently
# ---------------------------------------------------------------------------

spec       = CURVE_SPECS[curve_type]
df_display = df.drop(columns=["tenor_days"], errors="ignore").copy()
df_display[spec.value_col] = (
    pd.to_numeric(df_display[spec.value_col], errors="coerce") * spec.scale
)

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

profile     = curve_label.split(" (")[0]
demo_tag    = t("curves.demo_date_tag") if IS_DEMO else ""
chart_title = t(
    "curves.chart_title",
    curve_type=str(curve_type),
    profile=profile,
    curve_id=curve_id,
    demo_tag=demo_tag,
)

if curve_type == CurveType.RAW and "tenor_days" in df.columns:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["tenor_days"],
        y=df_display[spec.value_col],
        mode="lines+markers",
        text=df["maturityTenor"],
        hovertemplate=f"<b>%{{text}}</b><br>{spec.y_label}: %{{y:{spec.fmt}}}<extra></extra>",
    ))
    fig.update_layout(
        title=chart_title,
        xaxis=dict(
            tickmode="array",
            tickvals=df["tenor_days"].tolist(),
            ticktext=df["maturityTenor"].tolist(),
            title=t("curves.xaxis_tenor"),
        ),
        yaxis_title=spec.y_label,
        hovermode="x unified",
        height=450,
    )
else:
    fig = px.line(df_display, x=spec.date_col, y=spec.value_col, title=chart_title, markers=True)
    fig.update_layout(
        hovermode="x unified",
        xaxis_title=t("curves.xaxis_date"),
        yaxis_title=spec.y_label,
        height=450,
    )

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Data table — value column formatted as string for consistent alignment
# ---------------------------------------------------------------------------

st.subheader(t("curves.table_header", n=len(df_display)))
df_display[spec.value_col] = df_display[spec.value_col].apply(
    lambda x: f"{x:{spec.fmt}}" if pd.notna(x) else ""
)
st.dataframe(df_display, use_container_width=True, height=400)

# ---------------------------------------------------------------------------
# Demo CTA at page bottom
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")

st.divider()
with st.expander("About the MARS API", expanded=True):
    st.markdown(_API_DOCS)
