import streamlit as st

from configs.i18n import lang_selector, t

st.set_page_config(
    page_title="MARS API LatAm",
    page_icon="📊",
    layout="wide",
)

# Language selector — sets st.session_state["lang"] shared across all pages
with st.sidebar:
    lang_selector()

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
| 💱 Swaps | {t("app.demo_swaps")} |
| 💵 FX Options | {t("app.demo_fx")} |
| 🏦 Portfolio | {t("app.demo_portfolio")} |
| 📃 Deal Information | {t("app.demo_dealinfo")} |
| 🚀 Swaps Async | {t("app.demo_async")} |
"""
)

st.markdown("---")
st.markdown(t("app.resources_header"))
st.markdown(
    "- Bloomberg Terminal: `RISK<GO>`, `EAPI<GO>`, `SWPM<GO>`, `OVML<GO>`\n"
    "- [Bloomberg MARS API documentation]"
    "(https://developer.bloomberg.com/pages/apis/marsapi/reference)"
)
