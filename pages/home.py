"""
Home page — project overview and page directory.
"""

from __future__ import annotations

import streamlit as st

from configs.i18n import t

st.title(t("app.title"))
st.markdown(t("app.subtitle"))
st.caption(t("app.nav_prompt"))
st.markdown("---")

st.markdown(
    f"**{t('app.demos_header').strip('#').strip()}**\n\n"
    f"| {t('app.table_page')} | {t('app.table_desc')} |\n"
    f"|---|---|\n"
    f"| 📈 {t('curves.page_title')} | {t('app.demo_curves')} |\n"
    f"| 📃 {t('nav.deal_info')} | {t('app.demo_dealinfo')} |\n"
    f"| 💱 {t('swaps.page_title')} | {t('app.demo_swaps')} |\n"
    f"| 📊 {t('deriv.page_title')} | {t('app.demo_fx')} |\n"
    f"| 🏦 {t('nav.portfolio')} | {t('app.demo_portfolio')} {t('app.coming_soon')} |\n"
    f"| 🚀 {t('nav.swaps_async')} | {t('app.demo_async')} {t('app.coming_soon')} |\n"
    f"| 🧪 {t('nav.stress_testing')} | {t('app.demo_stress')} {t('app.coming_soon')} |\n"
    f"| 📐 {t('nav.krr')} | {t('app.demo_krr')} {t('app.coming_soon')} |"
)

st.markdown("---")
st.markdown(
    f"**Resources**\n\n"
    "- Bloomberg Terminal: `BDEV<GO>`, `RISK<GO>`, `EAPI<GO>`, `SWPM<GO>`, `OVML<GO>`, `ICVS<GO>`, `DLIB<GO>`\n"
    "- [Bloomberg MARS API documentation]"
    "(https://developer.bloomberg.com/pages/apis/marsapi/reference)"
)
