"""
Page — Key Rate Risk (KRR)

DV01 decomposition by tenor bucket, per curve, for a single Bloomberg deal
or an entire portfolio. Uses the Bloomberg MARS KRR API (synchronous).

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

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, MarsApiError
from configs.i18n import t
from configs.krr_config import (
    DEFAULT_DEAL_ID,
    DEFAULT_PORTFOLIO_NAME,
    KRR_DEFINITION_ID,
    KRR_DEFINITION_NAME,
)
from configs.settings import settings
from services.risk_service import KrrResult, KrrService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("krr.title"))
st.caption(t("krr.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "1"


@st.cache_resource(show_spinner=False)
def _get_service(v: str = _SVC_VERSION) -> KrrService:
    return KrrService.from_settings()


# ---------------------------------------------------------------------------
# KRR Definition ID input (shared between deal and portfolio runs)
# ---------------------------------------------------------------------------

krr_def_id = st.text_input(
    t("krr.krr_def_label"),
    value=KRR_DEFINITION_ID,
    help=t("krr.krr_def_help"),
    key="krr_def_id",
)

st.divider()

# ---------------------------------------------------------------------------
# Inputs: Deal ID / Portfolio Name with run buttons
# ---------------------------------------------------------------------------

_col1, _col2 = st.columns(2)

with _col1:
    deal_id = st.text_input(
        t("krr.deal_label"),
        value=DEFAULT_DEAL_ID,
        key="krr_deal_id",
    )
    _run_deal = st.button(t("krr.run_deal_btn"), type="primary", key="krr_run_deal")

with _col2:
    portfolio_name = st.text_input(
        t("krr.portfolio_label"),
        value=DEFAULT_PORTFOLIO_NAME,
        key="krr_portfolio_name",
    )
    _run_portfolio = st.button(t("krr.run_portfolio_btn"), type="primary", key="krr_run_portfolio")

st.divider()

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _fmt_dv01(value: float) -> str:
    try:
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return "—"


def _render_curve_chart(
    curve_label: str,
    dv01_by_tenor: dict[str, float],
) -> None:
    """Render a single bar chart for one curve's KRR tenor profile."""
    tenors = list(dv01_by_tenor.keys())
    values = list(dv01_by_tenor.values())

    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in values]

    fig = go.Figure(data=[
        go.Bar(
            x=tenors,
            y=values,
            marker_color=colors,
            text=[_fmt_dv01(v) for v in values],
            textposition="outside",
        )
    ])
    fig.update_layout(
        title=t("krr.chart_title", curve_label=curve_label),
        xaxis_title=t("krr.col_tenor"),
        yaxis_title=t("krr.col_dv01"),
        showlegend=False,
        height=380,
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame({
        t("krr.col_tenor"): tenors,
        t("krr.col_dv01"): [_fmt_dv01(v) for v in values],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_krr_results(result: KrrResult, is_portfolio: bool = False) -> None:
    """Render KRR results for a deal or an aggregated portfolio."""
    header_key = "krr.portfolio_results_header" if is_portfolio else "krr.deal_results_header"
    st.subheader(t(header_key))

    if is_portfolio:
        # Aggregate DV01 by curve across all deals
        aggregated = result.aggregate_by_curve()

        c1, c2 = st.columns(2)
        c1.metric(t("krr.deal_count"), len(result.deals))
        total_dv01 = sum(sum(v.values()) for v in aggregated.values())
        c2.metric(t("krr.total_dv01"), _fmt_dv01(total_dv01))

        for curve_label, dv01_by_tenor in aggregated.items():
            st.subheader(t("krr.curve_header", label=curve_label))
            _render_curve_chart(curve_label, dv01_by_tenor)

    else:
        # Single deal — show per-curve charts
        for deal in result.deals:
            if len(result.deals) > 1:
                st.subheader(t("krr.deal_header", label=deal.label))

            total_dv01 = sum(c.total_dv01 for c in deal.curves)
            st.metric(t("krr.total_dv01"), _fmt_dv01(total_dv01))

            for curve in deal.curves:
                st.subheader(t("krr.curve_header", label=curve.label))
                _render_curve_chart(curve.label, curve.dv01_by_tenor)


# ---------------------------------------------------------------------------
# Run handlers
# ---------------------------------------------------------------------------

if _run_deal:
    svc = _get_service()
    with st.spinner(t("krr.deal_spinner")):
        try:
            result = svc.run_deal_krr(
                deal_id=deal_id.strip(),
                valuation_date=date.today(),
                krr_def_id=krr_def_id.strip() or KRR_DEFINITION_ID,
                krr_def_name=KRR_DEFINITION_NAME,
            )
            st.session_state["krr_result_deal"] = result
        except IpNotWhitelistedError:
            st.error(
                "Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative."
            )
        except MarsApiError as exc:
            st.error(t("krr.error", error=str(exc)))

if _run_portfolio:
    svc = _get_service()
    with st.spinner(t("krr.portfolio_spinner")):
        try:
            result = svc.run_portfolio_krr(
                portfolio_name=portfolio_name.strip(),
                valuation_date=date.today(),
                krr_def_id=krr_def_id.strip() or KRR_DEFINITION_ID,
                krr_def_name=KRR_DEFINITION_NAME,
            )
            st.session_state["krr_result_portfolio"] = result
        except IpNotWhitelistedError:
            st.error(
                "Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative."
            )
        except MarsApiError as exc:
            st.error(t("krr.error", error=str(exc)))

# ---------------------------------------------------------------------------
# Results — Single Deal
# ---------------------------------------------------------------------------

deal_result: KrrResult | None = st.session_state.get("krr_result_deal")
if deal_result is not None and deal_result.ok:
    if deal_result.deals:
        _render_krr_results(deal_result, is_portfolio=False)
    else:
        st.info(t("krr.no_results"))
elif deal_result is not None and not deal_result.ok:
    st.error(t("krr.error", error=deal_result.error or "Unknown error"))

# ---------------------------------------------------------------------------
# Results — Portfolio
# ---------------------------------------------------------------------------

port_result: KrrResult | None = st.session_state.get("krr_result_portfolio")
if port_result is not None and port_result.ok:
    if port_result.deals:
        _render_krr_results(port_result, is_portfolio=True)
    else:
        st.info(t("krr.no_results"))
elif port_result is not None and not port_result.ok:
    st.error(t("krr.error", error=port_result.error or "Unknown error"))

# ---------------------------------------------------------------------------
# Demo CTA
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")

# ---------------------------------------------------------------------------
# MARS API capabilities reference
# ---------------------------------------------------------------------------

_API_DOCS = """
## Bloomberg MARS API — Key Rate Risk (KRR)

Key Rate Risk (KRR) measures the sensitivity of a deal's present value to a 1bp shift at each
individual tenor point of the interest rate curve, keeping all other tenors unchanged. The result
is a DV01 profile across the curve — a decomposition that reveals exactly which maturity buckets
carry the most interest rate risk.

Unlike a single DV01 number (which represents a parallel shift of the entire curve), KRR shows
the *shape* of the risk: a 5-year OIS swap will concentrate its KRR near the 5Y tenor, while a
XCCY swap will show KRR across two separate curves (the local currency leg and the USD leg),
each with its own tenor structure.

### KRR Definition ID

Before running a KRR request, you must configure a **Greek Definition** in Bloomberg MARS:

```
MARS <GO> → Settings → User Settings → Key Rate Risk → Greek Definition ID
```

Save the configuration to generate a new Greek Definition ID. This ID controls which tenors
are used as bucket boundaries, the shift size (typically 1bp), and how the shift is applied
(zero rate, par rate, etc.).

The definition name `"mars api per currency krr shift zero annual"` applies the shift
independently per currency — so multi-currency deals produce separate KRR profiles per curve.

### API Endpoints

| Operation | Endpoint |
|---|---|
| Single deal KRR | `POST /marswebapi/v1/securitiesKrr` |
| Portfolio KRR | `POST /enterprise/mars/portfolioKrr` |

Both endpoints are **synchronous** — results are returned inline in the response, with no
polling required.

### Single Deal KRR Request

```json
{
  "securitiesKrrRequest": {
    "pricingParameter": {
      "valuationDate": "2026-03-29",
      "requestedField": ["DV01", "Notional", "Ticker"]
    },
    "krrDefinition": {
      "id": "7609023221901295616",
      "externalName": "mars api per currency krr shift zero annual"
    },
    "security": [
      { "identifier": { "bloombergDealId": "SLLVJ42Q Corp" }, "position": 1 }
    ]
  }
}
```

### Portfolio KRR Request

```json
{
  "pricingParameter": {
    "valuationDate": "2026-03-29",
    "requestedField": ["DV01", "Notional", "Ticker"]
  },
  "krrDefinition": {
    "id": "7609023221901295616",
    "externalName": "mars api per currency krr shift zero annual"
  },
  "portfolio": {
    "portfolioName": "MARS_VIBE_CODING",
    "portfolioSource": "PORTFOLIO",
    "portfolioDate": "2026-03-29"
  }
}
```

### Response Structure

Each deal in the response contains a `krrResult` block alongside the standard pricing fields:

```json
{
  "krrResult": {
    "krrId": "7609023221901295616",
    "krrExternalName": "mars api per currency krr shift zero annual",
    "krrRiskResults": [
      {
        "valuationCurrency": "USD",
        "underlyingIRCurrency": "USD",
        "curveid": "S490",
        "errorCode": 0,
        "krrs": [
          { "term": { "term": 1, "unit": "YEAR" }, "ticker": "1 YR",  "krr": -33.0 },
          { "term": { "term": 2, "unit": "YEAR" }, "ticker": "2 YR",  "krr": -62.4 },
          { "term": { "term": 5, "unit": "YEAR" }, "ticker": "5 YR",  "krr": 4376.5 }
        ]
      }
    ]
  }
}
```

### Multi-curve results

For XCCY/NDS deals, the `krrRiskResults` array contains **one entry per curve** — for example,
a COP/USD NDS will have separate entries for the COP OIS curve (S329) and the USD SOFR curve
(S490). Each curve has its own tenor set and its own `ticker` notation:

| Curve type | Example tickers |
|---|---|
| USD SOFR, EUR OIS | `1 WK`, `3 MO`, `1 YR`, `5 YR`, `30 YR` |
| BRL Pre×DI (S89) | `JAN 31`, `APR 31` (IMM-style dates) |
| BRL (S387) | `92 DY`, `184 DY`, `1827 DY` (day counts) |
| MXN TIIE (S583) | `1x1`, `13x1`, `52x1`, `91x1` (TIIE contract notation) |
| COP/PEN | `92 DY`, `366 DY`, `549 DY`, `2 YR`, `5 YR` |
"""

st.divider()
with st.expander("About the MARS API", expanded=True):
    st.markdown(_API_DOCS)
