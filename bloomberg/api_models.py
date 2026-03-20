"""
Pydantic v2 models for all Bloomberg MARS API request and response envelopes.

Using typed models instead of raw dicts gives:
- IDE completion and type-checking at definition time
- ValidationError (not silent KeyError) when the API shape changes
- .model_dump(by_alias=True) to produce the exact camelCase JSON the API expects
- .model_validate(response) to safely navigate nested response envelopes

Sections
--------
A. Session management  (bloomberg/webapi/mars_client.py)
   A1. Deal session           POST /marswebapi/v1/sessions
       StartSessionRequest / StartSessionResponse
   A2. XMarket session        POST /marswebapi/v1/dataSessions
       StartXMarketSessionRequest / StartXMarketSessionResponse
   A3. Market data session    POST /marswebapi/v1/sessions
       StartMarketDataSessionRequest / StartMarketDataSessionResponse

B. XMarket data download  (services/curves_service.py)
   POST /marswebapi/v1/dataDownload

   Request envelope:
     DataDownloadRequest
       └─ GetDataRequest          (sessionId, keyAndData[])
            └─ KeyAndDataItem
                 ├─ key: _DataKey → _RateCurveKey (curveId)
                 └─ data: dict    (marketData wrapper, content varies by CurveType)

   Response envelope:
     DataDownloadResponse
       └─ _GetDataResponse        (keyAndData[])
            └─ _KeyAndDataResponseItem
                 └─ data: _MarketDataWrapper
                      └─ market_data: _MarketDataBody
                           ├─ error: str | None   (present when Bloomberg reports an error)
                           └─ data: _MarketDataContent
                                ├─ rate_curve: dict   (keys vary by CurveType)
                                └─ error: str | None
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    """Shared config: accept both snake_case Python names and camelCase API aliases."""

    model_config = ConfigDict(populate_by_name=True)


# ===========================================================================
# A. Session management models
# ===========================================================================

# ---------------------------------------------------------------------------
# A1. Deal session  (POST /marswebapi/v1/sessions)
# ---------------------------------------------------------------------------


class StartSessionRequest(_Base):
    start_session: dict = Field(default_factory=dict, alias="startSession")


class _StartSessionData(_Base):
    session_id: str = Field(alias="sessionId")


class StartSessionResponse(_Base):
    start_session: _StartSessionData = Field(alias="startSession")


# ---------------------------------------------------------------------------
# A2. XMarket session  (POST /marswebapi/v1/dataSessions)
# ---------------------------------------------------------------------------


class _XMarketSessionBody(_Base):
    market_date: str = Field(alias="marketDate")


class StartXMarketSessionRequest(_Base):
    start_session_request: _XMarketSessionBody = Field(alias="startSessionRequest")


class _XMarketSessionData(_Base):
    session_id: str = Field(alias="sessionId")


class StartXMarketSessionResponse(_Base):
    start_session_response: _XMarketSessionData = Field(alias="startSessionResponse")


# ---------------------------------------------------------------------------
# A3. Market data session  (POST /marswebapi/v1/sessions)
# ---------------------------------------------------------------------------


class _MarketDataSessionBody(_Base):
    market_id: str | None = Field(default=None, alias="marketId")


class StartMarketDataSessionRequest(_Base):
    start_market_data_session: _MarketDataSessionBody = Field(alias="startMarketDataSession")


class _MarketDataSessionData(_Base):
    market_data_session: str = Field(alias="marketDataSession")


class StartMarketDataSessionResponse(_Base):
    start_market_data_session_response: _MarketDataSessionData = Field(
        alias="startMarketDataSessionResponse"
    )


# ===========================================================================
# B. XMarket data download models
#    Endpoint: POST /marswebapi/v1/dataDownload
# ===========================================================================

# ---------------------------------------------------------------------------
# B1. Request envelope
# ---------------------------------------------------------------------------


class _RateCurveKey(_Base):
    curve_id: str = Field(alias="curveId")


class _DataKey(_Base):
    rate_curve_key: _RateCurveKey = Field(alias="rateCurveKey")


class KeyAndDataItem(_Base):
    key:  _DataKey
    data: dict  # spec-driven marketData wrapper — content varies by CurveType


class GetDataRequest(_Base):
    session_id:    str                  = Field(alias="sessionId")
    key_and_data:  list[KeyAndDataItem] = Field(alias="keyAndData")


class DataDownloadRequest(_Base):
    get_data_request: GetDataRequest = Field(alias="getDataRequest")


# ---------------------------------------------------------------------------
# B2. Response envelope
# ---------------------------------------------------------------------------


class _MarketDataContent(_Base):
    """Inner data layer; rate_curve keys vary by CurveType so kept as dict."""

    rate_curve: dict      = Field(alias="rateCurve")
    error:      str | None = None


class _MarketDataBody(_Base):
    data:  _MarketDataContent
    error: str | None = None


class _MarketDataWrapper(_Base):
    market_data: _MarketDataBody = Field(alias="marketData")


class _KeyAndDataResponseItem(_Base):
    data: _MarketDataWrapper


class _GetDataResponse(_Base):
    key_and_data: list[_KeyAndDataResponseItem] = Field(alias="keyAndData")


class DataDownloadResponse(_Base):
    get_data_response: _GetDataResponse = Field(alias="getDataResponse")
