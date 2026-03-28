from __future__ import annotations

import streamlit as st

from configs.i18n import lang_selector, t
from configs.settings import settings

st.set_page_config(
    page_title="MARS API LatAm",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    "<style>html, body, [class*='st-'] { font-size: 1.25rem; }</style>",
    unsafe_allow_html=True,
)

# Language selector and connection status appear on every page via the sidebar
with st.sidebar:
    lang_selector()
    st.markdown("---")
    if settings.demo_mode:
        st.error(t("common.status_demo"), icon="🔒")
    else:
        st.success(t("common.status_live"), icon="✅")

# Declarative page registry — add a new page by appending one dict here
_PAGES = [
    {"file": "pages/home.py",   "title_key": "nav.home",          "icon": "🏠", "default": True},
    {"file": "pages/curves.py", "title_key": "curves.page_title", "icon": "📈"},
    {"file": "pages/swaps.py",  "title_key": "swaps.page_title",  "icon": "💱"},
]

pg = st.navigation([
    st.Page(p["file"], title=t(p["title_key"]), icon=p["icon"], default=p.get("default", False))
    for p in _PAGES
])
pg.run()
