"""
Risk Assistant — chat page powered by xAI (Grok) with Bloomberg tool calling.

Copyright 2026, Bloomberg Finance L.P.
"""

from __future__ import annotations

import streamlit as st

from configs.i18n import t
from configs.settings import settings
from services.chat_service import ChatService

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
[data-testid="stMainBlockContainer"] {
    max-width: 1250px !important;
    margin: 0 auto !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "chat_service" not in st.session_state:
    try:
        st.session_state.chat_service = ChatService.from_settings()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

# ---------------------------------------------------------------------------
# WELCOME STATE
# ---------------------------------------------------------------------------

if not st.session_state.chat_messages:

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

    st.markdown(
        "<h2 style='text-align:center'>✨ Assistente de Riscos</h2>",
        unsafe_allow_html=True,
    )
    st.write("")

    if settings.demo_mode:
        st.info(t("chat.demo_notice"), icon="ℹ️")

    # Suggestion chips — clicking pre-fills the chat
    chips = [
        "Qual o MtM e DV01 de um COP OIS 5Y de COP 10bi?",
        "Asset swap AN9676742 Corp → CLP",
        "Stress +200bp na curva USD, deal SLLVJ42Q Corp",
        "DV01 por tenor do meu swap USD SOFR",
        "Taxa equivalente em CLP para AN9676742 Corp",
    ]

    row1 = st.columns(3)
    row2 = st.columns([1, 3, 3, 1])
    clicked = None

    for col, chip in zip(row1, chips[:3]):
        with col:
            if st.button(chip, use_container_width=True):
                clicked = chip

    for col, chip in zip(row2[1:3], chips[3:]):
        with col:
            if st.button(chip, use_container_width=True):
                clicked = chip

    if clicked:
        st.session_state.chat_messages.append({"role": "user", "content": clicked})
        with st.spinner(t("chat.thinking")):
            try:
                reply = st.session_state.chat_service.chat(st.session_state.chat_messages)
            except Exception as exc:
                reply = f"❌ Erro: {exc}"
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ---------------------------------------------------------------------------
# CONVERSATION STATE + chat_input (always rendered, native Streamlit)
# ---------------------------------------------------------------------------

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(t("chat.input_placeholder")):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(t("chat.thinking")):
            try:
                reply = st.session_state.chat_service.chat(st.session_state.chat_messages)
            except Exception as exc:
                reply = f"❌ Erro: {exc}"
        st.markdown(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("---")
    if st.button(t("chat.clear_btn"), use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()
    st.caption(t("chat.model_caption", model=settings.xai_model))
