"""
Page — IR Swaps (OIS & XCCY)

Structure and price interest rate swaps via the Bloomberg MARS API.
Layout mirrors Bloomberg SWPM: Leg 1 | Leg 2 | Valuation Settings, with
results displayed as metric cards below.

Two tabs:
  OIS  — fixed vs floating, same currency (COP, USD, BRL, MXN, CLP, EUR)
  XCCY — USD leg vs local-currency OIS leg  (USD/COP, USD/BRL, …)
"""

from __future__ import annotations

from datetime import date
from typing import Literal

import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, PricingError, StructuringError
from configs.curves_catalog import CURVES_BY_LABEL
from configs.i18n import t
from configs.settings import settings
from configs.swaps_config import (
    OIS_BY_LABEL,
    OIS_LABELS,
    OIS_SWAP_SPECS,
    SWAP_DAY_COUNTS,
    SWAP_DIRECTIONS,
    SWAP_PAY_FREQUENCIES,
    SWAP_SOLVE_TARGETS,
    SWAP_TENORS,
    XCCY_BY_LABEL,
    XCCY_LABELS,
    XCCY_SWAP_SPECS,
)
from services.swaps_service import SwapPricingService, SwapQuery, SwapResult

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("swaps.title"))
st.caption(t("swaps.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service — one instance per session (deal session is persistent)
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=t("swaps.spinner_session"))
def get_service() -> SwapPricingService:
    return SwapPricingService.from_settings()


# ---------------------------------------------------------------------------
# Cached pricing — re-runs only when inputs change
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=t("swaps.spinner_pricing"))
def run_pricing(_svc: SwapPricingService, query: SwapQuery) -> SwapResult:
    return _svc.price(query)


# ---------------------------------------------------------------------------
# Shared curve label list (searchable)
# ---------------------------------------------------------------------------

_ALL_CURVE_LABELS = list(CURVES_BY_LABEL.keys())


def _curve_selectbox(label: str, default_id: str, key: str) -> str:
    """Render a searchable curve selectbox; return the selected curve ID."""
    default_label = next(
        (lbl for lbl, cid in CURVES_BY_LABEL.items() if cid == default_id),
        _ALL_CURVE_LABELS[0],
    )
    chosen = st.selectbox(
        label,
        options=_ALL_CURVE_LABELS,
        index=_ALL_CURVE_LABELS.index(default_label),
        key=key,
        disabled=IS_DEMO,
    )
    return CURVES_BY_LABEL[chosen]


