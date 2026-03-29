"""
Page — Portfolio

Price any existing Bloomberg portfolio via portfolioPricingRequest and
display MTM and risk metrics per deal with portfolio-level aggregates.

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
import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, MarsApiError
from configs.i18n import t
from configs.portfolio_config import MARS_API_FIELDS, PORTFOLIO_NAME
from configs.settings import DEMO_DATE, settings
from services.portfolio_service import (
    PortfolioPricingService,
    PortfolioResult,
)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("portfolio.title"))
st.caption(t("portfolio.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "3"


@st.cache_resource(show_spinner=False)
def _get_service(v: str = _SVC_VERSION) -> PortfolioPricingService:
    return PortfolioPricingService.from_settings()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

_UNIFIED_DISPLAY_COLS: dict[str, str] = {"_label": "Deal"}
for _fn in MARS_API_FIELDS:
    _UNIFIED_DISPLAY_COLS[_fn] = _fn

_STRING_FIELDS: frozenset[str] = frozenset({
    "_label", "AsOfTimestamp", "AssetClass", "AssetType", "BaseCurrency",
    "BloombergDealId", "Call/Put", "CouponType", "Currency", "DayCount",
    "DealCcy", "Description", "Direction", "EffectiveDate", "ErrorCode",
    "ErrorMessage", "Exercise", "ExpiryDate", "FloatIndex", "Frequency",
    "FX_CCY1", "FX_CCY2", "Long/Short", "MarketDataDate", "MaturityDate",
    "NotionalCcy", "NotionalCcy1", "NotionalCcy2", "PayCcy", "PayFrequency",
    "ReceiveCcy", "Security", "SecurityCustomID", "Ticker", "Underlying",
    "UnderlyingCcy", "UniqueID", "ValuationDate",
})


def _fmt(value: float, decimals: int = 2) -> str:
    try:
        return f"{value:,.{decimals}f}"
    except (ValueError, TypeError):
        return "—"


def _build_display_df(
    deals: list[dict[str, str]], col_map: dict[str, str],
) -> pd.DataFrame:
    """Extract the columns in *col_map* from the deals list and rename them."""
    rows: list[dict[str, str]] = []
    for d in deals:
        row: dict[str, str] = {}
        for src_col, display_name in col_map.items():
            raw = d.get(src_col, "")
            if src_col in _STRING_FIELDS:
                row[display_name] = raw
            else:
                try:
                    row[display_name] = f"{float(raw):,.2f}" if raw else "—"
                except (ValueError, TypeError):
                    row[display_name] = raw or "—"
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Portfolio selector + pricing
# ---------------------------------------------------------------------------

today = date.today()
svc = _get_service()
portfolio_names: list[str] = svc.list_portfolios()

if portfolio_names:
    default_idx = 0
    if PORTFOLIO_NAME in portfolio_names:
        default_idx = portfolio_names.index(PORTFOLIO_NAME)
    selected_portfolio = st.selectbox(
        t("portfolio.select_label"),
        options=portfolio_names,
        index=default_idx,
        key="portfolio_selector",
    )
else:
    selected_portfolio = st.text_input(
        t("portfolio.select_label"),
        value=PORTFOLIO_NAME,
        key="portfolio_selector",
    )

if st.button(t("portfolio.price_btn"), type="primary", key="btn_price"):
    with st.spinner(t("portfolio.pricing_spinner")):
        try:
            price_result: PortfolioResult = svc.price_portfolio(
                selected_portfolio, today,
            )
            st.session_state["portfolio_result"] = price_result
        except IpNotWhitelistedError:
            st.error(
                "🔒 Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative to whitelist "
                "your current IP."
            )
        except MarsApiError as exc:
            st.error(f"Pricing error: {exc}")

# ---------------------------------------------------------------------------
# Results display — unified table
# ---------------------------------------------------------------------------

result: PortfolioResult | None = st.session_state.get("portfolio_result")

if result is not None and result.ok:
    agg = result.aggregate

    st.subheader(t("portfolio.summary_header"))

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("portfolio.deal_count"),  int(agg.get("DealCount", 0)))
    c2.metric(t("portfolio.total_mtm"),   _fmt(agg.get("MktValPortCcy", 0)))
    c3.metric(t("portfolio.total_dv01"),  _fmt(agg.get("DV01PortCcy", 0)))
    c4.metric(t("portfolio.total_pv01"),  _fmt(agg.get("PV01", 0)))
    c5.metric(t("portfolio.total_vega"),  _fmt(agg.get("Vega", 0)))
    c6.metric(t("portfolio.total_delta"), _fmt(agg.get("Delta", 0)))

    st.subheader(t("portfolio.deals_header"))
    unified_df = _build_display_df(result.deals, _UNIFIED_DISPLAY_COLS)

    all_columns = list(unified_df.columns)
    _DEFAULT_COLS = [
        "Deal", "DealCcy", "NotionalCcy", "Notional",
        "MktValPortCcy", "DV01PortCcy", "PV01",
        "MktPx", "Delta", "Gamma", "Vega",
    ]
    default_cols = [c for c in _DEFAULT_COLS if c in all_columns]
    visible_cols = st.multiselect(
        t("portfolio.select_columns"),
        options=all_columns,
        default=default_cols,
        key="portfolio_col_picker",
    )
    if visible_cols:
        st.dataframe(
            unified_df[visible_cols],
            use_container_width=True, hide_index=True,
        )

elif result is not None and not result.ok:
    st.error(result.error)

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
## Bloomberg MARS API — Portfolio Pricing

MARS API can price an entire Bloomberg portfolio in a single API call, using one consistent market
data snapshot for every position regardless of asset class. This single-snapshot approach is one of
MARS's most important architectural properties: because all deals are priced against the same
market data at the same instant, cross-asset risk metrics — total portfolio DV01, aggregated MktVal,
net Greeks — are internally consistent and directly comparable. This is a property that cannot be
guaranteed when combining results from multiple pricing systems or vendors.

MARS integrates natively with Bloomberg's trading and portfolio systems — PRTU portfolios,
AIM (Asset & Investment Manager) accounts, and TOMS (Trade Order Management System) books can
all be passed directly to the API without any manual position extraction or file upload. For
middle office and valuation teams, the MARS API can serve as a primary or secondary source for
independent price verification (IPV) of derivatives portfolios.

### Key capabilities

- **Single snapshot pricing** — all deals priced at the same market data timestamp, ensuring
  cross-asset consistency for aggregated risk and P&L attribution
- **Native system integration** — price PRTU portfolios, AIM accounts, TOMS books, and BVAL
  portfolios without manual data export
- **100+ pricing fields** — request any combination of MktVal, DV01, Greeks, cashflows,
  accruals, notional, and metadata fields per deal
- **Portfolio currency** — receive results in portfolio currency (`MktValPortCcy`, `DV01PortCcy`)
  for consolidated reporting across multi-currency books
- **Historical snapshots** — price the portfolio as it stood on any past date using `portfolioDate`
- **Bulk pricing** — price multiple portfolios in a single request with `bulkPortfolioPricingRequest`
- **Asset type filtering** — scope pricing to specific instrument types within a mixed portfolio
- **Scenario overlay** — combine with `scenarioParameter` to price the entire portfolio under
  stress scenarios simultaneously (see Stress Testing page)

### Endpoint

**`POST /marswebapi/v1/portfolioPricing`**

```json
{
  "portfolioPricingRequest": {
    "pricingParameter": {
      "valuationDate": "2026-03-29",
      "requestedField": [
        "MktVal", "MktValPortCcy", "DV01", "DV01PortCcy",
        "AccruedInterest", "Notional", "ValuationDate"
      ],
      "portfolioCurrency": "USD"
    },
    "portfolioDescription": {
      "portfolioName": "MY_PORTFOLIO",
      "portfolioSource": "PORTFOLIO",
      "portfolioDate": "2026-03-29"
    }
  }
}
```

### `portfolioSource` values

| Value | Description |
|---|---|
| `PORTFOLIO` | Bloomberg PRTU portfolio (most common for buy-side firms) |
| `PORTFOLIO_GROUP` | A group of PRTU portfolios — aggregates across all included books |
| `AIM_ACCOUNT` | AIM (Asset & Investment Manager) account |
| `AIM_ACCOUNT_GROUP` | Group of AIM accounts |
| `TOMS_BOOK` | TOMS (Trade Order Management System) trading book |
| `BVAL_PORTFOLIO` | BVAL-sourced portfolio for independent price verification workflows |

### Key `pricingParameter` fields

| Parameter | Required | Description |
|---|---|---|
| `valuationDate` | Yes | Date on which to price the portfolio |
| `requestedField` | Yes | Array of pricing fields to return per deal |
| `portfolioCurrency` | No | Currency for `*PortCcy` fields; defaults to each deal's native currency |
| `marketDataDate` | No | Override market data date independently of valuation date |
| `cashflow` | No | Include projected cashflow schedules for all deals |

### Bulk pricing — multiple portfolios in one call

```json
{
  "bulkPortfolioPricingRequest": {
    "pricingParameter": {
      "valuationDate": "2026-03-29",
      "requestedField": ["MktVal", "MktValPortCcy", "DV01"]
    },
    "portfolioSourceDescription": {
      "portfolioSourceDetails": [
        { "portfolioName": "RATES_BOOK",  "portfolioSource": "PORTFOLIO" },
        { "portfolioName": "FX_BOOK",     "portfolioSource": "PORTFOLIO" },
        { "portfolioName": "CREDIT_BOOK", "portfolioSource": "TOMS_BOOK" }
      ]
    }
  }
}
```

### Asset type filter

Restrict pricing to specific instrument classes within a mixed-asset portfolio:

```json
"additionalParameter": [
  {
    "name": "AssetTypeFilter",
    "value": { "stringVal": "Interest Rate Swap,Cross Currency Swap,OIS" }
  }
]
```

Values for the filter can be seen by loading `{FLDS DS213}` on the Bloomberg Terminal.
"""

st.divider()
with st.expander("About the MARS API", expanded=True):
    st.markdown(_API_DOCS)
