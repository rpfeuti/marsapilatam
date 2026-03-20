"""
Page 1 — Interest Rate Curves

Downloads rate curves from Bloomberg's XMarket platform and displays them
as an interactive Plotly chart plus a raw data table.

Supported curve types:
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
from configs.i18n import lang_selector, t
from configs.settings import (
    CURVE_API_FIELDS,
    CURVE_SIDES,
    CURVE_SIZE,
    CURVE_TYPES,
    DEMO_CURVES,
    INTERPOLATION_INTERVALS,
    INTERPOLATION_METHODS,
    settings,
)
from services.curves_service import CurvesService

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title=t("curves.page_title"), page_icon="📈", layout="wide")
st.title(t("curves.title"))
st.caption(t("curves.caption"))

# ---------------------------------------------------------------------------
# Demo mode detection
# ---------------------------------------------------------------------------

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=t("curves.spinner_session"))
def get_curves_service(market_date: date) -> CurvesService:
    return CurvesService(market_date=market_date)


# ---------------------------------------------------------------------------
# Cached download — re-runs only when inputs change
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=t("curves.spinner_download"))
def fetch_curve(
    _svc: CurvesService,
    curve_id: str,
    curve_date: date,
    curve_type: str,
    side: str,
    interval: str,
    interpolation: str,
) -> pd.DataFrame:
    requested_dates: list[date] = []

    if curve_type != "Raw Curve":
        step_map = {"Daily": 1, "Weekly": 7, "Monthly": 30}
        step = timedelta(days=step_map[interval])
        d = curve_date + timedelta(days=1)
        limit = curve_date + timedelta(days=CURVE_SIZE)
        while d < limit:
            requested_dates.append(d)
            d += step

    return _svc.download_curve(
        curve_type=curve_type,
        curve_id=curve_id,
        curve_date=curve_date,
        side=side,
        requested_dates=requested_dates,
        interpolation=interpolation,
    )


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

_demo_ids = {c["curve_id"] for c in DEMO_CURVES}
_labels_map = (
    {lbl: cid for lbl, cid in CURVES_BY_LABEL.items() if cid in _demo_ids}
    if IS_DEMO
    else CURVES_BY_LABEL
)

with st.sidebar:
    # Language selector first — affects all labels below
    lang_selector()

    st.header(t("curves.sidebar_header"))

    _labels = list(_labels_map.keys())
    _default_label = next((lbl for lbl in _labels if "USD.SOFR" in lbl), _labels[0])
    curve_label = st.selectbox(
        t("curves.curve_label"),
        options=_labels,
        index=_labels.index(_default_label),
        help=t("curves.curve_help_demo") if IS_DEMO else t("curves.curve_help"),
    )
    curve_id = _labels_map[curve_label]
    st.caption(t("curves.curve_id_caption", curve_id=curve_id))

    market_date = st.date_input(
        t("curves.market_date_label"),
        value=date(2026, 3, 18) if IS_DEMO else date.today(),
        disabled=IS_DEMO,
    )
    curve_date = st.date_input(
        t("curves.curve_date_label"),
        value=date(2026, 3, 18) if IS_DEMO else date.today(),
        disabled=IS_DEMO,
    )

    curve_type = st.selectbox(
        t("curves.curve_type_label"),
        ["Raw Curve"] if IS_DEMO else CURVE_TYPES,
    )
    side = st.selectbox(t("curves.side_label"), CURVE_SIDES, disabled=IS_DEMO)

    interpolation_label = st.selectbox(
        t("curves.interpolation_label"),
        list(INTERPOLATION_METHODS.keys()),
        disabled=(curve_type == "Raw Curve"),
    )
    interpolation = INTERPOLATION_METHODS[interpolation_label]

    interval = st.selectbox(
        t("curves.interval_label"),
        INTERPOLATION_INTERVALS,
        disabled=(curve_type == "Raw Curve"),
        help=t("curves.interval_help"),
    )

    run = st.button(t("curves.button_load"), type="primary", use_container_width=True)

    if IS_DEMO:
        st.divider()
        st.markdown(t("common.demo_cta_sidebar"))

# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

if not run:
    st.info(t("curves.info_idle"))
    st.stop()

if not IS_DEMO and curve_type != "Raw Curve" and curve_date >= market_date + timedelta(days=CURVE_SIZE):
    st.error(t("curves.error_date_range"))
    st.stop()

try:
    svc = get_curves_service(market_date)
    df = fetch_curve(svc, curve_id, curve_date, curve_type, side, interval, interpolation)
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
# Data cleaning
# ---------------------------------------------------------------------------

# Raw Curve: maturityTenor arrives as a nested dict {"length": 1, "unit": "WEEK"}
# Parse it into (1) a readable label "1W" and (2) a numeric days value for
# correct x-axis scaling in the chart.
if "maturityTenor" in df.columns:
    _days_per_unit = {"DAY": 1, "WEEK": 7, "MONTH": 30, "YEAR": 365}
    _unit_abbrev = {"WEEK": "W", "MONTH": "M", "YEAR": "Y", "DAY": "D"}

    def _tenor_days(v: object) -> float:
        if isinstance(v, dict):
            return float(v.get("length", 0)) * _days_per_unit.get(str(v.get("unit", "")).upper(), 1)
        return 0.0

    def _tenor_label(v: object) -> str:
        if isinstance(v, dict):
            length = v.get("length", "")
            unit = _unit_abbrev.get(str(v.get("unit", "")).upper(), v.get("unit", ""))
            return f"{length}{unit}"
        return str(v)

    df["_tenor_days"] = df["maturityTenor"].apply(_tenor_days)
    df["maturityTenor"] = df["maturityTenor"].apply(_tenor_label)

# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

date_col = CURVE_API_FIELDS[curve_type][0]
value_col = CURVE_API_FIELDS[curve_type][1]

profile = curve_label.split(" (")[0]
demo_tag = t("curves.demo_date_tag") if IS_DEMO else ""
chart_title = t("curves.chart_title", curve_type=curve_type, profile=profile,
                curve_id=curve_id, demo_tag=demo_tag)

if curve_type == "Raw Curve" and "_tenor_days" in df.columns:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["_tenor_days"],
        y=df[value_col],
        mode="lines+markers",
        text=df["maturityTenor"],
        hovertemplate="<b>%{text}</b><br>Rate: %{y:.4f}<extra></extra>",
    ))
    fig.update_layout(
        title=chart_title,
        xaxis=dict(
            tickmode="array",
            tickvals=df["_tenor_days"].tolist(),
            ticktext=df["maturityTenor"].tolist(),
            title=t("curves.xaxis_tenor"),
        ),
        yaxis_title="Rate",
        hovermode="x unified",
        height=450,
    )
else:
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    fig = px.line(df, x=date_col, y=value_col, title=chart_title, markers=True)
    fig.update_layout(
        hovermode="x unified",
        xaxis_title=t("curves.xaxis_date"),
        yaxis_title=value_col,
        height=450,
    )

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------

st.subheader(t("curves.table_header", n=len(df)))
display_df = df.drop(columns=["_tenor_days"], errors="ignore")
st.dataframe(display_df, use_container_width=True, height=400)

# ---------------------------------------------------------------------------
# Demo CTA at page bottom
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(t("common.demo_cta_bottom"), icon="ℹ️")
