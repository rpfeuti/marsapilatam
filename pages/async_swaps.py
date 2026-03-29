"""
Page — SOFR Curve Bootstrap (Async Swaps)

Builds a SOFR zero curve from user-provided par rates by:
  1. Concurrently structuring SOFR OIS deals via MARS API (async) to extract
     exact fixed-leg AccrualSchedules (payment dates + ACT/360 year fractions).
  2. Running a pure-Python recursive bootstrap to derive discount factors P(0,T)
     and continuously-compounded ACT/365 zero rates — identical convention to S490.
  3. Downloading Bloomberg's S490 zero and discount factor curves via CurvesService
     for side-by-side comparison.

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

import asyncio
import math
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, MarsApiError, StructuringError
from configs.curves_config import CurveType
from configs.i18n import t
from configs.settings import DEMO_DATE, settings
from services.bootstrap_service import (
    SOFR_DEFAULT_PAR_RATES,
    SOFR_TENORS,
    BootstrapResult,
    BootstrapService,
    TenorSchedule,
)
from services.curves_service import CurveQuery, XMarketCurveService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("async_swaps.title"))
st.caption(t("async_swaps.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service instances
# ---------------------------------------------------------------------------

_SVC_VERSION = "1"


@st.cache_resource(show_spinner=False)
def _get_bootstrap_service(v: str = _SVC_VERSION) -> BootstrapService:
    return BootstrapService.from_settings()


@st.cache_data(ttl=300, show_spinner=False)
def _load_live_par_rates(as_of_date: date) -> dict[str, float]:
    """Fetch SOFR OIS par rates from BLPAPI for a given date (cached 5 min).

    Uses live BDP for today and historical BDH for past dates so that the
    par rates always match the selected valuation date.
    """
    return BootstrapService.from_settings().get_sofr_par_rates(as_of_date)


# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

st.subheader(t("async_swaps.section_inputs"))

col_date, _, _ = st.columns(3)
with col_date:
    valuation_date: date = st.date_input(
        t("async_swaps.label_valuation_date"),
        value=DEMO_DATE if IS_DEMO else date.today(),
        disabled=IS_DEMO,
    )  # type: ignore[assignment]

# Par rate editor — one row per tenor, with Include toggle and editable rate
_live_rates = _load_live_par_rates(valuation_date)
_default_rows = [
    {
        t("async_swaps.label_include"):   True,
        t("async_swaps.label_tenor"):     tenor,
        t("async_swaps.label_par_rate"):  _live_rates.get(tenor, SOFR_DEFAULT_PAR_RATES[tenor]),
    }
    for tenor in SOFR_TENORS
]

edited_df = st.data_editor(
    pd.DataFrame(_default_rows),
    width="content",
    num_rows="fixed",
    disabled=[t("async_swaps.label_tenor")],
    column_config={
        t("async_swaps.label_include"):  st.column_config.CheckboxColumn(width="small"),
        t("async_swaps.label_tenor"):    st.column_config.TextColumn(width="small", disabled=True),
        t("async_swaps.label_par_rate"): st.column_config.NumberColumn(
            min_value=0.0, max_value=30.0, step=0.01, format="%.4f", width="medium",
        ),
    },
    key="par_rate_editor",
)

# Parse selected tenors and par rates from the editor
_include_col   = t("async_swaps.label_include")
_tenor_col     = t("async_swaps.label_tenor")
_par_rate_col  = t("async_swaps.label_par_rate")

selected_rows = edited_df[edited_df[_include_col] == True]  # noqa: E712
selected_tenors: list[str] = selected_rows[_tenor_col].tolist()
par_rates_pct:  dict[str, float] = dict(
    zip(selected_rows[_tenor_col], selected_rows[_par_rate_col])
)

_, col_btn, _ = st.columns([2, 1, 2])
with col_btn:
    run_clicked = st.button(
        t("async_swaps.button_bootstrap"),
        type="primary",
        use_container_width=True,
        disabled=len(selected_tenors) < 2,
    )

# ---------------------------------------------------------------------------
# S490 interpolation helper (used post-bootstrap)
# ---------------------------------------------------------------------------


def _interpolate_s490(df: pd.DataFrame, date_col: str, val_col: str, target: date) -> float | None:
    """Log-linearly interpolate an S490 series to a target date."""
    if df is None or df.empty:
        return None
    try:
        dates = pd.to_datetime(df[date_col]).dt.date.tolist()
        vals  = df[val_col].tolist()
        if not dates:
            return None
        if target in dates:
            return float(vals[dates.index(target)])
        before = [(d, v) for d, v in zip(dates, vals) if d <= target]
        after  = [(d, v) for d, v in zip(dates, vals) if d > target]
        if not before:
            return float(after[0][1])
        if not after:
            return float(before[-1][1])
        d1, v1 = before[-1]
        d2, v2 = after[0]
        span = (d2 - d1).days
        gap  = (target - d1).days
        if span > 0 and v1 > 0 and v2 > 0:
            return float(v1 * math.exp(math.log(v2 / v1) * gap / span))
        return float(v1)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Results — only rendered after Bootstrap Curve is clicked
# ---------------------------------------------------------------------------

if not run_clicked:
    st.info(t("async_swaps.info_idle"))
else:
    svc = _get_bootstrap_service()

    # Step 1 — fetch payment schedules from MARS (async, parallel)
    schedules: dict[str, TenorSchedule] = {}

    if IS_DEMO:
        with st.spinner(t("async_swaps.spinner_schedules", n=len(selected_tenors))):
            schedules = svc.build_demo_schedules(selected_tenors, valuation_date)
    else:
        try:
            with st.spinner(t("async_swaps.spinner_schedules", n=len(selected_tenors))):
                schedules = asyncio.run(
                    svc.fetch_schedules_async(selected_tenors, valuation_date)
                )
        except StructuringError as exc:
            st.error(t("async_swaps.error_structuring", error=exc))
            st.stop()
        except IpNotWhitelistedError:
            st.error(
                "Your IP is not whitelisted for the Bloomberg MARS API. "
                "Please contact your Bloomberg representative."
            )
            st.stop()
        except MarsApiError as exc:
            st.error(t("async_swaps.error_structuring", error=exc))
            st.stop()

    # Step 2 — bootstrap
    with st.spinner(t("async_swaps.spinner_bootstrap")):
        result: BootstrapResult = svc.bootstrap(par_rates_pct, schedules, valuation_date)

    if not result.ok:
        st.error(result.error)
        st.stop()

    # Step 3 — fetch S490 from CurvesService for comparison
    maturity_dates = [pt.maturity_date for pt in result.points]
    s490_zero_df: pd.DataFrame | None = None

    try:
        with st.spinner(t("async_swaps.spinner_s490")):
            _curve_svc = XMarketCurveService.from_settings(valuation_date)
            _query_z = CurveQuery(
                curve_id="S490",
                curve_type=CurveType.ZERO,
                as_of=valuation_date,
                requested_dates=tuple(maturity_dates),
            )
            s490_zero_df = _curve_svc.get_curve(_query_z)
    except Exception as exc:
        st.warning(t("async_swaps.error_s490", error=exc))

    # Build comparison DataFrame
    rows = []
    for pt in result.points:
        row: dict = {
            t("async_swaps.col_tenor"):    pt.tenor,
            t("async_swaps.col_maturity"): pt.maturity_date.isoformat(),
            t("async_swaps.col_days"):     pt.days_to_maturity,
            t("async_swaps.col_par_rate"): round(pt.par_rate_pct, 4),
            t("async_swaps.col_df_ours"):  round(pt.discount_factor, 6),
            t("async_swaps.col_z_ours"):   round(pt.zero_rate_pct, 4),
            t("async_swaps.col_z_s490"):   None,
            t("async_swaps.col_diff_z"):   None,
        }
        rows.append(row)

    compare_df = pd.DataFrame(rows)

    if s490_zero_df is not None and not s490_zero_df.empty:
        date_col_z = "date"
        rate_col_z = "rate"
        if date_col_z in s490_zero_df.columns and rate_col_z in s490_zero_df.columns:
            for i, pt in enumerate(result.points):
                z_s490_raw = _interpolate_s490(s490_zero_df, date_col_z, rate_col_z, pt.maturity_date)
                if z_s490_raw is not None:
                    z_s490_pct = z_s490_raw * 100
                    compare_df.at[i, t("async_swaps.col_z_s490")] = round(z_s490_pct, 4)
                    diff = pt.zero_rate_pct - z_s490_pct
                    compare_df.at[i, t("async_swaps.col_diff_z")]  = round(diff * 100, 1)

    # Chart
    _years = [pt.days_to_maturity / 365.0 for pt in result.points]

    def _make_zero_rate_chart() -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=_years,
            y=[pt.par_rate_pct for pt in result.points],
            mode="lines+markers",
            name=t("async_swaps.legend_par"),
            line=dict(dash="dash", width=1.5, color="#aaaaaa"),
            marker=dict(size=5),
        ))
        fig.add_trace(go.Scatter(
            x=_years,
            y=[pt.zero_rate_pct for pt in result.points],
            mode="lines+markers",
            name=t("async_swaps.legend_bootstrap"),
            line=dict(width=2.5, color="#1f77b4"),
            marker=dict(size=7),
        ))
        if s490_zero_df is not None and t("async_swaps.col_z_s490") in compare_df.columns:
            s490_vals = compare_df[t("async_swaps.col_z_s490")].tolist()
            if any(v is not None for v in s490_vals):
                fig.add_trace(go.Scatter(
                    x=_years,
                    y=s490_vals,
                    mode="lines+markers",
                    name=t("async_swaps.legend_s490"),
                    line=dict(width=2, dash="dot", color="#ff7f0e"),
                    marker=dict(size=6, symbol="diamond"),
                ))
        fig.update_layout(
            title=t("async_swaps.chart_zero_title"),
            xaxis_title=t("async_swaps.chart_x_label"),
            yaxis_title=t("async_swaps.chart_y_zero"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            margin=dict(t=80),
        )
        return fig

    # Output tabs
    tab_zero, tab_detail = st.tabs([
        t("async_swaps.tab_zero_rates"),
        t("async_swaps.tab_detail"),
    ])
    with tab_zero:
        st.plotly_chart(_make_zero_rate_chart(), use_container_width=True)
    with tab_detail:
        st.dataframe(compare_df, width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Documentation — always visible
# ---------------------------------------------------------------------------

st.divider()
with st.expander(t("async_swaps.docs_title"), expanded=True):

    st.subheader(t("async_swaps.docs_walkthrough_header"))
    st.markdown(r"""
