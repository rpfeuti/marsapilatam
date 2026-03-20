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

st.set_page_config(page_title="Curves", page_icon="📈", layout="wide")
st.title("📈 Interest Rate Curves")
st.caption("Download and visualize Bloomberg XMarket rate curves via the MARS API.")

# ---------------------------------------------------------------------------
# Demo mode detection
# ---------------------------------------------------------------------------

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(
        "**Demo Mode** — displaying pre-loaded market data (2026-03-18). "
        "Connect a Bloomberg MARS API account to access live data for any curve and date.",
        icon="🔒",
    )

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="Starting XMarket session…")
def get_curves_service(market_date: date) -> CurvesService:
    return CurvesService(market_date=market_date)


# ---------------------------------------------------------------------------
# Cached download — re-runs only when inputs change
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Loading curve…")
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

# In demo mode restrict the curve selector to the 7 pre-saved curves
_demo_ids = {c["curve_id"] for c in DEMO_CURVES}

if IS_DEMO:
    _demo_labels_map = {
        lbl: cid
        for lbl, cid in CURVES_BY_LABEL.items()
        if cid in _demo_ids
    }
else:
    _demo_labels_map = CURVES_BY_LABEL

with st.sidebar:
    st.header("Curve parameters")

    _labels = list(_demo_labels_map.keys())
    _default_label = next(
        (lbl for lbl in _labels if "USD.SOFR" in lbl), _labels[0]
    )
    curve_label = st.selectbox(
        "Curve",
        options=_labels,
        index=_labels.index(_default_label),
        help="Select a Bloomberg XMarket curve from the catalog."
        if not IS_DEMO
        else "Demo mode: 7 LatAm + global curves available.",
    )
    curve_id = _demo_labels_map[curve_label]
    st.caption(f"Curve ID: **{curve_id}**")

    market_date = st.date_input(
        "Market date (XMarket session)",
        value=date(2026, 3, 18) if IS_DEMO else date.today(),
        disabled=IS_DEMO,
    )
    curve_date = st.date_input(
        "Curve date",
        value=date(2026, 3, 18) if IS_DEMO else date.today(),
        disabled=IS_DEMO,
    )

    curve_type = st.selectbox("Curve type", ["Raw Curve"] if IS_DEMO else CURVE_TYPES)

    side = st.selectbox("Side", CURVE_SIDES, disabled=IS_DEMO)

    interpolation_label = st.selectbox(
        "Interpolation method",
        list(INTERPOLATION_METHODS.keys()),
        disabled=(curve_type == "Raw Curve"),
    )
    interpolation = INTERPOLATION_METHODS[interpolation_label]

    interval = st.selectbox(
        "Interval",
        INTERPOLATION_INTERVALS,
        disabled=(curve_type == "Raw Curve"),
        help="Only used for Zero Coupon and Discount Factor curves.",
    )

    run = st.button("Load curve", type="primary", use_container_width=True)

    if IS_DEMO:
        st.divider()
        st.markdown(
            "**Want live data?**\n\n"
            "This tool is powered by the [Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/). "
            "Reach out to your Bloomberg representative to request a trial."
        )

# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

if not run:
    st.info("Select a curve in the sidebar and click **Load curve**.")
    st.stop()

if not IS_DEMO and curve_type != "Raw Curve" and curve_date >= market_date + timedelta(days=CURVE_SIZE):
    st.error("Curve date is too far in the future for the selected market date.")
    st.stop()

try:
    svc = get_curves_service(market_date)
    df = fetch_curve(svc, curve_id, curve_date, curve_type, side, interval, interpolation)
except CurveError as e:
    st.error(f"Curve error: {e}")
    st.stop()
except MarsApiError as e:
    st.error(f"Bloomberg API error: {e}")
    st.stop()

if df.empty:
    st.warning("No data returned for this curve.")
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

date_col = CURVE_API_FIELDS[curve_type][0]   # "maturityDate" or "date"
value_col = CURVE_API_FIELDS[curve_type][1]  # "rate" or "factor"

demo_tag = "  |  Demo Data — 2026-03-18" if IS_DEMO else ""

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
        title=f"{curve_type} — {curve_label.split(' (')[0]}  |  {curve_id}{demo_tag}",
        xaxis=dict(
            tickmode="array",
            tickvals=df["_tenor_days"].tolist(),
            ticktext=df["maturityTenor"].tolist(),
            title="Tenor",
        ),
        yaxis_title="Rate",
        hovermode="x unified",
        height=450,
    )
else:
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    fig = px.line(
        df,
        x=date_col,
        y=value_col,
        title=f"{curve_type} — {curve_label.split(' (')[0]}  |  {curve_id}{demo_tag}",
        markers=True,
    )
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title=value_col,
        height=450,
    )

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------

st.subheader(f"Curve data  —  {len(df)} points")
display_df = df.drop(columns=["_tenor_days"], errors="ignore")
st.dataframe(display_df, use_container_width=True, height=400)

# ---------------------------------------------------------------------------
# Demo CTA
# ---------------------------------------------------------------------------

if IS_DEMO:
    st.divider()
    st.info(
        "**This is a live Bloomberg MARS API integration.**  "
        "With a Bloomberg terminal subscription you get access to 246+ curves across all asset classes, "
        "live dates, and the full structuring & pricing engine.  "
        "**[Learn more about Bloomberg MARS](https://www.bloomberg.com/professional/product/multi-asset-risk-system/)**",
        icon="ℹ️",
    )
