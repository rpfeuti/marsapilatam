"""
Home page — project overview and page directory.

Copyright 2026, Bloomberg Finance L.P.

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
    f"| 🏦 {t('nav.portfolio')} | {t('app.demo_portfolio')} |\n"
    f"| 🧪 {t('nav.stress_testing')} | {t('app.demo_stress')} |\n"
    f"| 📐 {t('nav.krr')} | {t('app.demo_krr')} |\n"
    f"| 🚀 {t('nav.swaps_async')} | {t('app.demo_async')} |"
)

st.markdown("---")
st.markdown(
    f"**Resources**\n\n"
    "- Bloomberg Terminal: `BDEV<GO>`, `RISK<GO>`, `EAPI<GO>`, `SWPM<GO>`, `OVML<GO>`, `ICVS<GO>`, `DLIB<GO>`\n"
    "- [Bloomberg MARS API documentation]"
    "(https://developer.bloomberg.com/pages/apis/marsapi/reference)\n"
    "- [Source code on GitHub](https://github.com/rpfeuti/marsapilatam)"
)
