"""Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

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
    "<style>"
    "html, body, [class*='st-'] { font-size: 1.25rem; }"
    "[data-testid='stMainBlockContainer'] { padding-top: 2rem; }"
    "</style>",
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
    {"file": "pages/home.py",      "title_key": "nav.home",            "icon": "🏠", "default": True},
    {"file": "pages/curves.py",    "title_key": "curves.page_title",   "icon": "📈"},
    {"file": "pages/deal_info.py", "title_key": "dealinfo.page_title", "icon": "📃"},
    {"file": "pages/swaps.py",        "title_key": "swaps.page_title",  "icon": "💱"},
    {"file": "pages/fx_derivatives.py", "title_key": "deriv.page_title", "icon": "📊"},
    {"file": "pages/portfolio.py",      "title_key": "portfolio.page_title", "icon": "🏦"},
    {"file": "pages/stress_testing.py",  "title_key": "nav.stress_testing",   "icon": "🔬"},
    {"file": "pages/krr.py",             "title_key": "krr.page_title",        "icon": "📐"},
    {"file": "pages/async_swaps.py",     "title_key": "async_swaps.page_title", "icon": "🔗"},
]

pg = st.navigation([
    st.Page(p["file"], title=t(p["title_key"]), icon=p["icon"], default=p.get("default", False))
    for p in _PAGES
])
pg.run()