This tool builds a SOFR zero curve from scratch using only market par rates and
exact cashflow schedules obtained from Bloomberg.
Here is every step that runs when you click **Bootstrap Curve**:

**Step 0 — Select a valuation date.**
Choose any past business day or today.  The date drives everything that follows:
settlement date, accrual schedules, market rates, and the Bloomberg S490 comparison.

**Step 1 — Fetch par rates.**
The overnight SOFR fixing (`SOFRRATE Index`) and the 32 SOFR OIS swap rates
(`YCSW0490 Index` members) are pulled from Bloomberg BLPAPI.
- For **today's date**: a live `ReferenceDataRequest` (BDP) is used.
- For a **past date**: a `HistoricalDataRequest` (BDH) is used, so the input rates
  match exactly what Bloomberg's S490 was built from on that day.

You can override any rate in the editor table above before clicking Bootstrap.

**Step 2 — Fetch accrual schedules.**
For each selected tenor a temporary `IR.OIS.SOFR` deal is structured via the
Bloomberg MARS API — all tenors fire concurrently (`asyncio.gather`).
MARS returns the **exact fixed-leg accrual schedule**: start date, end date,
and ACT/360 year fraction for every coupon period, respecting the full
NYSE/SIFMA holiday calendar and the 2-business-day payment delay convention.
No pricing is performed; MARS is used purely as a **calendar engine**.

