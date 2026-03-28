"""
Bloomberg MARS API HTTP client.

Handles:
- JWT authentication (fresh token per request)
- Session lifecycle: deal session, XMarket (XMKT) session, market data session
- Synchronous and asynchronous request dispatch via httpx
- Automatic response polling with tenacity retry
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Any

import httpx
from pydantic import ValidationError

from bloomberg.api_models import (
    StartMarketDataSessionRequest,
    StartMarketDataSessionResponse,
    StartSessionRequest,
    StartSessionResponse,
    StartXMarketSessionRequest,
    StartXMarketSessionResponse,
    _MarketDataSessionBody,
    _XMarketSessionBody,
)
from bloomberg.exceptions import (
    IpNotWhitelistedError,
    MarsApiError,
    SessionError,
)
from bloomberg.webapi.bbg_jwt import JwtFactory
from configs.settings import Settings

log = logging.getLogger(__name__)

_POLL_WAIT_SECONDS: int = 10
_POLL_MAX_ATTEMPTS: int = 120  # 20 minutes maximum


_PRICING_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/marswebapi/v1/securitiesPricing",
        "/marswebapi/v1/portfolioPricing",
        "/marswebapi/v1/securitiesKrr",
    }
)


def _results_endpoint(endpoint: str) -> str:
    if endpoint == "/marswebapi/v1/deals":
        return "/marswebapi/v1/results/Upload"
    if endpoint in _PRICING_ENDPOINTS:
        return "/marswebapi/v1/results/Pricing"
    return endpoint


class MarsClient:
    """
    Synchronous + asynchronous client for the Bloomberg MARS REST API.

    Usage (sync)::

        client = MarsClient(settings)
        response = client.send("POST", "/marswebapi/v1/securitiesPricing", body)

    Usage (async)::

        async with MarsClient(settings) as client:
            response = await client.send_async("POST", "/marswebapi/v1/securitiesPricing", body)
    """

    def __init__(self, settings: Settings, market_date: date | None = None) -> None:
        self._settings = settings
        self._jwt_factory = JwtFactory(
            host=settings.bbg_host,
            client_id=settings.bbg_client_id,
            client_secret=settings.bbg_client_secret,
        )
        self._market_date = market_date
        self._session_id: str | None = None
        self._xmarket_session_id: str | None = None
        self._market_data_session_id: str | None = None

        self._verify_ip_whitelist()

        if market_date is not None:
            self._xmarket_session_id = self._start_xmarket_session()

    def __del__(self) -> None:
        """Close all open sessions on garbage collection."""
        try:
            if self._xmarket_session_id:
                self.send("DELETE", f"/marswebapi/v1/dataSessions/{self._xmarket_session_id}")
            if self._market_data_session_id:
                self.send("DELETE", f"/marswebapi/v1/sessions/{self._market_data_session_id}")
            if self._session_id:
                self.send("DELETE", f"/marswebapi/v1/sessions/{self._session_id}")
        except Exception:
            pass  # best-effort cleanup

    def __enter__(self) -> MarsClient:
        return self

    def __exit__(self, *_: object) -> None:
        try:
            if self._xmarket_session_id:
                self.send("DELETE", f"/marswebapi/v1/dataSessions/{self._xmarket_session_id}")
            if self._market_data_session_id:
                self.send("DELETE", f"/marswebapi/v1/sessions/{self._market_data_session_id}")
            if self._session_id:
                self.send("DELETE", f"/marswebapi/v1/sessions/{self._session_id}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def session_id(self) -> str:
        """Deal session ID — lazily started on first access."""
        if self._session_id is None:
            self._session_id = self._start_deal_session()
        return self._session_id

    @property
    def xmarket_session_id(self) -> str | None:
        """XMarket (XMKT) session ID, or ``None`` if no market_date was given."""
        return self._xmarket_session_id

    @property
    def market_data_session_id(self) -> str:
        """Market data session ID — lazily started on first access."""
        if self._market_data_session_id is None:
            self._market_data_session_id = self._start_market_data_session()
        return self._market_data_session_id

    # ------------------------------------------------------------------
    # Public request helpers
    # ------------------------------------------------------------------

    def send(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
        results_endpoint: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a request and poll until results are ready.

        Args:
            method:           HTTP verb.
            endpoint:         API path.
            body:             Optional JSON request body.
            results_endpoint: Override the polling path (inferred automatically if omitted).

        Returns:
            Final JSON response dict.

        Raises:
            MarsApiError: On HTTP or API-level errors.
        """
        response = self._dispatch(method, endpoint, body)
        poll_endpoint = results_endpoint or _results_endpoint(endpoint)
        return self._poll_until_ready(response, poll_endpoint)

    async def send_async(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
        results_endpoint: str | None = None,
    ) -> dict[str, Any]:
        """
        Async version of :meth:`send`.
        """
        response = await self._dispatch_async(method, endpoint, body)
        poll_endpoint = results_endpoint or _results_endpoint(endpoint)
        return await self._poll_until_ready_async(response, poll_endpoint)

    # ------------------------------------------------------------------
    # Context manager support for async use
    # ------------------------------------------------------------------

    async def __aenter__(self) -> MarsClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        try:
            if self._xmarket_session_id:
                await self._dispatch_async("DELETE", f"/marswebapi/v1/dataSessions/{self._xmarket_session_id}")
            if self._market_data_session_id:
                sid = self._market_data_session_id
                await self._dispatch_async("DELETE", f"/marswebapi/v1/sessions/{sid}")
            if self._session_id:
                await self._dispatch_async("DELETE", f"/marswebapi/v1/sessions/{self._session_id}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal: HTTP dispatch
    # ------------------------------------------------------------------

    def _build_headers(self, method: str, endpoint: str, has_body: bool = False) -> dict[str, str]:
        token = self._jwt_factory.generate(
            path=endpoint,
            method=method,
            kvp={"uuid": self._settings.bbg_uuid},
        )
        headers: dict[str, str] = {"jwt": token}
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _dispatch(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._settings.bbg_host + endpoint
        headers = self._build_headers(method, endpoint, has_body=body is not None)
        try:
            resp = httpx.request(
                method=method,
                url=url,
                json=body,
                headers=headers,
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            body_text = exc.response.text[:300]
            raise MarsApiError(
                f"HTTP {exc.response.status_code} on {method} {endpoint}: {body_text}"
            ) from exc
        except httpx.RequestError as exc:
            raise MarsApiError(f"Request failed: {exc}") from exc

    async def _dispatch_async(
        self,
        method: str,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._settings.bbg_host + endpoint
        headers = self._build_headers(method, endpoint, has_body=body is not None)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as exc:
            body_text = exc.response.text[:300]
            raise MarsApiError(
                f"HTTP {exc.response.status_code} on {method} {endpoint}: {body_text}"
            ) from exc
        except httpx.RequestError as exc:
            raise MarsApiError(f"Request failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal: polling
    # ------------------------------------------------------------------

    def _extract_retrieval_id(
        self,
        response: dict[str, Any],
        current_id: str | None,
    ) -> tuple[str | None, bool]:
        """
        Parse a MARS response to extract a resultRetrievalId if the result is not
        ready yet. Returns ``(retrieval_id, still_pending)``.
        """
        results = response.get("results", [{}])
        first = results[0] if results else {}

        # Pattern 1: top-level resultNotReadyResponse
        if "resultNotReadyResponse" in response:
            return response["resultNotReadyResponse"]["resultRetrievalId"], True

        # Pattern 2: nested in results[]
        if "resultNotReadyResponse" in first:
            return first["resultNotReadyResponse"]["resultRetrievalId"], True

        # Pattern 3: uploadResponse with error code 0 (initial async response)
        upload = first.get("uploadResponse", {})
        if (
            upload.get("error", {}).get("errorCode") == 0
            and current_id is None
            and "assetClassesResponse" not in upload
        ):
            key_vals = upload.get("status", {}).get("key_vals", [])
            if key_vals:
                return key_vals[0]["value"]["str_value"], True

        # Pattern 4: uploadResponse still in progress (error code 104)
        if upload.get("error", {}).get("errorCode") == 104:
            if current_id is None:
                raise MarsApiError("Server returned 'still processing' (code 104) without a retrieval ID.")
            return current_id, True

        return current_id, False

    def _poll_until_ready(
        self,
        initial_response: dict[str, Any],
        results_endpoint: str,
    ) -> dict[str, Any]:
        response = initial_response
        retrieval_id: str | None = None

        for _ in range(_POLL_MAX_ATTEMPTS):
            retrieval_id, still_pending = self._extract_retrieval_id(response, retrieval_id)
            if not still_pending:
                break
            log.debug("Result not ready, polling %s/%s …", results_endpoint, retrieval_id)
            time.sleep(_POLL_WAIT_SECONDS)
            response = self._dispatch("GET", f"{results_endpoint}/{retrieval_id}")
        else:
            raise MarsApiError(f"Polling timed out after {_POLL_MAX_ATTEMPTS} attempts.")

        if isinstance(response, dict):
            response["requestId"] = retrieval_id
        return response

    async def _poll_until_ready_async(
        self,
        initial_response: dict[str, Any],
        results_endpoint: str,
    ) -> dict[str, Any]:
        response = initial_response
        retrieval_id: str | None = None

        for _ in range(_POLL_MAX_ATTEMPTS):
            retrieval_id, still_pending = self._extract_retrieval_id(response, retrieval_id)
            if not still_pending:
                break
            log.debug("Result not ready, polling %s/%s …", results_endpoint, retrieval_id)
            await asyncio.sleep(_POLL_WAIT_SECONDS)
            response = await self._dispatch_async("GET", f"{results_endpoint}/{retrieval_id}")
        else:
            raise MarsApiError(f"Polling timed out after {_POLL_MAX_ATTEMPTS} attempts.")

        if isinstance(response, dict):
            response["requestId"] = retrieval_id
        return response

    # ------------------------------------------------------------------
    # Internal: session management
    # ------------------------------------------------------------------

    def _verify_ip_whitelist(self) -> None:
        try:
            response = self._dispatch("GET", "/marswebapi/v1/scenarios/12345")
        except MarsApiError as exc:
            msg = str(exc)
            if "403" in msg or "401" in msg or "whitelist" in msg.lower():
                raise IpNotWhitelistedError(msg) from exc
            raise
        errors = response.get("errors", [])
        if errors:
            detail = errors[0].get("detail", str(errors[0]))
            raise IpNotWhitelistedError(detail)

    def _start_deal_session(self) -> str:
        try:
            req  = StartSessionRequest()
            resp = StartSessionResponse.model_validate(
                self.send("POST", "/marswebapi/v1/sessions", req.model_dump(by_alias=True))
            )
            return resp.start_session.session_id
        except (ValidationError, MarsApiError) as exc:
            raise SessionError("Failed to start deal session") from exc

    def _start_xmarket_session(self) -> str:
        try:
            req  = StartXMarketSessionRequest(
                start_session_request=_XMarketSessionBody(market_date=str(self._market_date))
            )
            resp = StartXMarketSessionResponse.model_validate(
                self.send("POST", "/marswebapi/v1/dataSessions", req.model_dump(by_alias=True))
            )
            return resp.start_session_response.session_id
        except (ValidationError, MarsApiError) as exc:
            raise SessionError("Failed to start XMarket session") from exc

    def _start_market_data_session(self) -> str:
        try:
            req  = StartMarketDataSessionRequest(
                start_market_data_session=_MarketDataSessionBody(
                    market_id=self._xmarket_session_id
                )
            )
            resp = StartMarketDataSessionResponse.model_validate(
                self.send(
                    "POST",
                    "/marswebapi/v1/sessions",
                    req.model_dump(by_alias=True, exclude_none=True),
                )
            )
            return resp.start_market_data_session_response.market_data_session
        except (ValidationError, MarsApiError) as exc:
            raise SessionError("Failed to start market data session") from exc
