"""
Home page — project overview and page directory.
"""

from __future__ import annotations

import streamlit as st

from configs.i18n import t

st.title(t("app.title"))
st.markdown(t("app.subtitle"))
st.markdown(t("app.nav_prompt"))
st.markdown("---")
st.markdown(t("app.demos_header"))

st.markdown(
    f"""
| {t("app.table_page")} | {t("app.table_desc")} |
|---|---|
| 📈 {t("curves.page_title")} | {t("app.demo_curves")} |
| 💱 Swaps | {t("app.demo_swaps")} {t("app.coming_soon")} |
| 💵 FX Options | {t("app.demo_fx")} {t("app.coming_soon")} |
| 🏦 Portfolio | {t("app.demo_portfolio")} {t("app.coming_soon")} |
| 📃 Deal Information | {t("app.demo_dealinfo")} {t("app.coming_soon")} |
| 🚀 Swaps Async | {t("app.demo_async")} {t("app.coming_soon")} |
"""
)

st.markdown("---")
st.markdown(t("app.resources_header"))
st.markdown(
    "- Bloomberg Terminal: `RISK<GO>`, `EAPI<GO>`, `SWPM<GO>`, `OVML<GO>`\n"
    "- [Bloomberg MARS API documentation]"
    "(https://developer.bloomberg.com/pages/apis/marsapi/reference)"
)