**Step 3 — Compute the T+2 settlement discount factor** $P_{\text{settle}}$.
SOFR OIS swaps settle T+2, so the first cashflow date is two business days
after the trade date.  The overnight rate bridges that gap (see T+2 section).

**Step 4 — Bootstrap 1W → 50Y.**
Starting from the shortest tenor, each par rate equation (NPV = 0) is solved
analytically for the unknown discount factor $P(0, T_n)$.  Intermediate coupon
dates that fall between already-known pillars are filled by log-linear
interpolation on discount factors (= step-forward, piecewise-constant forwards).

**Step 5 — Post-process the 1D node.**
The 1D maturity falls inside the first swap segment.  Its discount factor is
read off the curve by log-linear interpolation between $P_{\text{settle}}$ and
$P(0, T_{1\text{W,end}})$, matching Bloomberg S490's step-forward method.

**Step 6 — Convert to zero rates.**
Each discount factor is converted to a continuously compounded ACT/365 zero rate,
using calendar days from the **trade date** to match Bloomberg S490's display convention.
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_glossary_header"))
    st.markdown(r"""
| Symbol | Meaning |
|:-------|:--------|
| $T_0$ | Trade date (valuation date) — the date you select in the input |
| $T_{\text{settle}}$ | Settlement date = $T_0$ + 2 business days |
| $\Delta_{\text{gap}}$ | Calendar days from $T_0$ to $T_{\text{settle}}$ (typically 2; 4 for a Friday) |
| $r_{\text{ON}}$ | 1D SOFR overnight rate, in **decimal** (e.g. 4.32 % → 0.04320) |
| $c_n$ | Par rate for tenor $n$, in **decimal** |
| $\tau_i$ | ACT/360 year fraction for accrual period $i$ = $(\text{end}_i - \text{start}_i)\text{.days} \;/\; 360$ |
| $T_i$ | Accrual-end date of period $i$ — the **pillar** where $P(0,T_i)$ is anchored |
| $P(0,T)$ | Discount factor from $T_0$ to date $T$ — present value of \$1 paid at $T$ |
| $z(T)$ | Continuously compounded zero rate (ACT/365, in %) |
| $\alpha$ | Interpolation weight between two neighbouring pillars |

> **Day-count note** — coupon $\tau$ uses **ACT/360** (SOFR OIS contract convention);
> zero rates use **ACT/365** (Bloomberg S490 display convention).  These are two
> different counts for two different purposes.
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_settlement_header"))
    st.markdown(r"""
SOFR OIS swaps settle **T+2 business days** after the trade date.  The first
accrual period therefore starts on $T_{\text{settle}}$, not on $T_0$.
To anchor the entire curve at $T_0$, we need a discount factor for the gap:

$$\boxed{P_{\text{settle}} \;=\; P(0,\,T_{\text{settle}}) \;=\; \frac{1}{1 + r_{\text{ON}} \times \Delta_{\text{gap}} / 360}}$$

This uses **simple interest** (money-market convention, ACT/360) over the overnight rate.

**Concrete example** — trade date = Monday 2026-02-10:

| | Value |
|:---|:---|
| $T_{\text{settle}}$ | Wednesday 2026-02-12 |
| $\Delta_{\text{gap}}$ | 2 calendar days |
| $r_{\text{ON}}$ | 3.6500 % → 0.036500 |
| $P_{\text{settle}}$ | $1\,/\,(1 + 0.036500 \times 2/360) = 1\,/\,1.000203 = 0.999797$ |

**Friday example** — trade date = Friday 2026-03-27, settle = Tuesday 2026-03-31:
$\Delta_{\text{gap}} = 4$ calendar days (weekend skipped by the T+2 business-day rule).

> $P_{\text{settle}}$ feeds into the **numerator** of every bootstrap equation below,
> ensuring that all discount factors and zero rates are measured from $T_0$.
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_math_header"))
    st.markdown(r"""
### Why NPV = 0 gives us P(0, T)

A par SOFR OIS swap has zero net present value at inception.  Its two legs are:

- **Floating leg PV** — the compounded SOFR payments plus the notional exchange
  simplify (under no-arbitrage) to: $\text{PV}_{\text{float}} = P_{\text{settle}} - P(0, T_n)$
- **Fixed leg PV** — the fixed coupon $c_n$ paid on each period:
  $\text{PV}_{\text{fixed}} = c_n \displaystyle\sum_{i=1}^{n} P(0, T_i)\,\tau_i$

Setting $\text{PV}_{\text{float}} = \text{PV}_{\text{fixed}}$ and isolating the
**unknown** last discount factor $P(0, T_n)$:

$$P_{\text{settle}} - P(0, T_n) \;=\; c_n \sum_{i=1}^{n} P(0, T_i)\,\tau_i$$

$$\Downarrow$$

$$\boxed{P(0, T_n) \;=\; \frac{P_{\text{settle}} \;-\; c_n \displaystyle\sum_{i=1}^{n-1} P(0, T_i)\,\tau_i}{1 + c_n\,\tau_n}}$$

All $P(0, T_i)$ for $i < n$ are already known from shorter tenors (or interpolated).

---

### Single-period swap (all sub-annual tenors: 1W, 2W, …, 11M)

A 1M swap has only one accrual period, so the sum $\sum_{i<n}$ is empty:

$$\boxed{P(0, T_1) \;=\; \frac{P_{\text{settle}}}{1 + c_1\,\tau_1}}$$

**Worked example** — tenor = 1W, trade date = 2026-02-10:

| | Value |
|:---|:---|
| Accrual start | 2026-02-12 (= $T_{\text{settle}}$) |
| Accrual end $T_1$ | 2026-02-19 |
| $\tau_1$ | $7\,/\,360 = 0.019\,444$ |
| $c_1$ | 3.6477 % → 0.036477 |
| $P_{\text{settle}}$ | 0.999797 |
| $P(0, T_1)$ | $0.999797\,/\,(1 + 0.036477 \times 0.019\,444) = 0.999797\,/\,1.000709 = \mathbf{0.999089}$ |

---

### Multi-period swap (1Y and above, annual coupons)

A 2Y SOFR OIS has two annual periods.  The 1Y pillar $P(0, T_1)$ is already
known; we solve for the 2Y pillar $P(0, T_2)$:

$$P(0, T_2) = \frac{P_{\text{settle}} - c_2 \cdot P(0, T_1)\,\tau_1}{1 + c_2\,\tau_2}$$

For a 3Y swap with three annual periods, $P(0,T_1)$ and $P(0,T_2)$ are both
already known, and so on recursively.  If an intermediate coupon date does not
coincide with an existing pillar (which can happen for off-grid dates), its
$P(0,T_i)$ is obtained by **log-linear interpolation** (see next section).
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_interpolation_header"))
    st.markdown(r"""
Whenever the bootstrap needs $P(0,t)$ for a date $t$ that falls **between** two
already-known pillars $T_1 < t < T_2$, it interpolates log-linearly on the
discount factors:

$$\alpha = \frac{(t - T_1)\text{.days}}{(T_2 - T_1)\text{.days}}$$

$$\boxed{P(0,t) \;=\; P(0,T_1)^{\,1-\alpha} \cdot P(0,T_2)^{\,\alpha}}$$

**Why this equals step-forward (piecewise-constant forwards)**

Taking the log: $\ln P(0,t) = (1-\alpha)\,\ln P(0,T_1) + \alpha\,\ln P(0,T_2)$,
i.e. $\ln P$ is **linear in time** between the two pillars.  The instantaneous
forward rate is $f(t) = -d[\ln P(0,t)]/dt$, which is **constant** on each segment.
That is the definition of piecewise-constant forwards — the same setting Bloomberg
labels "Step Forward (Cont)" in the S490 curve parameters.

The three descriptions are equivalent:

| Name | Domain | What is linear |
|:-----|:-------|:--------------|
| Log-linear on DFs | Discount factor | $\ln P$ vs time |
| Step-forward | Forward rate | $f(t)$ is flat per segment |
| Bloomberg "Step Forward (Cont)" | UI label | same algorithm |
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_oneday_header"))
    st.markdown(r"""
The 1D tenor is **not** bootstrapped as a par swap.  The reason: the 1D OIS
maturity falls inside the very first segment $[T_{\text{settle}},\, T_{1\text{W,end}}]$,
which is a single flat-forward segment.  Treating it as an independent swap
would over-constrain the curve and introduce an artificial kink.

Bloomberg S490 handles this the same way: the 1D node is an **interpolated point**
on the short end of the curve, not an independent input.

**Algorithm** — after all 1W–50Y pillars are built:

$$\alpha_{1D} = \frac{(T_{1D} - T_{\text{settle}})\text{.days}}{(T_{1\text{W,end}} - T_{\text{settle}})\text{.days}}$$

$$\boxed{P(0, T_{1D}) = P_{\text{settle}}^{\,1-\alpha_{1D}} \cdot P(0,\,T_{1\text{W,end}})^{\,\alpha_{1D}}}$$

**Worked example** — trade date = 2026-02-10:

| | Value |
|:---|:---|
| $T_{\text{settle}}$ | 2026-02-12 |
| $T_{1D}$ (accrual end of 1D swap) | 2026-02-13 |
| $T_{1\text{W,end}}$ | 2026-02-19 |
| $\alpha_{1D}$ | $(13-12)\text{.days}\,/\,(19-12)\text{.days} = 1/7 = 0.1429$ |
| $P_{\text{settle}}$ | 0.999797 |
| $P(0, T_{1\text{W,end}})$ | 0.999089 |
| $P(0, T_{1D})$ | $0.999797^{0.8571} \times 0.999089^{0.1429} \approx \mathbf{0.999696}$ |
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_zerorates_header"))
    st.markdown(r"""
Once every discount factor $P(0,T)$ is known, the zero rate is:

$$\boxed{z(T) \;=\; -\,\frac{\ln P(0,T) \times 365}{(T - T_0)\text{.days}} \times 100\%}$$

Key points:
- **Continuous compounding** — no compounding frequency adjustment needed.
- **ACT/365 day count** — calendar days from the **trade date** $T_0$, divided
  by 365 (not 360).  This matches Bloomberg S490's display convention.
- The result is in **percent** (multiply by 100).

**Worked example** using the 1W pillar from above:

| | Value |
|:---|:---|
| $P(0, T_{1\text{W,end}})$ | 0.999089 |
| $(T_{1\text{W,end}} - T_0)\text{.days}$ | $(2026\text{-}02\text{-}19 - 2026\text{-}02\text{-}10)\text{.days} = 9$ |
| $z$ | $-\,\ln(0.999089) \times 365\,/\,9 \times 100 = 0.000912 \times 365\,/\,9 \times 100 = \mathbf{3.698\%}$ |

**1D example**:

| | Value |
|:---|:---|
| $P(0, T_{1D})$ | 0.999696 |
| $(T_{1D} - T_0)\text{.days}$ | $(2026\text{-}02\text{-}13 - 2026\text{-}02\text{-}10)\text{.days} = 3$ |
| $z$ | $-\,\ln(0.999696) \times 365\,/\,3 \times 100 = 0.000304 \times 365\,/\,3 \times 100 = \mathbf{3.699\%}$ |
""")

    # ------------------------------------------------------------------
    st.subheader(t("async_swaps.docs_tickers_header"))
    st.markdown("""
| Tenor | Bloomberg Ticker | Notes |
|:------|:----------------|:------|
| 1D | `SOFRRATE Index` | SOFR overnight fixing |
| 1W, 2W, 3W | `USOSFR1Z`, `USOSFR2Z`, `USOSFR3Z BGN Curncy` | Z suffix = weeks |
| 1M–11M | `USOSFRA`–`USOSFRK BGN Curncy` | A=1M, B=2M, …, K=11M |
| 18M | `USOSFR1F BGN Curncy` | 18-month OIS |
| 1Y–9Y | `USOSFR1`–`USOSFR9 BGN Curncy` | Annual OIS |
| 10Y–50Y | `USOSFR10`–`USOSFR50 BGN Curncy` | Long-end OIS |

Par rates are fetched via `YCSW0490 Index` → `INDX_MEMBERS` (32 swap tickers) plus
`SOFRRATE Index` for the 1D anchor.  Field: `PX_LAST` (% p.a., no rescaling needed).

For **historical valuation dates**, a `HistoricalDataRequest` (BDH) is sent instead
of the standard `ReferenceDataRequest` (BDP).  The index membership
(`INDX_MEMBERS`) is always fetched current — the S490 constituent list is stable.
""")

    st.subheader(t("async_swaps.docs_calendar_header"))
    st.markdown(t("async_swaps.docs_calendar_body"))

