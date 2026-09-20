"""
Risk Assistant — xAI (Grok) chat service orchestrator.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from openai import APIConnectionError, APIError, APITimeoutError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from services.chat_tools import (
    _TOOLS,
    _SYSTEM_PROMPT,
    execute_tool,
    _fallback_reply_from_tool_content,
    _last_tool_content_for_fallback,
    _MAX_CHAT_TOOL_ROUNDS,
    _XAI_BASE_URL,
    _XAI_HTTP_TIMEOUT
)
from configs.settings import settings

log = logging.getLogger(__name__)

class ChatService:
    def __init__(self, api_key: str, model: str = "grok-beta") -> None:
        self._client = OpenAI(
            api_key=api_key,
            base_url=_XAI_BASE_URL,
            timeout=_XAI_HTTP_TIMEOUT,
            max_retries=2,
        )
        self._model = model

    def _system_message(self) -> str:
        from datetime import date
        today = date.today().isoformat()
        mode  = "Ligado (mock)" if settings.demo_mode else "Desligado (live API)"
        return _SYSTEM_PROMPT.format(today=today, demo_mode=mode)

    def chat_loop(self, messages: list[dict[str, Any]]) -> str:
        """
        Run the function-calling loop for the given conversation history.

        Returns the final assistant text reply.
        """
        working: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self._system_message()},
            *messages,
        ]

        rounds = 0
        while True:
            rounds += 1
            if rounds > _MAX_CHAT_TOOL_ROUNDS:
                log.error("chat_loop exceeded max tool rounds (%s)", _MAX_CHAT_TOOL_ROUNDS)
                return (
                    "❌ O assistente excedeu o número máximo de chamadas a ferramentas seguidas. "
                    "Use **Limpar conversa** e envie a pergunta de novo (em uma única mensagem, se possível)."
                )

            kwargs: dict[str, Any] = {"model": self._model, "messages": working}
            if _TOOLS:
                kwargs["tools"] = _TOOLS
                kwargs["tool_choice"] = "auto"

            try:
                response = self._client.chat.completions.create(**kwargs)
            except APITimeoutError as exc:
                log.warning("xAI request timed out: %s", exc)
                return (
                    "❌ Tempo esgotado ao falar com o serviço xAI (Grok). "
                    "A rede ou a API pode estar lenta — tente de novo em instantes."
                )
            except APIConnectionError as exc:
                log.warning("xAI connection error: %s", exc)
                return (
                    "❌ Não foi possível ligar ao serviço xAI (Grok). Verifique a ligação à internet "
                    "e o estado do serviço."
                )
            except APIError as exc:
                log.warning("xAI API error: %s", exc)
                return f"❌ Erro da API xAI (Grok): {exc}"

            msg = response.choices[0].message

            if not msg.tool_calls:
                text = (msg.content or "").strip()
                if text:
                    return msg.content or ""
                fb = _last_tool_content_for_fallback(working)
                if fb is not None:
                    fallback = _fallback_reply_from_tool_content(fb)
                    if fallback.strip():
                        log.warning(
                            "Assistant returned empty content after tools; using tool result fallback"
                        )
                        return fallback
                return ""

            working.append(msg)  # type: ignore[arg-type]

            for tc in msg.tool_calls:
                try:
                    args   = json.loads(tc.function.arguments)
                    result = execute_tool(tc.function.name, args)
                except Exception as exc:
                    result = json.dumps({"error": str(exc)})
                    log.exception("Tool %s failed", tc.function.name)

                working.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result,
                })

    def chat(self, messages: list[dict[str, Any]]) -> str:
        """Public entry point used by the Streamlit Risk Assistant page."""
        return self.chat_loop(messages)

    @classmethod
    def from_settings(cls) -> ChatService:
        if not settings.xai_api_key:
            raise RuntimeError(
                "XAI_API_KEY não configurado. Adicione XAI_API_KEY no .env local "
                "ou em App settings → Secrets no Streamlit Cloud."
            )
        return cls(api_key=settings.xai_api_key, model=settings.xai_model)
