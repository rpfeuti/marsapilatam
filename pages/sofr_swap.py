"""
Page — SOFR Swap Market Value

Single-purpose calculator for USD SOFR OIS swaps: the user enters the
operation's characteristics (direction, notional, dates, fixed rate, spread,
curves) and gets the market value (MktVal, DV01, PV01, ...) via the
Bloomberg MARS API. Optionally saves the deal permanently to the Bloomberg
Terminal.

Reuses the existing "USD" template (IR.OIS.SOFR) from OIS_SWAP_SPECS and the
SwapPricingService — no new service layer is introduced.

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

import calendar
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, MarsApiError, PricingError, StructuringError
from configs.curves_catalog import CURVES_BY_LABEL
from configs.i18n import t
from configs.settings import DEMO_DATE, settings
from configs.stress_config import IRRBB_TENORS
from configs.swaps_config import (
    OIS_SWAP_SPECS,
    SWAP_DAY_COUNTS,
    SWAP_DIRECTIONS,
    SWAP_PAY_FREQUENCIES,
)
from services.stress_service import ScenarioOutput, StressResult, StressScenario, StressService
from services.swaps_service import SwapPricingService, SwapQuery, SwapResult

_SHOCK_BP = 100.0

_SPEC = OIS_SWAP_SPECS["USD"]  # IR.OIS.SOFR — SOFRRATE / S490

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("sofr.title"))
st.caption(t("sofr.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service — one instance per session (deal session is persistent)
# ---------------------------------------------------------------------------

_SVC_VERSION = "1"


@st.cache_resource(show_spinner=t("swaps.spinner_session"))
def get_service(v: str = _SVC_VERSION) -> SwapPricingService:
    return SwapPricingService.from_settings()


@st.cache_resource(show_spinner=False)
def get_stress_service(v: str = _SVC_VERSION) -> StressService:
    return StressService.from_settings()


def run_pricing(svc: SwapPricingService, query: SwapQuery) -> SwapResult:
    with st.spinner(t("swaps.spinner_pricing")):
        return svc.price(query)


_ALL_CURVE_LABELS = list(CURVES_BY_LABEL.keys())


def _curve_selectbox(label: str, default_id: str, key: str) -> str:
    """Render a searchable curve selectbox with inline label; return the selected curve ID."""
    default_label = next(
        (lbl for lbl, cid in CURVES_BY_LABEL.items() if cid == default_id),
        _ALL_CURVE_LABELS[0],
    )
    chosen = _lrow(label).selectbox(
        "",
        options=_ALL_CURVE_LABELS,
        index=_ALL_CURVE_LABELS.index(default_label),
        key=key,
        disabled=IS_DEMO,
        label_visibility="collapsed",
    )
    return CURVES_BY_LABEL[chosen]


def _lrow(label: str, ratio: tuple[int, int] = (1, 2)) -> st.delta_generator.DeltaGenerator:
    """Render a label in the left mini-column, return the right mini-column for the widget."""
    c_lbl, c_inp = st.columns(ratio)
    c_lbl.markdown(
        f"<p style='margin-top:8px;font-size:0.85em;color:#aaa'>{label}</p>",
        unsafe_allow_html=True,
    )
    return c_inp


def _get_solve_targets(deal_type: str) -> list[str]:
    """Return SOLVABLE field names for *deal_type*, cached in session_state."""
    cache_key = f"_solve_targets_{deal_type}"
    if cache_key not in st.session_state:
        svc = get_service()
        st.session_state[cache_key] = svc.fetch_solvable_fields(deal_type)
    return st.session_state[cache_key]  # type: ignore[return-value]


def _tenor_to_maturity(effective: date, years: int) -> date:
    target_year = effective.year + years
    day = min(effective.day, calendar.monthrange(target_year, effective.month)[1])
    return date(target_year, effective.month, day)


def _fmt(raw: str, decimals: int = 2) -> str:
    """Format a numeric string with thousand separators and fixed decimals."""
    try:
        return f"{float(raw):,.{decimals}f}"
    except (ValueError, TypeError):
        return raw if raw else "—"


def _to_float(raw: str) -> float:
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def _shock_scenarios() -> list[StressScenario]:
    """+100bp / -100bp parallel shift of the USD SOFR swap curve across all IRRBB tenors."""
    return [
        StressScenario(
            name=t("sofr.shock_up_label"),
            currency="USD",
            tenor_shifts={tenor: _SHOCK_BP for tenor in IRRBB_TENORS},
        ),
        StressScenario(
            name=t("sofr.shock_down_label"),
            currency="USD",
            tenor_shifts={tenor: -_SHOCK_BP for tenor in IRRBB_TENORS},
        ),
    ]


def _render_shock_chart(base_mtm: float, shock_result: StressResult) -> None:
    rows: list[dict[str, str]] = [{
        t("sofr.shock_col_scenario"): t("sofr.shock_base_label"),
        t("sofr.shock_col_mtm"): f"{base_mtm:,.2f}",
        t("sofr.shock_col_delta"): "—",
    }]
    names = [t("sofr.shock_base_label")]
    deltas = [0.0]

    for so in shock_result.scenario_results:
        mtm = _to_float(so.metrics.get("MktVal", "0"))
        delta = mtm - base_mtm
        rows.append({
            t("sofr.shock_col_scenario"): so.name,
            t("sofr.shock_col_mtm"): f"{mtm:,.2f}",
            t("sofr.shock_col_delta"): f"{delta:+,.2f}",
        })
        names.append(so.name)
        deltas.append(delta)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    colors = ["#95a5a6"] + ["#e74c3c" if d < 0 else "#2ecc71" for d in deltas[1:]]
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=[base_mtm] + [base_mtm + d for d in deltas[1:]],
            marker_color=colors,
            text=[f"{v:,.0f}" for v in [base_mtm] + [base_mtm + d for d in deltas[1:]]],
            textposition="outside",
        )
    ])
    fig.update_layout(
        title=t("sofr.shock_header"),
        yaxis_title=t("sofr.shock_col_mtm"),
        showlegend=False,
        height=380,
        margin=dict(t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_shock_simulation(result: SwapResult, valuation_date: date) -> None:
    """Reprice the swap under a +100bp / -100bp parallel USD SOFR curve shock."""
    base_mtm = _to_float(result.metrics.get("MktVal", "0"))

    st.markdown("---")
    st.markdown(f"**{t('sofr.shock_header')}**")
    st.caption(t("sofr.shock_caption"))

    if result.deal_handle:
        try:
            stress_svc = get_stress_service()
            with st.spinner(t("sofr.shock_spinner")):
                shock_result = stress_svc.run_stress_test_on_handle(
                    result.deal_handle, _shock_scenarios(), valuation_date,
                )
            if not shock_result.ok:
                st.error(t("sofr.shock_error", error=shock_result.error or "Unknown error"))
                return
            _render_shock_chart(base_mtm, shock_result)
        except MarsApiError as e:
            st.error(t("sofr.shock_error", error=str(e)))
    else:
        # Demo mode: no live dealHandle to run scenarios against — approximate
        # linearly from the base DV01 (dMktVal ≈ -DV01 * shock_bp).
        dv01 = _to_float(result.metrics.get("DV01", "0"))
        demo_result = StressResult(
            base_metrics=result.metrics,
            scenario_results=[
                ScenarioOutput(
                    name=sc.name,
                    tenor_shifts=sc.tenor_shifts,
                    metrics={"MktVal": f"{base_mtm - dv01 * next(iter(sc.tenor_shifts.values())):.2f}"},
                )
                for sc in _shock_scenarios()
            ],
        )
        st.info(t("sofr.shock_demo_note"), icon="🔒")
        _render_shock_chart(base_mtm, demo_result)


# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------

col_op, col_val = st.columns(2)

with col_op:
    st.markdown(f"**{t('sofr.section_operation')}**")

    direction = _lrow(t("swaps.direction_label")).selectbox(
        "", options=SWAP_DIRECTIONS,
        index=SWAP_DIRECTIONS.index("Receive"),
        key="sofr_direction",
        label_visibility="collapsed",
    )
    notional = _lrow(t("swaps.notional_label")).number_input(
        "",
        value=float(_SPEC.notional),
        min_value=1.0,
        step=1_000_000.0,
        format="%.0f",
        key="sofr_notional",
        label_visibility="collapsed",
    )
    effective = _lrow(t("swaps.effective_label")).date_input(
        "",
        value=date.today() if not IS_DEMO else DEMO_DATE,
        disabled=IS_DEMO,
        key="sofr_effective",
        label_visibility="collapsed",
    )
    maturity = _lrow(t("swaps.maturity_label")).date_input(
        "",
        value=_tenor_to_maturity(effective, 5),
        key="sofr_maturity",
        label_visibility="collapsed",
    )
    fixed_rate_str = _lrow(t("swaps.fixed_rate_label")).text_input(
        "",
        value="",
        placeholder="e.g. 4.25",
        key="sofr_fixed_rate",
        disabled=IS_DEMO,
        label_visibility="collapsed",
    )
    spread_val = _lrow(t("swaps.spread_label")).number_input(
        "",
        value=0.0,
        step=1.0,
        format="%.1f",
        key="sofr_spread",
        disabled=IS_DEMO,
        label_visibility="collapsed",
    )
    pay_frequency = _lrow(t("swaps.pay_freq_label")).selectbox(
        "",
        options=SWAP_PAY_FREQUENCIES,
        index=SWAP_PAY_FREQUENCIES.index(_SPEC.pay_frequency)
        if _SPEC.pay_frequency in SWAP_PAY_FREQUENCIES
        else 0,
        key="sofr_pay_freq",
        label_visibility="collapsed",
    )
    day_count = _lrow(t("swaps.day_count_label")).selectbox(
        "",
        options=SWAP_DAY_COUNTS,
        index=SWAP_DAY_COUNTS.index(_SPEC.day_count) if _SPEC.day_count in SWAP_DAY_COUNTS else 0,
        key="sofr_day_count",
        label_visibility="collapsed",
    )

with col_val:
    st.markdown(f"**{t('sofr.section_valuation')}**")

    curve_date = _lrow(t("swaps.curve_date_label")).date_input(
        "",
        value=DEMO_DATE if IS_DEMO else date.today(),
        disabled=IS_DEMO,
        key="sofr_curve_date",
        label_visibility="collapsed",
    )
    valuation_date = _lrow(t("swaps.valuation_date_label")).date_input(
        "",
        value=DEMO_DATE if IS_DEMO else date.today(),
        disabled=IS_DEMO,
        key="sofr_valuation_date",
        label_visibility="collapsed",
    )
    discount_curve_id = _curve_selectbox(
        t("swaps.discount_curve_label"), _SPEC.discount_curve, "sofr_discount_curve",
    )
    forward_curve_id = _curve_selectbox(
        t("swaps.forward_curve_label"), _SPEC.forward_curve, "sofr_forward_curve",
    )
    _solve_targets = _get_solve_targets(_SPEC.deal_type)
    solve_for = _lrow(t("swaps.solve_for_label")).selectbox(
        "",
        options=_solve_targets,
        key="sofr_solve_for",
        label_visibility="collapsed",
    )

    st.markdown("")
    calc_clicked = st.button(
        t("sofr.button_calculate"),
        type="primary",
        use_container_width=True,
        key="sofr_calc_btn",
    )

    if not IS_DEMO:
        save_clicked = st.button(
            t("common.button_save_deal"),
            use_container_width=True,
            key="sofr_save_btn",
        )
    else:
        save_clicked = False

    _saved_id = st.session_state.get("_saved_deal_id_sofr")
    if _saved_id:
        st.success(t("common.save_success", deal_id=_saved_id))

    if IS_DEMO:
        st.divider()
        st.markdown(t("common.demo_cta_sidebar"))

# ---------------------------------------------------------------------------
# Build query, price / save
# ---------------------------------------------------------------------------

if calc_clicked or save_clicked:
    fixed_rate: float | None = None
    _valid = True
    if fixed_rate_str.strip():
        try:
            fixed_rate = float(fixed_rate_str.strip())
        except ValueError:
            st.error(f"Invalid fixed rate: {fixed_rate_str!r}")
            _valid = False

    if _valid:
        query = SwapQuery(
            key="USD",
            swap_type="OIS",
            direction=direction,
            effective_date=effective,
            maturity_date=maturity,
            valuation_date=valuation_date,
            curve_date=curve_date,
            notional=notional,
            forward_curve=forward_curve_id,
            discount_curve=discount_curve_id,
            float_index=_SPEC.float_index,
            pay_frequency=pay_frequency,
            day_count=day_count,
            fixed_rate=fixed_rate,
            spread=float(spread_val),
            solve_for=solve_for or "Coupon",
        )

        if save_clicked:
            try:
                svc = get_service()
                with st.spinner(t("common.spinner_saving")):
                    deal_id = svc.save_deal(query)
                st.session_state["_saved_deal_id_sofr"] = deal_id
                st.rerun()
            except (StructuringError, MarsApiError) as e:
                st.error(t("common.save_error", error=e))
        else:
            try:
                svc = get_service()
                result = run_pricing(svc, query)

                if not result.ok:
                    st.error(result.error)
                elif not result.metrics and result.par_rate is None:
                    st.warning(t("swaps.warning_no_result"))
                else:
                    st.markdown("---")
                    m = result.metrics
                    cols = st.columns(7)

                    solved_label = (
                        t("swaps.result_par_cpn") if solve_for in ("Coupon", "FixedRate") else f"Par {solve_for}"
                    )
                    par_str = (
                        f"{result.par_rate:.6f}" if result.par_rate is not None else _fmt(m.get("MktPx", ""), 6)
                    )
                    cols[0].metric(solved_label, par_str)
                    cols[1].metric(t("swaps.result_npv"),     _fmt(m.get("MktVal",           "")))
                    cols[2].metric(t("swaps.result_dv01"),     _fmt(m.get("DV01",            "")))
                    cols[3].metric(t("swaps.result_pv01"),     _fmt(m.get("PV01",            "")))
                    cols[4].metric(t("swaps.result_bp_value"), _fmt(m.get("BpValue", m.get("DV01", ""))))
                    cols[5].metric(t("swaps.result_premium"),  _fmt(m.get("MktPx",           "")))
                    cols[6].metric(t("swaps.result_accrued"),  _fmt(m.get("AccruedInterest", "")))

                    _render_shock_simulation(result, valuation_date)
            except StructuringError as e:
                st.error(t("swaps.error_structuring", error=e))
            except PricingError as e:
                st.error(t("swaps.error_pricing", error=e))
            except IpNotWhitelistedError:
                st.error("🔒 Your IP is not whitelisted for the Bloomberg MARS API. "
                         "Please contact your Bloomberg representative to whitelist your current IP.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
else:
    st.info(t("sofr.info_idle"))

# ---------------------------------------------------------------------------
# Demo CTA at page bottom
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")
