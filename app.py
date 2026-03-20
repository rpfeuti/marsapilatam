from __future__ import annotations

import streamlit as st

from configs.i18n import lang_selector, t
from configs.settings import settings

st.set_page_config(
    page_title="MARS API LatAm",
    page_icon="📊",
    layout="wide",
)

# Language selector lives here so it appears on every page
with st.sidebar:
    lang_selector()
    st.markdown("---")
    if settings.demo_mode:
        st.error(t("common.status_demo"), icon="🔒")
    else:
        st.success(t("common.status_live"), icon="✅")

pg = st.navigation(
    [
        st.Page("pages/home.py", title=t("nav.home"), icon="🏠", default=True),
        st.Page("pages/1_📈_Curves.py", title=t("curves.page_title"), icon="📈"),
    ]
)
pg.run()
