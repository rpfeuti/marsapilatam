"""
Page — Swaps (OIS & XCCY)

Structure and price interest rate swaps via the Bloomberg MARS API.
Layout mirrors Bloomberg SWPM: Leg 1 | Leg 2 | Valuation Settings, with
results displayed as metric cards below.

Two tabs:
  OIS  — fixed vs floating, same currency (COP, USD, BRL, MXN, CLP, EUR)
  XCCY — USD leg vs local-currency OIS leg  (USD/COP, USD/BRL, …)
"""

from __future__ import annotations

import calendar
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
    XCCY_BY_LABEL,
    XCCY_LABELS,
    XCCY_SWAP_SPECS,
)
from services.fx_service import FxRateService
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
# FX rate service — one instance per browser session, cached with 1h TTL
# ---------------------------------------------------------------------------

if "_fx_service" not in st.session_state:
    st.session_state["_fx_service"] = FxRateService.from_settings()

_fx: FxRateService = st.session_state["_fx_service"]

# ---------------------------------------------------------------------------
# Cached service — one instance per session (deal session is persistent)
# ---------------------------------------------------------------------------


# Bump this constant whenever SwapPricingService gains new methods / changes
# its public API. Streamlit uses it as part of the cache key, ensuring the
# resource is re-created rather than served from a stale hot-reload cache.
_SVC_VERSION = "2"


@st.cache_resource(show_spinner=t("swaps.spinner_session"))
def get_service(v: str = _SVC_VERSION) -> SwapPricingService:
    return SwapPricingService.from_settings()


# ---------------------------------------------------------------------------
# Pricing — uses session_state as cache to avoid pickle serialisation of SwapResult
# ---------------------------------------------------------------------------


def run_pricing(svc: SwapPricingService, query: SwapQuery) -> SwapResult:
    """Price query, always calling the service (no caching)."""
    with st.spinner(t("swaps.spinner_pricing")):
        return svc.price(query)


# ---------------------------------------------------------------------------
# Shared curve label list (searchable)
# ---------------------------------------------------------------------------

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