def _tenor_to_maturity(effective: date, tenor: str) -> date:
    years_map = {"1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5, "7Y": 7, "10Y": 10}
    years = years_map.get(tenor, 5)
    return date(effective.year + years, effective.month, effective.day)


# ---------------------------------------------------------------------------
# Core form renderer — reused for both OIS and XCCY tabs
# ---------------------------------------------------------------------------


def _render_swap_form(
    tab_key:    str,
    swap_type:  Literal["OIS", "XCCY"],
    specs:      dict,
    labels:     list[str],
    by_label:   dict[str, str],
) -> SwapQuery | None:
    """
    Render the 3-column SWPM-style form and return a SwapQuery if the user
    clicked the Price button, otherwise None.
    """

    # Template selector — populates everything via session_state
    template_label = st.selectbox(
        t("swaps.template_label"),
        options=labels,
        key=f"{tab_key}_template",
        help=t("swaps.template_help"),
    )
    spec_key = by_label[template_label]
    spec     = specs[spec_key]

    st.markdown("---")

    col_leg1, col_leg2, col_val = st.columns(3)

    # -----------------------------------------------------------------------
    # Leg 1 — Fixed
    # -----------------------------------------------------------------------
    with col_leg1:
        st.markdown(f"**{t('swaps.leg1_header')}**")

        direction = st.selectbox(
            t("swaps.direction_label"),
            options=SWAP_DIRECTIONS,
            index=SWAP_DIRECTIONS.index("Receive"),
            key=f"{tab_key}_direction",
        )
        notional = st.number_input(
            t("swaps.notional_label"),
            value=float(spec.notional),
            min_value=1.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"{tab_key}_notional",
        )
        st.text_input(
            t("swaps.currency_label"),
            value=spec.currency,
            disabled=True,
            key=f"{tab_key}_ccy",
        )
        effective = st.date_input(
            t("swaps.effective_label"),
            value=date.today() if not IS_DEMO else date(2026, 3, 26),
            disabled=IS_DEMO,
            key=f"{tab_key}_effective",
        )
        tenor = st.selectbox(
            t("swaps.tenor_label"),
            options=SWAP_TENORS,
            index=SWAP_TENORS.index(spec.default_tenor),
            key=f"{tab_key}_tenor",
        )
        maturity = _tenor_to_maturity(effective, tenor)
        st.date_input(
            t("swaps.maturity_label"),
            value=maturity,
            disabled=True,
            key=f"{tab_key}_maturity",
        )
        fixed_rate_str = st.text_input(
            t("swaps.fixed_rate_label"),
            value="",
            placeholder="e.g. 5.25",
            key=f"{tab_key}_fixed_rate",
            disabled=IS_DEMO,
        )
        pay_freq_leg1 = st.selectbox(
            t("swaps.pay_freq_label"),
            options=SWAP_PAY_FREQUENCIES,
            index=SWAP_PAY_FREQUENCIES.index(spec.pay_frequency)
            if spec.pay_frequency in SWAP_PAY_FREQUENCIES
            else 0,
            key=f"{tab_key}_pay_freq_leg1",
        )
        day_count_leg1 = st.selectbox(
            t("swaps.day_count_label"),
            options=SWAP_DAY_COUNTS,
            index=SWAP_DAY_COUNTS.index(spec.day_count)
            if spec.day_count in SWAP_DAY_COUNTS
            else 0,
            key=f"{tab_key}_day_count_leg1",
        )

    # -----------------------------------------------------------------------
    # Leg 2 — Float
    # -----------------------------------------------------------------------
    with col_leg2:
        st.markdown(f"**{t('swaps.leg2_header')}**")

        opposite = "Pay" if direction == "Receive" else "Receive"
        st.text_input(
            t("swaps.direction_label"),
            value=opposite,
            disabled=True,
            key=f"{tab_key}_direction_leg2",
        )
        st.text_input(
            t("swaps.notional_label"),
            value=f"{notional:,.0f}",
            disabled=True,
            key=f"{tab_key}_notional_leg2",
        )
        st.text_input(
            t("swaps.currency_label"),
            value=spec.currency,
            disabled=True,
            key=f"{tab_key}_ccy_leg2",
        )
        st.text_input(
            t("swaps.effective_label"),
            value=str(effective),
            disabled=True,
            key=f"{tab_key}_effective_leg2",
        )
        st.text_input(
            t("swaps.maturity_label"),
            value=str(maturity),
            disabled=True,
            key=f"{tab_key}_maturity_leg2",
        )
        float_index = st.text_input(
            t("swaps.float_index_label"),
            value=spec.float_index,
            key=f"{tab_key}_float_index",
            disabled=IS_DEMO,
        )
        st.selectbox(
            t("swaps.pay_freq_label"),
            options=SWAP_PAY_FREQUENCIES,
            index=SWAP_PAY_FREQUENCIES.index(spec.pay_frequency)
            if spec.pay_frequency in SWAP_PAY_FREQUENCIES
            else 0,
            key=f"{tab_key}_pay_freq_leg2",
            disabled=True,
        )
        st.selectbox(
            t("swaps.day_count_label"),
            options=SWAP_DAY_COUNTS,
            index=SWAP_DAY_COUNTS.index(spec.day_count)
            if spec.day_count in SWAP_DAY_COUNTS
            else 0,
            key=f"{tab_key}_day_count_leg2",
            disabled=True,
        )

    # -----------------------------------------------------------------------
    # Valuation Settings + Price button
    # -----------------------------------------------------------------------
    with col_val:
        st.markdown(f"**{t('swaps.valuation_header')}**")

        curve_date = st.date_input(
            t("swaps.curve_date_label"),
            value=date(2026, 3, 26) if IS_DEMO else date.today(),
            disabled=IS_DEMO,
            key=f"{tab_key}_curve_date",
        )
        valuation_date = st.date_input(
            t("swaps.valuation_date_label"),
            value=date(2026, 3, 26) if IS_DEMO else date.today(),
            disabled=IS_DEMO,
            key=f"{tab_key}_valuation_date",
        )
        st.text_input(
            t("swaps.csa_ccy_label"),
            value=spec.csa_ccy,
            disabled=True,
            key=f"{tab_key}_csa_ccy",
        )
        coll_curve_id = _curve_selectbox(
            t("swaps.coll_curve_label"), spec.coll_curve, f"{tab_key}_coll_curve"
        )
        discount_curve_id = _curve_selectbox(
            t("swaps.discount_curve_label"), spec.discount_curve, f"{tab_key}_discount_curve"
        )
        forward_curve_id = _curve_selectbox(
            t("swaps.forward_curve_label"), spec.forward_curve, f"{tab_key}_forward_curve"
        )
        solve_for = st.selectbox(
            t("swaps.solve_for_label"),
            options=SWAP_SOLVE_TARGETS,
            key=f"{tab_key}_solve_for",
        )

        st.markdown("")
        price_clicked = st.button(
            t("swaps.button_price"),
            type="primary",
            use_container_width=True,
            key=f"{tab_key}_price_btn",
        )

        if IS_DEMO:
            st.divider()
            st.markdown(t("common.demo_cta_sidebar"))

    if not price_clicked:
        return None

    # Parse optional fixed rate
    fixed_rate: float | None = None
    if fixed_rate_str.strip():
        try:
            fixed_rate = float(fixed_rate_str.strip())
        except ValueError:
            st.error(f"Invalid fixed rate: {fixed_rate_str!r}")
            return None

    return SwapQuery(
        key=spec_key,
        swap_type=swap_type,
        direction=direction,
        tenor=tenor,
        valuation_date=valuation_date,
        curve_date=curve_date,
        notional=notional,
        discount_curve=discount_curve_id,
        forward_curve=forward_curve_id,
        csa_ccy=spec.csa_ccy,
        coll_curve=coll_curve_id,
        float_index=float_index,
        pay_frequency=pay_freq_leg1,
        day_count=day_count_leg1,
        fixed_rate=fixed_rate,
        solve_for=solve_for or "Coupon",
    )


# ---------------------------------------------------------------------------
# Results renderer
# ---------------------------------------------------------------------------


def _render_results(result: SwapResult, solve_for: str = "Coupon") -> None:
    if not result.ok:
        st.error(result.error)
        return
    if not result.metrics and result.par_rate is None:
        st.warning(t("swaps.warning_no_result"))
        return

    st.markdown("---")

    m = result.metrics
    cols = st.columns(6)

    solved_label = t("swaps.result_par_cpn") if solve_for == "Coupon" else f"Par {solve_for}"
    par_str = f"{result.par_rate:.6f}" if result.par_rate is not None else m.get("MktPx", "—")
    cols[0].metric(solved_label, par_str)
    cols[1].metric(t("swaps.result_npv"),      m.get("MktVal",          "—"))
    cols[2].metric(t("swaps.result_dv01"),      m.get("DV01",           "—"))
    cols[3].metric(t("swaps.result_pv01"),      m.get("PV01",           "—"))
    cols[4].metric(t("swaps.result_bp_value"),  m.get("BpValue",        "—"))
    cols[5].metric(t("swaps.result_accrued"),   m.get("AccruedInterest","—"))


# ---------------------------------------------------------------------------
# Page tabs
# ---------------------------------------------------------------------------

tab_ois, tab_xccy = st.tabs([t("swaps.tab_ois"), t("swaps.tab_xccy")])

with tab_ois:
    query_ois = _render_swap_form(
        tab_key="ois",
        swap_type="OIS",
        specs=OIS_SWAP_SPECS,
        labels=OIS_LABELS,
        by_label=OIS_BY_LABEL,
    )
    if query_ois is None:
        st.info(t("swaps.info_idle"))
    else:
        try:
            svc        = get_service()
            result_ois = run_pricing(svc, query_ois)
            _render_results(result_ois, query_ois.solve_for)
        except StructuringError as e:
            st.error(t("swaps.error_structuring", error=e))
        except PricingError as e:
            st.error(t("swaps.error_pricing", error=e))
        except IpNotWhitelistedError:
            st.error("🔒 Your IP is not whitelisted for the Bloomberg MARS API. "
                     "Please contact your Bloomberg representative to whitelist your current IP.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

with tab_xccy:
    query_xccy = _render_swap_form(
        tab_key="xccy",
        swap_type="XCCY",
        specs=XCCY_SWAP_SPECS,
        labels=XCCY_LABELS,
        by_label=XCCY_BY_LABEL,
    )
    if query_xccy is None:
        st.info(t("swaps.info_idle"))
    else:
        try:
            svc         = get_service()
            result_xccy = run_pricing(svc, query_xccy)
            _render_results(result_xccy, query_xccy.solve_for)
        except StructuringError as e:
            st.error(t("swaps.error_structuring", error=e))
        except PricingError as e:
            st.error(t("swaps.error_pricing", error=e))
        except IpNotWhitelistedError:
            st.error("🔒 Your IP is not whitelisted for the Bloomberg MARS API. "
                     "Please contact your Bloomberg representative to whitelist your current IP.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ---------------------------------------------------------------------------
# Demo CTA at page bottom
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")
