"""
Page — FX Derivatives

Structure and price FX options via the Bloomberg MARS API.
Supports four product types across three tabs:
  FX Vanilla   — single-leg vanilla options (FX.VA)
  Risk Reversal — two-leg collar structure (FX.RR)
  FX Barriers   — knock-in (FX.KI) and knock-out (FX.KO) options
"""

from __future__ import annotations

import calendar
from datetime import date

import streamlit as st

from bloomberg.exceptions import IpNotWhitelistedError, PricingError, StructuringError
from configs.derivatives_config import (
    FX_BARRIER_DIRS_KI,
    FX_BARRIER_DIRS_KO,
    FX_BARRIER_TYPES,
    FX_CALL_PUT,
    FX_DIRECTIONS,
    FX_EXERCISE_TYPES,
    FX_KI_BY_LABEL,
    FX_KI_LABELS,
    FX_KI_SPECS,
    FX_KO_BY_LABEL,
    FX_KO_LABELS,
    FX_KO_SPECS,
    FX_RR_BY_LABEL,
    FX_RR_LABELS,
    FX_RR_SPECS,
    FX_VANILLA_BY_LABEL,
    FX_VANILLA_LABELS,
    FX_VANILLA_SPECS,
)
from configs.derivatives_config import FxDerivativeSpec
from configs.i18n import t
from configs.settings import settings
from services.fx_derivatives_service import DerivativePricingService, DerivativeQuery, DerivativeResult
from services.fx_service import FxRateService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("deriv.title"))
st.caption(t("deriv.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "1"


@st.cache_resource(show_spinner=t("deriv.spinner_session"))
def _get_service(v: str = _SVC_VERSION) -> DerivativePricingService:
    return DerivativePricingService.from_settings()


def _run_pricing(svc: DerivativePricingService, query: DerivativeQuery) -> DerivativeResult:
    with st.spinner(t("deriv.spinner_pricing")):
        return svc.price(query)


# ---------------------------------------------------------------------------
# FX spot rates (BLPAPI)
# ---------------------------------------------------------------------------

if "_fx_service" not in st.session_state:
    st.session_state["_fx_service"] = FxRateService.from_settings()

_fx: FxRateService = st.session_state["_fx_service"]


def _get_spot(spec: FxDerivativeSpec) -> float:
    """Return the spot rate in the pair's quoting convention via BLPAPI."""
    if spec.base_currency == "USD":
        return _fx.get_rate(spec.quote_currency) or 0.0
    return 1.0 / (_fx.get_rate(spec.base_currency) or 1.0)


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


def _default_expiry(tenor: str = "3M") -> date:
    """Compute a default expiry date from today (or demo date) plus tenor."""
    base = date(2026, 3, 26) if IS_DEMO else date.today()
    months_map = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12}
    months = months_map.get(tenor, 3)
    target_month = base.month + months
    target_year = base.year + (target_month - 1) // 12
    target_month = (target_month - 1) % 12 + 1
    day = min(base.day, calendar.monthrange(target_year, target_month)[1])
    return date(target_year, target_month, day)


def _fmt(raw: str, decimals: int = 4) -> str:
    """Format a numeric string with thousand separators and fixed decimals."""
    try:
        return f"{float(raw):,.{decimals}f}"
    except (ValueError, TypeError):
        return raw if raw else "—"


# ---------------------------------------------------------------------------
# Results renderer
# ---------------------------------------------------------------------------


def _render_results(result: DerivativeResult, spot: float = 0.0) -> None:
    if not result.ok:
        st.error(result.error)
        return
    if not result.metrics:
        st.warning(t("deriv.warning_no_result"))
        return

    st.markdown("---")
    m = result.metrics

    cols = st.columns(6)
    cols[0].metric(t("deriv.result_spot"),        _fmt(spot, 4) if spot else "—")
    cols[1].metric(t("deriv.result_premium"),     _fmt(m.get("MktPx", ""), 4))
    cols[2].metric(t("deriv.result_implied_vol"), _fmt(m.get("ImplVol", ""), 4))
    cols[3].metric(t("deriv.result_npv"),         _fmt(m.get("MktVal", ""), 2))
    cols[4].metric(t("deriv.result_delta"),       _fmt(m.get("Delta", ""), 4))
    cols[5].metric(t("deriv.result_gamma"),       _fmt(m.get("Gamma", ""), 6))

    cols2 = st.columns(6)
    cols2[0].metric(t("deriv.result_vega"),  _fmt(m.get("Vega", ""), 2))
    cols2[1].metric(t("deriv.result_theta"), _fmt(m.get("Theta", ""), 2))
    cols2[2].metric(t("deriv.result_rho"),   _fmt(m.get("Rho", ""), 2))
    cols2[3].metric("Vanna",                 _fmt(m.get("Vanna", ""), 2))
    cols2[4].metric("Volga",                 _fmt(m.get("Volga", ""), 2))


# ---------------------------------------------------------------------------
# Tab 1 — FX Vanilla
# ---------------------------------------------------------------------------


def _render_vanilla_form(tab_key: str) -> tuple[DerivativeQuery | None, float]:
    col_sel, _ = st.columns(2)
    with col_sel:
        template_label = _lrow(t("deriv.template_label")).selectbox(
            "", options=FX_VANILLA_LABELS, key=f"{tab_key}_template",
            help=t("deriv.template_help"), label_visibility="collapsed",
        )
    spec_key = FX_VANILLA_BY_LABEL[template_label]
    spec = FX_VANILLA_SPECS[spec_key]
    fk = f"{tab_key}_{spec_key}"
    spot = _get_spot(spec)

    st.markdown("---")
    col_deal, col_val = st.columns(2)

    with col_deal:
        st.markdown(f"**{t('deriv.deal_terms_header')}**")

        direction = _lrow(t("deriv.direction_label")).selectbox(
            "", options=FX_DIRECTIONS, key=f"{tab_key}_direction", label_visibility="collapsed",
        )
        call_put = _lrow(t("deriv.call_put_label")).selectbox(
            "", options=FX_CALL_PUT, key=f"{tab_key}_call_put", label_visibility="collapsed",
        )
        _lrow(t("deriv.underlying_label")).text_input(
            "", value=spec.underlying_ticker, disabled=True,
            key=f"{fk}_underlying_disp", label_visibility="collapsed",
        )
        notional = _lrow(t("deriv.notional_label")).number_input(
            "", value=float(spec.notional), min_value=1.0, step=100_000.0,
            format="%.0f", key=f"{fk}_notional", label_visibility="collapsed",
        )
        _lrow(t("deriv.notional_ccy_label")).text_input(
            "", value=spec.notional_currency, disabled=True,
            key=f"{fk}_nccy_disp", label_visibility="collapsed",
        )
        strike = _lrow(t("deriv.strike_label")).number_input(
            "", value=round(spot, 4), min_value=0.0, step=0.01, format="%.4f",
            key=f"{fk}_strike", disabled=IS_DEMO, label_visibility="collapsed",
        )
        expiry = _lrow(t("deriv.expiry_label")).date_input(
            "", value=_default_expiry(spec.default_tenor), disabled=IS_DEMO,
            key=f"{fk}_expiry", label_visibility="collapsed",
        )
        exercise_type = _lrow(t("deriv.exercise_type_label")).selectbox(
            "", options=FX_EXERCISE_TYPES, key=f"{fk}_exercise", label_visibility="collapsed",
        )

    with col_val:
        st.markdown(f"**{t('deriv.valuation_header')}**")

        curve_date = _lrow(t("deriv.curve_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_curve_date", label_visibility="collapsed",
        )
        valuation_date = _lrow(t("deriv.valuation_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_val_date", label_visibility="collapsed",
        )

        st.markdown("")
        price_clicked = st.button(
            t("deriv.button_price"), type="primary", use_container_width=True,
            key=f"{tab_key}_price_btn",
        )

        if IS_DEMO:
            st.divider()
            st.markdown(t("common.demo_cta_sidebar"))

    if not price_clicked:
        return None, spot

    return DerivativeQuery(
        key=spec_key, product_type="FX_VANILLA",
        direction=direction, call_put=call_put,
        notional=notional, strike=strike,
        expiry_date=expiry, valuation_date=valuation_date,
        curve_date=curve_date, exercise_type=exercise_type,
    ), spot


# ---------------------------------------------------------------------------
# Tab 2 — FX Risk Reversal
# ---------------------------------------------------------------------------


def _render_rr_form(tab_key: str) -> tuple[DerivativeQuery | None, float]:
    col_sel, _, _ = st.columns(3)
    with col_sel:
        template_label = _lrow(t("deriv.template_label")).selectbox(
            "", options=FX_RR_LABELS, key=f"{tab_key}_template",
            help=t("deriv.template_help"), label_visibility="collapsed",
        )
    spec_key = FX_RR_BY_LABEL[template_label]
    spec = FX_RR_SPECS[spec_key]
    fk = f"{tab_key}_{spec_key}"
    spot = _get_spot(spec)

    st.markdown("---")
    col_leg1, col_leg2, col_val = st.columns(3)

    with col_leg1:
        st.markdown(f"**{t('deriv.leg1_header')}**")

        direction = _lrow(t("deriv.direction_label")).selectbox(
            "", options=FX_DIRECTIONS, key=f"{tab_key}_direction", label_visibility="collapsed",
        )
        call_put = _lrow(t("deriv.call_put_label")).selectbox(
            "", options=FX_CALL_PUT, key=f"{tab_key}_call_put", label_visibility="collapsed",
        )
        _lrow(t("deriv.underlying_label")).text_input(
            "", value=spec.underlying_ticker, disabled=True,
            key=f"{fk}_underlying_disp", label_visibility="collapsed",
        )
        notional = _lrow(t("deriv.notional_label")).number_input(
            "", value=float(spec.notional), min_value=1.0, step=100_000.0,
            format="%.0f", key=f"{fk}_notional", label_visibility="collapsed",
        )
        strike1 = _lrow(t("deriv.strike_label")).number_input(
            "", value=round(spot * 1.05, 4), min_value=0.0, step=0.01, format="%.4f",
            key=f"{fk}_strike1", disabled=IS_DEMO, label_visibility="collapsed",
        )
        expiry = _lrow(t("deriv.expiry_label")).date_input(
            "", value=_default_expiry(spec.default_tenor), disabled=IS_DEMO,
            key=f"{fk}_expiry", label_visibility="collapsed",
        )
        exercise_type = _lrow(t("deriv.exercise_type_label")).selectbox(
            "", options=FX_EXERCISE_TYPES, key=f"{fk}_exercise", label_visibility="collapsed",
        )

    with col_leg2:
        st.markdown(f"**{t('deriv.leg2_header')}**")

        opposite_dir = "Sell" if direction == "Buy" else "Buy"
        _lrow(t("deriv.direction_label")).text_input(
            "", value=opposite_dir, disabled=True,
            key=f"{tab_key}_dir_leg2_{opposite_dir}", label_visibility="collapsed",
        )
        opposite_cp = "Put" if call_put == "Call" else "Call"
        _lrow(t("deriv.call_put_label")).text_input(
            "", value=opposite_cp, disabled=True,
            key=f"{tab_key}_cp_leg2_{opposite_cp}", label_visibility="collapsed",
        )
        _lrow(t("deriv.underlying_label")).text_input(
            "", value=spec.underlying_ticker, disabled=True,
            key=f"{fk}_underlying_leg2_disp", label_visibility="collapsed",
        )
        _lrow(t("deriv.notional_label")).text_input(
            "", value=f"{notional:,.0f}", disabled=True,
            key=f"{tab_key}_notional_leg2_{notional}", label_visibility="collapsed",
        )
        strike2 = _lrow(t("deriv.strike_label")).number_input(
            "", value=round(spot * 0.95, 4), min_value=0.0, step=0.01, format="%.4f",
            key=f"{fk}_strike2", disabled=IS_DEMO, label_visibility="collapsed",
        )
        _lrow(t("deriv.expiry_label")).text_input(
            "", value=str(expiry), disabled=True,
            key=f"{tab_key}_expiry_leg2_{expiry}", label_visibility="collapsed",
        )

    with col_val:
        st.markdown(f"**{t('deriv.valuation_header')}**")

        curve_date = _lrow(t("deriv.curve_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_curve_date", label_visibility="collapsed",
        )
        valuation_date = _lrow(t("deriv.valuation_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_val_date", label_visibility="collapsed",
        )

        st.markdown("")
        price_clicked = st.button(
            t("deriv.button_price"), type="primary", use_container_width=True,
            key=f"{tab_key}_price_btn",
        )

        if IS_DEMO:
            st.divider()
            st.markdown(t("common.demo_cta_sidebar"))

    if not price_clicked:
        return None, spot

    return DerivativeQuery(
        key=spec_key, product_type="FX_RR",
        direction=direction, call_put=call_put,
        notional=notional, strike=strike1,
        expiry_date=expiry, valuation_date=valuation_date,
        curve_date=curve_date, exercise_type=exercise_type,
        leg2_call_put=opposite_cp, leg2_strike=strike2,
        leg2_direction=opposite_dir,
    ), spot


# ---------------------------------------------------------------------------
# Tab 3 — FX Barriers (Knock-In / Knock-Out)
# ---------------------------------------------------------------------------


def _render_barrier_form(tab_key: str) -> tuple[DerivativeQuery | None, float]:
    col_sel, _ = st.columns(2)
    with col_sel:
        barrier_product = _lrow(t("deriv.barrier_product_label")).selectbox(
            "", options=["Knock-In", "Knock-Out"], key=f"{tab_key}_product",
            label_visibility="collapsed",
        )
        is_ki = barrier_product == "Knock-In"
        product_type = "FX_KI" if is_ki else "FX_KO"
        labels = FX_KI_LABELS if is_ki else FX_KO_LABELS
        by_label = FX_KI_BY_LABEL if is_ki else FX_KO_BY_LABEL
        specs = FX_KI_SPECS if is_ki else FX_KO_SPECS
        barrier_dirs = FX_BARRIER_DIRS_KI if is_ki else FX_BARRIER_DIRS_KO

        template_label = _lrow(t("deriv.template_label")).selectbox(
            "", options=labels, key=f"{tab_key}_template_{product_type}",
            help=t("deriv.template_help"), label_visibility="collapsed",
        )
    spec_key = by_label[template_label]
    spec = specs[spec_key]
    fk = f"{tab_key}_{product_type}_{spec_key}"
    spot = _get_spot(spec)

    st.markdown("---")
    col_deal, col_val = st.columns(2)

    with col_deal:
        st.markdown(f"**{t('deriv.deal_terms_header')}**")

        direction = _lrow(t("deriv.direction_label")).selectbox(
            "", options=FX_DIRECTIONS, key=f"{tab_key}_direction", label_visibility="collapsed",
        )
        call_put = _lrow(t("deriv.call_put_label")).selectbox(
            "", options=FX_CALL_PUT, key=f"{tab_key}_call_put", label_visibility="collapsed",
        )
        _lrow(t("deriv.underlying_label")).text_input(
            "", value=spec.underlying_ticker, disabled=True,
            key=f"{fk}_underlying_disp", label_visibility="collapsed",
        )
        notional = _lrow(t("deriv.notional_label")).number_input(
            "", value=float(spec.notional), min_value=1.0, step=100_000.0,
            format="%.0f", key=f"{fk}_notional", label_visibility="collapsed",
        )
        strike = _lrow(t("deriv.strike_label")).number_input(
            "", value=round(spot, 4), min_value=0.0, step=0.01, format="%.4f",
            key=f"{fk}_strike", disabled=IS_DEMO, label_visibility="collapsed",
        )
        expiry = _lrow(t("deriv.expiry_label")).date_input(
            "", value=_default_expiry(spec.default_tenor), disabled=IS_DEMO,
            key=f"{fk}_expiry", label_visibility="collapsed",
        )
        barrier_dir = _lrow(t("deriv.barrier_dir_label")).selectbox(
            "", options=barrier_dirs, key=f"{fk}_barrier_dir", label_visibility="collapsed",
        )
        barrier_default = round(spot * 1.10, 4) if "Up" in barrier_dirs[0] else round(spot * 0.90, 4)
        barrier_level = _lrow(t("deriv.barrier_level_label")).number_input(
            "", value=barrier_default, min_value=0.0, step=0.01, format="%.4f",
            key=f"{fk}_barrier_level", disabled=IS_DEMO, label_visibility="collapsed",
        )
        barrier_type = _lrow(t("deriv.barrier_type_label")).selectbox(
            "", options=FX_BARRIER_TYPES, key=f"{fk}_barrier_type", label_visibility="collapsed",
        )

    with col_val:
        st.markdown(f"**{t('deriv.valuation_header')}**")

        curve_date = _lrow(t("deriv.curve_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_curve_date", label_visibility="collapsed",
        )
        valuation_date = _lrow(t("deriv.valuation_date_label")).date_input(
            "", value=date(2026, 3, 26) if IS_DEMO else date.today(), disabled=IS_DEMO,
            key=f"{tab_key}_val_date", label_visibility="collapsed",
        )

        st.markdown("")
        price_clicked = st.button(
            t("deriv.button_price"), type="primary", use_container_width=True,
            key=f"{tab_key}_price_btn",
        )

        if IS_DEMO:
            st.divider()
            st.markdown(t("common.demo_cta_sidebar"))

    if not price_clicked:
        return None, spot

    return DerivativeQuery(
        key=spec_key, product_type=product_type,
        direction=direction, call_put=call_put,
        notional=notional, strike=strike,
        expiry_date=expiry, valuation_date=valuation_date,
        curve_date=curve_date,
        barrier_direction=barrier_dir, barrier_level=barrier_level,
        barrier_type=barrier_type,
    ), spot


# ---------------------------------------------------------------------------
# Error handler wrapper
# ---------------------------------------------------------------------------


def _price_and_render(tab_key: str, query: DerivativeQuery | None, spot: float = 0.0) -> None:
    if query is None:
        st.info(t("deriv.info_idle"))
        return
    try:
        svc = _get_service()
        result = _run_pricing(svc, query)
        _render_results(result, spot=spot)
    except StructuringError as e:
        st.error(t("deriv.error_structuring", error=e))
    except PricingError as e:
        st.error(t("deriv.error_pricing", error=e))
    except IpNotWhitelistedError:
        st.error("🔒 Your IP is not whitelisted for the Bloomberg MARS API. "
                 "Please contact your Bloomberg representative to whitelist your current IP.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")


# ---------------------------------------------------------------------------
# Page tabs
# ---------------------------------------------------------------------------

tab_vanilla, tab_barrier, tab_rr = st.tabs([
    t("deriv.tab_vanilla"), t("deriv.tab_barrier"), t("deriv.tab_rr"),
])

with tab_vanilla:
    query_va, spot_va = _render_vanilla_form("va")
    _price_and_render("va", query_va, spot_va)

with tab_barrier:
    query_bar, spot_bar = _render_barrier_form("bar")
    _price_and_render("bar", query_bar, spot_bar)

with tab_rr:
    query_rr, spot_rr = _render_rr_form("rr")
    _price_and_render("rr", query_rr, spot_rr)

# ---------------------------------------------------------------------------
# Demo CTA at page bottom
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")
