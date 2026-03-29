"""
Page -- IRRBB Stress Testing

Run interest rate shock scenarios on a pre-saved Bloomberg deal or an entire
portfolio.  Users edit a full tenor x scenario grid (bp shifts), then price
the deal / portfolio under all scenarios in a single API call.

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
from configs.settings import DEMO_DATE, settings
from configs.stress_config import (
    DEFAULT_DEAL_ID,
    DEFAULT_PORTFOLIO_NAME,
    IRRBB_MATRIX,
    IRRBB_SCENARIOS,
    IRRBB_TENORS,
)
from services.stress_service import StressResult, StressScenario, StressService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("stress.title"))
st.caption(t("stress.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "4"


@st.cache_resource(show_spinner=False)
def _get_service(v: str = _SVC_VERSION) -> StressService:
    return StressService.from_settings()


# ---------------------------------------------------------------------------
# Inputs: Deal ID / Portfolio Name with their run buttons (above the grid)
# ---------------------------------------------------------------------------

_input_col1, _input_col2 = st.columns(2)

with _input_col1:
    deal_id = st.text_input(
        t("stress.deal_label"),
        value=DEFAULT_DEAL_ID,
        key="stress_deal_id",
    )
    _run_deal = st.button(t("stress.run_btn"), type="primary", key="stress_run_deal")

with _input_col2:
    portfolio_name = st.text_input(
        t("stress.portfolio_label"),
        value=DEFAULT_PORTFOLIO_NAME,
        key="stress_portfolio_name",
    )
    _run_portfolio = st.button(t("stress.run_btn"), type="primary", key="stress_run_portfolio")

# ---------------------------------------------------------------------------
# Shared scenario grid (tenor x scenario)
# ---------------------------------------------------------------------------

st.subheader(t("stress.scenarios_header"))
st.caption(t("stress.grid_caption"))

_GRID_KEY = "stress_grid_df_v4"
_EDITOR_KEY = "stress_grid_editor_v4"


def _build_default_grid() -> pd.DataFrame:
    data: dict[str, list] = {"Tenor": list(IRRBB_TENORS)}
    for scenario in IRRBB_SCENARIOS:
        data[scenario] = [IRRBB_MATRIX[scenario].get(tenor, 0.0) for tenor in IRRBB_TENORS]
    return pd.DataFrame(data)


if _GRID_KEY not in st.session_state:
    st.session_state[_GRID_KEY] = _build_default_grid()

column_config: dict = {
    "Tenor": st.column_config.TextColumn(label="Tenor", disabled=True, width="small"),
    **{
        scenario: st.column_config.NumberColumn(
            label=scenario,
            min_value=-2000.0,
            max_value=2000.0,
            step=25.0,
            format="%.0f bp",
        )
        for scenario in IRRBB_SCENARIOS
    },
}

edited_grid: pd.DataFrame = st.data_editor(
    st.session_state[_GRID_KEY],
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config=column_config,
    key=_EDITOR_KEY,
)

col_reset, _ = st.columns([1, 5])
if col_reset.button("↺ Reset to IRRBB defaults", key="stress_reset"):
    st.session_state[_GRID_KEY] = _build_default_grid()
    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt(raw: str, decimals: int = 2) -> str:
    try:
        return f"{float(raw):,.{decimals}f}"
    except (ValueError, TypeError):
        return raw if raw else "—"


def _to_float(raw: str) -> float:
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def _build_scenarios_from_grid(grid: pd.DataFrame) -> list[StressScenario]:
    scenarios: list[StressScenario] = []
    for col in IRRBB_SCENARIOS:
        tenor_shifts = {
            row["Tenor"]: float(row[col])
            for _, row in grid.iterrows()
        }
        scenarios.append(StressScenario(name=col, tenor_shifts=tenor_shifts))
    return scenarios


def _render_stress_results(result: StressResult, chart_title: str, session_key: str) -> None:
    base = result.base_metrics
    base_mtm = _to_float(base.get("MktValPortCcy", "0"))

    st.subheader(t("stress.base_case") if "deal" in session_key else t("stress.portfolio_base_case"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("stress.base_mtm"), _fmt(base.get("MktValPortCcy", "")))
    c2.metric(t("stress.base_dv01"), _fmt(base.get("DV01PortCcy", "")))
    c3.metric(t("stress.base_pv01"), _fmt(base.get("PV01", "")))
    c4.metric(t("stress.base_price"), _fmt(base.get("MktPx", "")))

    if result.scenario_results:
        st.subheader(
            t("stress.results_header") if "deal" in session_key
            else t("stress.portfolio_results_header")
        )

        rows: list[dict[str, str]] = []
        chart_names: list[str] = []
        chart_deltas: list[float] = []

        for so in result.scenario_results:
            sc_mtm = _to_float(so.metrics.get("MktValPortCcy", "0"))
            delta_mtm = sc_mtm - base_mtm
            rows.append({
                t("stress.col_scenario"): so.name,
                t("stress.col_mtm"): _fmt(so.metrics.get("MktValPortCcy", "")),
                t("stress.col_delta_mtm"): f"{delta_mtm:+,.2f}",
                t("stress.col_dv01"): _fmt(so.metrics.get("DV01PortCcy", "")),
            })
            chart_names.append(so.name)
            chart_deltas.append(delta_mtm)

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        colors = ["#e74c3c" if d < 0 else "#2ecc71" for d in chart_deltas]
        fig = go.Figure(data=[
            go.Bar(
                x=chart_names,
                y=chart_deltas,
                marker_color=colors,
                text=[f"{d:+,.0f}" for d in chart_deltas],
                textposition="outside",
            )
        ])
        fig.update_layout(
            title=chart_title,
            xaxis_title=t("stress.col_scenario"),
            yaxis_title=t("stress.col_delta_mtm"),
            showlegend=False,
            height=420,
            margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("stress.no_results"))


# ---------------------------------------------------------------------------
# Run handlers
# ---------------------------------------------------------------------------

if _run_deal:
    scenarios = _build_scenarios_from_grid(edited_grid)
    svc = _get_service()
    with st.spinner(t("stress.running_spinner")):
        try:
            result = svc.run_stress_test(
                deal_id=deal_id.strip(),
                scenarios=scenarios,
                valuation_date=date.today(),
            )
            st.session_state["stress_result_deal"] = result
        except IpNotWhitelistedError:
            st.error(
                "Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative."
            )
        except MarsApiError as exc:
            st.error(t("stress.error", error=str(exc)))

if _run_portfolio:
    scenarios = _build_scenarios_from_grid(edited_grid)
    svc = _get_service()
    with st.spinner(t("stress.portfolio_spinner")):
        try:
            result = svc.run_portfolio_stress_test(
                portfolio_name=portfolio_name.strip(),
                scenarios=scenarios,
                valuation_date=date.today(),
            )
            st.session_state["stress_result_portfolio"] = result
        except IpNotWhitelistedError:
            st.error(
                "Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative."
            )
        except MarsApiError as exc:
            st.error(t("stress.error", error=str(exc)))

# ---------------------------------------------------------------------------
# Results – Single Deal
# ---------------------------------------------------------------------------

deal_result: StressResult | None = st.session_state.get("stress_result_deal")
if deal_result is not None and deal_result.ok:
    _render_stress_results(deal_result, t("stress.chart_title"), "deal")
elif deal_result is not None and not deal_result.ok:
    st.error(t("stress.error", error=deal_result.error or "Unknown error"))

# ---------------------------------------------------------------------------
# Results – Portfolio
# ---------------------------------------------------------------------------

port_result: StressResult | None = st.session_state.get("stress_result_portfolio")
if port_result is not None and port_result.ok:
    _render_stress_results(port_result, t("stress.portfolio_chart_title"), "portfolio")
elif port_result is not None and not port_result.ok:
    st.error(t("stress.error", error=port_result.error or "Unknown error"))

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
## Bloomberg MARS API — Scenario Analysis & Stress Testing

MARS API's scenario analysis engine is designed for pre-deal analysis and intra-day risk monitoring
against portfolio limits. Bloomberg MARS uses a consistent, centralized market data and settings
framework across all asset classes, which means that a single scenario (e.g. a +200bp parallel
rate shock) is applied consistently across all interest rate sensitive positions in a portfolio —
regardless of whether they are OIS swaps, XCCY swaps, inflation-linked instruments, or fixed-income
securities. This cross-asset consistency is critical for IRRBB regulatory reporting, where all
exposures must be shocked using the same scenario definition.

Named SHOC (Shock) scenarios apply user-defined market shocks to a deal or an entire portfolio, with
all scenarios priced simultaneously in a single API call. The results include both base-case and
stressed metrics per security, so Delta MtM and Delta DV01 per scenario can be computed directly
from the response without any additional API calls.

### Key capabilities

- **Per-tenor shock granularity** — apply different bp shifts at each tenor point (1D, 1M, 1Y, 5Y,
  10Y, etc.) to model non-parallel rate movements such as steepeners, flatteners, and short-rate shocks
- **Multi-currency scenarios** — specify shifts for each currency independently; `shiftWhat` filter
  targets specific currency/tenor combinations
- **Three shock modes** — absolute (additive bp shift), percent (multiplicative), or override (replace)
- **Simultaneous multi-scenario pricing** — create multiple scenarios and pass all `scenarioId`s in
  one `securitiesPricingRequest` to receive base + all stressed metrics in a single response
- **Works for single deals and portfolios** — `scenarioParameter` is supported by both
  `securitiesPricing` and `portfolioPricing` with the same syntax
- **IRRBB Basel scenarios** — the six standard Basel interest rate risk in the banking book scenarios
  (Parallel Up, Parallel Down, Steepener, Flattener, Short Rate Up, Short Rate Down) are
  implementable directly with per-tenor `swapCurveShift` nodes
- **Ephemeral scenarios** — scenarios are created on-demand and deleted after use; no persistent
  scenario storage is required

### Use cases

- **Regulatory IRRBB reporting** — run the six Basel IRRBB scenarios on a banking book and report
  EVE (Economic Value of Equity) and NII (Net Interest Income) sensitivities
- **Pre-deal analysis** — before trading, price a proposed deal under stress scenarios to understand
  its contribution to portfolio risk under adverse market conditions
- **Intra-day limit monitoring** — run scenario repricing throughout the day to track portfolio
  exposure against approved risk limits
- **Hedge effectiveness** — price the hedged and unhedged portfolio under the same scenarios to
  validate that the hedge reduces stressed P&L as expected
- **Custom regulatory scenarios** — implement EBA, Fed, or other regulatory stress test specifications
  as named scenarios with precise tenor-level shift vectors

### Full lifecycle

**Step 1 — Create a scenario**

**`POST /marswebapi/v1/scenarios`**

```json
{
  "createScenarioRequest": {
    "scenario": {
      "header": {
        "name": "Parallel Up 200bp",
        "description": "IRRBB parallel up shock - 200bp all tenors"
      },
      "setting": {},
      "content": {
        "regularScenario": {
          "swapCurveShift": [
            { "shiftWhat": "Currency=USD,Tenor=1D",  "shiftMode": { "absolute": {} }, "shiftValue": { "scalarShift": 200 } },
            { "shiftWhat": "Currency=USD,Tenor=1Y",  "shiftMode": { "absolute": {} }, "shiftValue": { "scalarShift": 200 } },
            { "shiftWhat": "Currency=USD,Tenor=5Y",  "shiftMode": { "absolute": {} }, "shiftValue": { "scalarShift": 200 } },
            { "shiftWhat": "Currency=USD,Tenor=10Y", "shiftMode": { "absolute": {} }, "shiftValue": { "scalarShift": 200 } }
          ]
        }
      }
    }
  }
}
```

The response contains a `scenarioId` that is referenced in all subsequent pricing requests.
The `setting: {}` object is required even when empty.

---

**Step 2a — Price a single deal under the scenario**

**`POST /marswebapi/v1/securitiesPricing`**

The `scenarioParameter` block is added alongside the standard `pricingParameter`. The base-case
fields are requested in `pricingParameter.requestedField`; the stressed fields are requested in
`scenarioParameter.requestedField`. Both are returned in the same response.

```json
{
  "securitiesPricingRequest": {
    "pricingParameter": {
      "valuationDate": "2026-03-29",
      "requestedField": ["MktVal", "MktValPortCcy", "DV01", "DV01PortCcy"]
    },
    "scenarioParameter": {
      "scenario": [{ "scenarioId": "<scenario-id>" }],
      "requestedField": ["MktVal", "MktValPortCcy", "DV01", "DV01PortCcy"]
    },
    "security": [
      { "identifier": { "bloombergDealId": "SLLVJ42Q Corp" }, "position": 1 }
    ]
  }
}
```

---

**Step 2b — Price an entire portfolio under the scenario**

**`POST /marswebapi/v1/portfolioPricing`**

Identical `scenarioParameter` syntax — works for portfolio pricing without any changes:

```json
{
  "portfolioPricingRequest": {
    "pricingParameter": {
      "valuationDate": "2026-03-29",
      "requestedField": ["MktVal", "MktValPortCcy", "DV01", "DV01PortCcy"]
    },
    "scenarioParameter": {
      "scenario": [{ "scenarioId": "<scenario-id>" }],
      "requestedField": ["MktVal", "MktValPortCcy", "DV01", "DV01PortCcy"]
    },
    "portfolioDescription": {
      "portfolioName": "MY_PORTFOLIO",
      "portfolioSource": "PORTFOLIO"
    }
  }
}
```

---

**Step 3 — Delete the scenario**

**`DELETE /marswebapi/v1/scenarios`**

Scenarios should always be deleted after use to avoid accumulating stale scenario objects.
Multiple scenario IDs can be deleted in a single call:

```json
{ "deleteScenariosRequest": { "scenarioIds": ["<id-1>", "<id-2>", "<id-3>"] } }
```

### `shiftWhat` filter syntax

The `shiftWhat` string uses `key=value` pairs to target specific curve dimensions:

| Example | Effect |
|---|---|
| `"Currency=USD"` | Shift all tenor points of the USD swap curve by the same amount |
| `"Currency=USD,Tenor=1Y"` | Shift only the 1Y point of the USD swap curve |
| `"Currency=COP,Tenor=5Y"` | Shift only the 5Y point of the COP swap curve |
| `"Currency=BRL,Tenor=10Y"` | Shift only the 10Y point of the BRL swap curve |

For a full IRRBB scenario, include one `swapCurveShift` node per currency per tenor that should
be shifted. Tenors not listed receive a zero shift.

### `shiftMode` options

| Mode | Key | Description |
|---|---|---|
| Absolute | `"absolute": {}` | Additive shift in basis points (e.g. `200` = +200bp) |
| Percent | `"percent": {}` | Multiplicative percentage shift of the current curve level |
| Override | `"override": {}` | Replace the curve rate at that tenor with the specified value |

### IRRBB standard scenarios (Basel)

| Scenario | Short tenors | Long tenors |
|---|---|---|
| Parallel Up | +200bp all | +200bp all |
| Parallel Down | -200bp all | -200bp all |
| Steepener | -100bp (short end) | +100bp (long end) |
| Flattener | +100bp (short end) | -100bp (long end) |
| Short Rate Up | +300bp (1D–1Y fading to 0 at 7Y+) | 0bp |
| Short Rate Down | -300bp (1D–1Y fading to 0 at 7Y+) | 0bp |
"""

st.divider()
with st.expander("About the MARS API", expanded=True):
    st.markdown(_API_DOCS)
