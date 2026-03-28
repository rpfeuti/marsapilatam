"""
Page — Interest Rate Curves

Downloads rate curves from Bloomberg's XMarket platform and displays them
as an interactive Plotly chart plus a raw data table.

Supported curve types (defined in configs/curves_config.py):
- Raw Curve        — par rates at instrument maturities
- Zero Coupon      — interpolated zero rates at custom date grid
- Discount Factor  — interpolated discount factors at custom date grid
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
# Guard: stop until the user clicks Load
# ---------------------------------------------------------------------------

if not run:
    st.info(t("curves.info_idle"))
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
