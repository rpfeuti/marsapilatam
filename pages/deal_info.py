"""
Page — Deal Information

Browse all MARS deal types and inspect their full parameter schemas
(deal-level and per-leg), including field names, types, modes,
solvable targets, and allowed values for selection fields.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from configs.i18n import t
from configs.settings import settings
from services.deal_info_service import DealInfoService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("dealinfo.title"))
st.caption(t("dealinfo.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "5"


@st.cache_resource(show_spinner=t("dealinfo.spinner_types"))
def _get_service(_v: str = _SVC_VERSION) -> DealInfoService:
    return DealInfoService.from_settings()


@st.cache_data(ttl=3600, show_spinner=t("dealinfo.spinner_types"))
def _get_deal_types(_v: str = _SVC_VERSION) -> list[tuple[str, str]]:
    return _get_service().fetch_deal_types()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _params_to_df(params: list[dict]) -> pd.DataFrame:
    """Convert a list of schema parameter dicts to a display DataFrame."""
    rows: list[dict[str, str]] = []
    for p in params:
        val_info = p.get("value", {})
        val_type = val_info.get("type", "")

        allowed = ""
        if val_type == "SELECTION_VAL":
            items = (
                val_info.get("valueInfo", {})
                .get("selection", {})
                .get("items", [])
            )
            allowed = ", ".join(it.get("value", "") for it in items)

        rows.append({
            t("dealinfo.col_name"):        p.get("name", ""),
            t("dealinfo.col_type"):        val_type,
            t("dealinfo.col_mode"):        p.get("mode", ""),
            t("dealinfo.col_solvable"):    "Yes" if p.get("solvableTarget") else "",
            t("dealinfo.col_category"):    p.get("category", ""),
            t("dealinfo.col_description"): p.get("description", ""),
            t("dealinfo.col_allowed"):     allowed,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

deal_types = _get_deal_types()
type_labels = [f"{code} — {desc}" if desc else code for code, desc in deal_types]
type_codes = [code for code, _ in deal_types]

default_idx = type_codes.index("IR.OIS") if "IR.OIS" in type_codes else 0

col_sel, _, _ = st.columns(3)
with col_sel:
    selected_label = st.selectbox(
        t("dealinfo.deal_type_label"),
        options=type_labels,
        index=default_idx,
    )
    selected_type = type_codes[type_labels.index(selected_label)]
    st.caption(f"{len(deal_types)} deal types available")
    load_clicked = st.button(
        t("dealinfo.btn_load"),
        type="primary",
    )

if not load_clicked:
    st.info(t("dealinfo.no_params"))
    st.stop()

if IS_DEMO:
    st.warning(t("common.demo_banner"), icon="🔒")
    st.stop()

# ---------------------------------------------------------------------------
# Fetch and display schema
# ---------------------------------------------------------------------------

with st.spinner(t("dealinfo.spinner")):
    svc = _get_service()
    schema_resp = svc.fetch_deal_schema(selected_type)

if not schema_resp:
    st.error(t("dealinfo.no_params"))
    st.stop()

status = schema_resp.get("returnStatus", {})
if status.get("status") == "S_FAILURE":
    notifications = status.get("notifications", [])
    msg = notifications[0].get("message", "") if notifications else "Unknown error"
    st.error(f"**{selected_type}** is not supported: {msg}")
    st.stop()

structure = schema_resp.get("dealStructure", {})
if not structure:
    st.error(t("dealinfo.no_params"))
    st.stop()

deal_params = structure.get("param", [])
legs = structure.get("leg", [])

total_params = len(deal_params) + sum(len(leg.get("param", [])) for leg in legs)
solvable_count = (
    sum(1 for p in deal_params if p.get("solvableTarget"))
    + sum(1 for leg in legs for p in leg.get("param", []) if p.get("solvableTarget"))
)

st.markdown("---")
summary = t("dealinfo.summary").format(
    total=total_params, legs=len(legs), solvable=solvable_count,
)
st.caption(summary)

# Deal-level parameters
if deal_params:
    st.subheader(t("dealinfo.deal_params_header"))
    st.dataframe(
        _params_to_df(deal_params),
        use_container_width=True,
        hide_index=True,
    )

# Per-leg parameters
for i, leg in enumerate(legs, start=1):
    leg_params = leg.get("param", [])
    if not leg_params:
        continue
    header = t("dealinfo.leg_header").replace("{n}", str(i))
    st.subheader(header)
    st.dataframe(
        _params_to_df(leg_params),
        use_container_width=True,
        hide_index=True,
    )