def _tenor_to_maturity(effective: date, tenor: str) -> date:
    years_map = {"1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5, "7Y": 7, "10Y": 10}
    years = years_map.get(tenor, 5)
    target_year = effective.year + years
    day = min(effective.day, calendar.monthrange(target_year, effective.month)[1])
    return date(target_year, effective.month, day)


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

    Key design: every spec-dependent widget uses `fk = f"{tab_key}_{spec_key}"` as
    its key prefix. When the template changes spec_key changes, so Streamlit sees a
    brand-new widget and initialises it from value=/index= — no session_state
    manipulation needed.

    Display-only (disabled) fields that mirror other widget values have NO key, so
    Streamlit always uses the current value= parameter and never serves a stale value.
    """

    col_tmpl, _, _ = st.columns(3)
    with col_tmpl:
        template_label = _lrow(t("swaps.template_label")).selectbox(
            "",
            options=labels,
            key=f"{tab_key}_template",
            help=t("swaps.template_help"),
            label_visibility="collapsed",
        )
    spec_key = by_label[template_label]
    spec     = specs[spec_key]

    is_xccy  = bool(spec.base_currency)
    leg1_ccy = spec.base_currency if is_xccy else spec.currency
    leg2_ccy = spec.currency

    # fk changes whenever spec_key changes → fresh widget → value=/index= is used
    fk = f"{tab_key}_{spec_key}"

    st.markdown("---")

    col_leg1, col_leg2, col_val = st.columns(3)

    # -----------------------------------------------------------------------
    # Leg 1
    # -----------------------------------------------------------------------
    with col_leg1:
        st.markdown(f"**{t('swaps.leg1_header')}**")

        direction = _lrow(t("swaps.direction_label")).selectbox(
            "", options=SWAP_DIRECTIONS,
            index=SWAP_DIRECTIONS.index("Receive"),
            key=f"{tab_key}_direction",
            label_visibility="collapsed",
        )
        notional = _lrow(t("swaps.notional_label")).number_input(
            "",
            value=float(spec.notional),
            min_value=1.0,
            step=1_000_000.0,
            format="%.0f",
            key=f"{fk}_notional",
            label_visibility="collapsed",
        )
        _lrow(t("swaps.currency_label")).text_input(
            "", value=leg1_ccy, disabled=True,
            key=f"{fk}_ccy_leg1_disp",
            label_visibility="collapsed",
        )
        effective = _lrow(t("swaps.effective_label")).date_input(
            "",
            value=date.today() if not IS_DEMO else date(2026, 3, 26),
            disabled=IS_DEMO,
            key=f"{tab_key}_effective",
            label_visibility="collapsed",
        )
        _default_maturity = _tenor_to_maturity(
            date.today() if not IS_DEMO else date(2026, 3, 26),
            spec.default_tenor,
        )
        maturity = _lrow(t("swaps.maturity_label")).date_input(
            "",
            value=_default_maturity,
            disabled=IS_DEMO,
            key=f"{fk}_maturity",
            label_visibility="collapsed",
        )
        fixed_rate_str = _lrow(t("swaps.fixed_rate_label")).text_input(
            "",
            value="",
            placeholder="e.g. 5.25",
            key=f"{fk}_fixed_rate",
            disabled=IS_DEMO,
            label_visibility="collapsed",
        )
        pay_freq_leg1 = _lrow(t("swaps.pay_freq_label")).selectbox(
            "",
            options=SWAP_PAY_FREQUENCIES,
            index=SWAP_PAY_FREQUENCIES.index(spec.pay_frequency)
            if spec.pay_frequency in SWAP_PAY_FREQUENCIES
            else 0,
            key=f"{fk}_pay_freq_leg1",
            label_visibility="collapsed",
        )
        if spec.day_count:
            day_count_leg1 = _lrow(t("swaps.day_count_label")).selectbox(
                "",
                options=SWAP_DAY_COUNTS,
                index=SWAP_DAY_COUNTS.index(spec.day_count)
                if spec.day_count in SWAP_DAY_COUNTS
                else 0,
                key=f"{fk}_day_count_leg1",
                label_visibility="collapsed",
            )
        else:
            day_count_leg1 = ""
            _lrow(t("swaps.day_count_label")).text_input(
                "", value="(API default)", disabled=True,
                key=f"{fk}_dc_leg1_disp",
                label_visibility="collapsed",
            )

        leg1_default_disc = spec.leg1_discount_curve if is_xccy else spec.discount_curve
        leg1_discount_id = _curve_selectbox(
            t("swaps.discount_curve_label"), leg1_default_disc, f"{fk}_leg1_discount"
        )

    # -----------------------------------------------------------------------
    # Leg 2 — Float
    # -----------------------------------------------------------------------
    with col_leg2:
        st.markdown(f"**{t('swaps.leg2_header')}**")

        opposite = "Pay" if direction == "Receive" else "Receive"
        _lrow(t("swaps.direction_label")).text_input(
            "", value=opposite, disabled=True,
            key=f"{tab_key}_dir_leg2_{opposite}",
            label_visibility="collapsed",
        )

        # XCCY: Leg 2 has its own editable notional converted via FX spot
        if is_xccy:
            if leg1_ccy == "USD":
                _fx_default = _fx.default_leg2_notional(notional, leg2_ccy)
            else:
                _rate = _fx.get_rate(leg1_ccy)
                _fx_default = round(notional / _rate) if _rate and _rate > 0 else notional
            leg2_notional = _lrow(t("swaps.notional_label")).number_input(
                "",
                value=float(spec.leg2_notional) if spec.leg2_notional > 0 else float(_fx_default),
                min_value=1.0,
                step=1_000_000.0,
                format="%.0f",
                key=f"{fk}_leg2_notional",
                label_visibility="collapsed",
            )
        else:
            leg2_notional = 0.0
            _lrow(t("swaps.notional_label")).text_input(
                "", value=f"{notional:,.0f}", disabled=True,
                key=f"{tab_key}_notional_leg2_{notional}",
                label_visibility="collapsed",
            )

        _lrow(t("swaps.currency_label")).text_input(
            "", value=leg2_ccy, disabled=True,
            key=f"{fk}_ccy_leg2_disp",
            label_visibility="collapsed",
        )
        _lrow(t("swaps.effective_label")).text_input(
            "", value=str(effective), disabled=True,
            key=f"{tab_key}_eff_leg2_{effective}",
            label_visibility="collapsed",
        )
        _lrow(t("swaps.maturity_label")).text_input(
            "", value=str(maturity), disabled=True,
            key=f"{tab_key}_mat_leg2_{maturity}",
            label_visibility="collapsed",
        )
        float_index = _lrow(t("swaps.float_index_label")).text_input(
            "",
            value=spec.float_index,
            key=f"{fk}_float_index",
            disabled=IS_DEMO,
            label_visibility="collapsed",
        )
        spread_val = _lrow(t("swaps.spread_label")).number_input(
            "",
            value=0.0,
            step=1.0,
            format="%.1f",
            key=f"{fk}_spread",
            disabled=IS_DEMO,
            label_visibility="collapsed",
        )
        _lrow(t("swaps.pay_freq_label")).text_input(
            "", value=pay_freq_leg1, disabled=True,
            key=f"{tab_key}_pf_leg2_{pay_freq_leg1}",
            label_visibility="collapsed",
        )
        if spec.day_count:
            _lrow(t("swaps.day_count_label")).selectbox(
                "",
                options=SWAP_DAY_COUNTS,
                index=SWAP_DAY_COUNTS.index(spec.day_count)
                if spec.day_count in SWAP_DAY_COUNTS
                else 0,
                disabled=True,
                key=f"{fk}_dc_leg2_disp",
                label_visibility="collapsed",
            )
        else:
            _lrow(t("swaps.day_count_label")).text_input(
                "", value="(API default)", disabled=True,
                key=f"{fk}_dc_leg2_disp",
                label_visibility="collapsed",
            )

        leg2_discount_id = _curve_selectbox(
            t("swaps.discount_curve_label"), spec.discount_curve, f"{fk}_leg2_discount"
        )
        leg2_forward_id = _curve_selectbox(
            t("swaps.forward_curve_label"), spec.forward_curve, f"{fk}_leg2_forward"
        )

    # -----------------------------------------------------------------------
    # Valuation Settings + Price button
    # -----------------------------------------------------------------------
    with col_val:
        st.markdown(f"**{t('swaps.valuation_header')}**")

        curve_date = _lrow(t("swaps.curve_date_label")).date_input(
            "",
            value=date(2026, 3, 26) if IS_DEMO else date.today(),
            disabled=IS_DEMO,
            key=f"{tab_key}_curve_date",
            label_visibility="collapsed",
        )
        valuation_date = _lrow(t("swaps.valuation_date_label")).date_input(
            "",
            value=date(2026, 3, 26) if IS_DEMO else date.today(),
            disabled=IS_DEMO,
            key=f"{tab_key}_valuation_date",
            label_visibility="collapsed",
        )
        _solve_targets = _get_solve_targets(spec.deal_type)
        solve_for = _lrow(t("swaps.solve_for_label")).selectbox(
            "",
            options=_solve_targets,
            key=f"{fk}_solve_for",
            label_visibility="collapsed",
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

    spread: float = float(spread_val)

    return SwapQuery(
        key=spec_key,
        swap_type=swap_type,
        direction=direction,
        effective_date=effective,
        maturity_date=maturity,
        valuation_date=valuation_date,
        curve_date=curve_date,
        notional=notional,
        forward_curve=leg2_forward_id,
        discount_curve=leg2_discount_id,
        float_index=float_index,
        pay_frequency=pay_freq_leg1,
        day_count=day_count_leg1,
        fixed_rate=fixed_rate,
        spread=spread,
        solve_for=solve_for or "Coupon",
        leg1_discount_curve=leg1_discount_id,
        leg2_notional=leg2_notional,
    )


# ---------------------------------------------------------------------------
# Results renderer
# ---------------------------------------------------------------------------


def _fmt(raw: str, decimals: int = 2) -> str:
    """Format a numeric string with thousand separators and fixed decimals."""
    try:
        return f"{float(raw):,.{decimals}f}"
    except (ValueError, TypeError):
        return raw if raw else "—"


def _render_results(result: SwapResult, solve_for: str = "Coupon") -> None:
    if not result.ok:
        st.error(result.error)
        return
    if not result.metrics and result.par_rate is None:
        st.warning(t("swaps.warning_no_result"))
        return

    st.markdown("---")

    m = result.metrics
    cols = st.columns(7)

    solved_label = t("swaps.result_par_cpn") if solve_for in ("Coupon", "FixedRate") else f"Par {solve_for}"
    par_str = f"{result.par_rate:.6f}" if result.par_rate is not None else _fmt(m.get("MktPx", ""), 6)
    cols[0].metric(solved_label, par_str)
    cols[1].metric(t("swaps.result_npv"),      _fmt(m.get("MktVal",          "")))
    cols[2].metric(t("swaps.result_dv01"),      _fmt(m.get("DV01",           "")))
    cols[3].metric(t("swaps.result_pv01"),      _fmt(m.get("PV01",           "")))
    cols[4].metric(t("swaps.result_bp_value"),  _fmt(m.get("BpValue", m.get("DV01", ""))))
    cols[5].metric(t("swaps.result_premium"),   _fmt(m.get("MktPx",          "")))
    cols[6].metric(t("swaps.result_accrued"),   _fmt(m.get("AccruedInterest","")))


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
