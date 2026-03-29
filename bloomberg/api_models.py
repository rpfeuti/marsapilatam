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


# ===========================================================================
# C. Deal structuring and pricing models
#    Endpoints:
#      POST /marswebapi/v1/deals/temporary    (structure)
#      POST /marswebapi/v1/securitiesPricing  (price / solve)
#
#    Note: Response parsing for these endpoints is handled by
#    bloomberg/pricing_result.py because the response shape varies
#    significantly by deal type and field.  Only the REQUEST side is
#    modelled here to get type-safe construction and .model_dump().
# ===========================================================================

# ---------------------------------------------------------------------------
# C1. Structure request  (POST /marswebapi/v1/deals/temporary)
# ---------------------------------------------------------------------------


class _MarsParamValue(_Base):
    """One typed value inside a MARS param entry."""

    double_val:    float | None = Field(default=None, alias="doubleVal")
    string_val:    str | None   = Field(default=None, alias="stringVal")
    date_val:      str | None   = Field(default=None, alias="dateVal")
    int_val:       int | None   = Field(default=None, alias="intVal")
    selection_val: dict | None  = Field(default=None, alias="selectionVal")


class _MarsParam(_Base):
    name:  str
    value: _MarsParamValue


class _LegOverride(_Base):
    param: list[_MarsParam]


class _DealStructureOverride(_Base):
    param: list[_MarsParam]
    leg:   list[_LegOverride] = Field(default_factory=list)


class StructureRequest(_Base):
    """
    Body for POST /marswebapi/v1/deals/temporary.

    session_id is injected by the service layer before serialisation.
    """

    session_id:              str                  = Field(alias="sessionId")
    tail:                    str
    deal_structure_override: _DealStructureOverride = Field(alias="dealStructureOverride")


# ---------------------------------------------------------------------------
# C2. Pricing request  (POST /marswebapi/v1/securitiesPricing)
# ---------------------------------------------------------------------------


class _DealHandleIdentifier(_Base):
    deal_handle: str = Field(alias="dealHandle")


class _SecurityEntry(_Base):
    identifier: _DealHandleIdentifier
    position:   int = 1


class _PricingParameter(_Base):
    valuation_date:                str        = Field(alias="valuationDate")
    market_data_date:              str        = Field(alias="marketDataDate")
    deal_session:                  str        = Field(alias="dealSession")
    requested_field:               list[str]  = Field(alias="requestedField")
    use_bbg_recommended_settings:  bool       = Field(
        default=True, alias="useBbgRecommendedSettings"
    )


class _SecuritiesPricingBody(_Base):
    pricing_parameter: _PricingParameter     = Field(alias="pricingParameter")
    security:          list[_SecurityEntry]


class PricingRequest(_Base):
    """Body for POST /marswebapi/v1/securitiesPricing (pricing mode)."""

    securities_pricing_request: _SecuritiesPricingBody = Field(
        alias="securitiesPricingRequest"
    )


# ---------------------------------------------------------------------------
# C3. Solve request  (POST /marswebapi/v1/securitiesPricing in solve mode)
# ---------------------------------------------------------------------------


class _SolveInput(_Base):
    name:  str
    value: _MarsParamValue


class _SolveBody(_Base):
    identifier:       _DealHandleIdentifier
    input:            _SolveInput
    solve_for:        str  = Field(alias="solveFor")
    solve_for_leg:    int  = Field(alias="solveForLeg")
    valuation_date:   str  = Field(alias="valuationDate")
    deal_session:     str  = Field(alias="dealSession")
    market_data_date: str  = Field(alias="marketDataDate")


class SolveRequest(_Base):
    """Body for POST /marswebapi/v1/securitiesPricing (solve mode)."""

    solve_request: _SolveBody = Field(alias="solveRequest")
