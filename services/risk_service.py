"""
Key Rate Risk (KRR) service.

Submits KRR requests to the Bloomberg MARS API and returns per-deal, per-curve
DV01 decomposition by tenor bucket.

Both securitiesKrr (single deal) and portfolioKrr endpoints are synchronous —
results are returned inline in the submission response.

Architecture:
    KrrCurveResult      — DV01 by tenor for one curve on one deal
    KrrDealResult       — all curves for one deal
    KrrResult           — full response (list of deals + optional error)
    KrrRepository       — structural Protocol
    KrrLiveRepository   — live Bloomberg MARS implementation
    KrrDemoRepository   — offline demo-data implementation
    KrrService          — thin orchestrator with from_settings() factory

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

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from bloomberg.exceptions import MarsApiError
from bloomberg.webapi import MarsClient
from configs.curves_catalog import CURVES_BY_ID
from configs.krr_config import (
    DEMO_KRR_TENORS_LOCAL,
    DEMO_KRR_TENORS_USD,
    KRR_DEFINITION_ID,
    KRR_DEFINITION_NAME,
    KRR_PRICING_FIELDS,
)
from configs.settings import settings

log = logging.getLogger(__name__)


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass
class KrrCurveResult:
    """DV01 decomposition for one curve on one deal."""

    curveid: str
    underlying_currency: str
    valuation_currency: str
    dv01_by_tenor: dict[str, float]

    @property
    def label(self) -> str:
        """Human-readable label: catalog description or fallback."""
        catalog_label = CURVES_BY_ID.get(self.curveid)
        if catalog_label:
            return catalog_label
        return f"{self.underlying_currency} ({self.curveid})"

    @property
    def total_dv01(self) -> float:
        return sum(self.dv01_by_tenor.values())


@dataclass
class KrrDealResult:
    """KRR result for one deal: all curves."""

    deal_id: str
    ticker: str
    curves: list[KrrCurveResult] = field(default_factory=list)

    @property
    def label(self) -> str:
        return self.ticker or self.deal_id


@dataclass
class KrrResult:
    """Full KRR output for a deal or portfolio."""

    deals: list[KrrDealResult] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def aggregate_by_curve(self) -> dict[str, dict[str, float]]:
        """Sum DV01 across all deals, keyed by curve label then tenor.

        Returns {curve_label: {tenor: total_dv01}}.
        Preserves tenor order from the first deal that contributes each curve.
        """
        result: dict[str, dict[str, float]] = {}
        for deal in self.deals:
            for curve in deal.curves:
                lbl = curve.label
                if lbl not in result:
                    result[lbl] = {}
                for tenor, dv01 in curve.dv01_by_tenor.items():
                    result[lbl][tenor] = result[lbl].get(tenor, 0.0) + dv01
        return result


# ===========================================================================
# Repository Protocol
# ===========================================================================


class KrrRepository(Protocol):
    def run_deal_krr(
        self,
        deal_id: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult: ...

    def run_portfolio_krr(
        self,
        portfolio_name: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult: ...


# ===========================================================================
# Pure helpers
# ===========================================================================


def _parse_security_results(raw_results: list[dict[str, Any]]) -> list[KrrDealResult]:
    """Parse `securityResult` list from a KRR response into KrrDealResult objects."""
    deals: list[KrrDealResult] = []
    for sec in raw_results:
        deal_id = sec.get("identifiers", {}).get("bloombergDealId", "")
        if sec.get("errorCode", 0) != 0:
            log.warning("KRR error for deal %s: %s", deal_id, sec.get("errorMessage", ""))
            continue

        ticker = ""
        for item in sec.get("pricingResult", []):
            if item.get("name") == "Ticker":
                ticker = item.get("value", {}).get("stringVal", "")
                break

        curves: list[KrrCurveResult] = []
        krr_result = sec.get("krrResult", {})
        for rr in krr_result.get("krrRiskResults", []):
            if rr.get("errorCode", 0) != 0:
                continue
            curveid = rr.get("curveid", "")
            underlying_ccy = rr.get("underlyingIRCurrency", "")
            val_ccy = rr.get("valuationCurrency", "")
            dv01_by_tenor: dict[str, float] = {
                b["ticker"]: b["krr"]
                for b in rr.get("krrs", [])
                if "ticker" in b and "krr" in b
            }
            curves.append(KrrCurveResult(
                curveid=curveid,
                underlying_currency=underlying_ccy,
                valuation_currency=val_ccy,
                dv01_by_tenor=dv01_by_tenor,
            ))

        deals.append(KrrDealResult(deal_id=deal_id, ticker=ticker, curves=curves))
    return deals


def _extract_security_results(resp: dict[str, Any]) -> list[dict[str, Any]]:
    """Drill into the standard pricingResultResponse wrapper."""
    try:
        return resp["results"][0]["pricingResultResponse"]["securityResult"]
    except (KeyError, IndexError):
        return []


# ===========================================================================
# Live repository
# ===========================================================================


class KrrLiveRepository:
    """Live Bloomberg MARS KRR pricing."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def run_deal_krr(
        self,
        deal_id: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult:
        body: dict[str, Any] = {
            "securitiesKrrRequest": {
                "pricingParameter": {
                    "valuationDate": str(valuation_date),
                    "requestedField": KRR_PRICING_FIELDS,
                    "useBbgRecommendedSettings": True,
                },
                "krrDefinition": {
                    "id": krr_def_id,
                    "externalName": krr_def_name,
                },
                "security": [
                    {"identifier": {"bloombergDealId": deal_id}, "position": 1}
                ],
            }
        }
        try:
            resp = self._client.send("POST", "/marswebapi/v1/securitiesKrr", body)
            if "error" in resp:
                return KrrResult(error=resp.get("error_description", str(resp["error"])))
            raw = _extract_security_results(resp)
            if not raw:
                return KrrResult(error="No KRR results returned for deal")
            deals = _parse_security_results(raw)
            return KrrResult(deals=deals)
        except MarsApiError as exc:
            return KrrResult(error=str(exc))

    def run_portfolio_krr(
        self,
        portfolio_name: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult:
        body: dict[str, Any] = {
            "pricingParameter": {
                "valuationDate": str(valuation_date),
                "requestedField": KRR_PRICING_FIELDS,
                "useBbgRecommendedSettings": True,
            },
            "krrDefinition": {
                "id": krr_def_id,
                "externalName": krr_def_name,
            },
            "portfolio": {
                "portfolioName": portfolio_name,
                "portfolioSource": "PORTFOLIO",
                "portfolioDate": str(valuation_date),
            },
        }
        try:
            resp = self._client.send("POST", "/enterprise/mars/portfolioKrr", body)
            if "error" in resp:
                return KrrResult(error=resp.get("error_description", str(resp["error"])))
            raw = _extract_security_results(resp)
            if not raw:
                return KrrResult(error="No KRR results returned for portfolio")
            deals = _parse_security_results(raw)
            return KrrResult(deals=deals)
        except MarsApiError as exc:
            return KrrResult(error=str(exc))


# ===========================================================================
# Demo repository
# ===========================================================================


class KrrDemoRepository:
    """Offline KRR with synthetic per-tenor DV01 buckets."""

    def run_deal_krr(
        self,
        deal_id: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult:
        usd_dv01 = [1.8, 0.0, 0.0, 0.0, -4.0, -33.0, -62.4, -95.3, -130.1, 4376.5, 0.0, 0.0]
        usd_curve = KrrCurveResult(
            curveid="S490",
            underlying_currency="USD",
            valuation_currency="USD",
            dv01_by_tenor=dict(zip(DEMO_KRR_TENORS_USD, usd_dv01)),
        )
        return KrrResult(deals=[
            KrrDealResult(deal_id=deal_id, ticker="/SWAP", curves=[usd_curve]),
        ])

    def run_portfolio_krr(
        self,
        portfolio_name: str,
        krr_def_id: str,
        krr_def_name: str,
        valuation_date: date,
    ) -> KrrResult:
        deals: list[KrrDealResult] = []

        # USD OIS deal
        usd_dv01 = [1.8, 0.0, 0.0, 0.0, -4.0, -33.0, -62.4, -95.3, -130.1, 4376.5, 0.0, 0.0]
        deals.append(KrrDealResult(
            deal_id="DEMO_USD_OIS",
            ticker="/SWAP",
            curves=[KrrCurveResult(
                curveid="S490", underlying_currency="USD", valuation_currency="USD",
                dv01_by_tenor=dict(zip(DEMO_KRR_TENORS_USD, usd_dv01)),
            )],
        ))

        # XCCY NDS deal — USD leg + local COP leg
        local_dv01 = [0.0, -2.6, -6.8, -12.1, -30.4, -60.7, -83.1, 947.3]
        usd_leg_dv01 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.56]
        deals.append(KrrDealResult(
            deal_id="DEMO_COP_XCCY",
            ticker="/NDS",
            curves=[
                KrrCurveResult(
                    curveid="S329", underlying_currency="COP", valuation_currency="COP",
                    dv01_by_tenor=dict(zip(DEMO_KRR_TENORS_LOCAL, local_dv01)),
                ),
                KrrCurveResult(
                    curveid="S490", underlying_currency="USD", valuation_currency="COP",
                    dv01_by_tenor=dict(zip(DEMO_KRR_TENORS_LOCAL, usd_leg_dv01)),
                ),
            ],
        ))

        return KrrResult(deals=deals)


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class KrrService:
    """
    Orchestrator for Key Rate Risk requests.

    Usage::

        svc = KrrService.from_settings()
        result = svc.run_deal_krr("SLLVJ42Q Corp", date.today())
        result = svc.run_portfolio_krr("MARS_VIBE_CODING", date.today())
    """

    def __init__(self, repository: KrrRepository) -> None:
        self._repo = repository

    def run_deal_krr(
        self,
        deal_id: str,
        valuation_date: date,
        krr_def_id: str = KRR_DEFINITION_ID,
        krr_def_name: str = KRR_DEFINITION_NAME,
    ) -> KrrResult:
        return self._repo.run_deal_krr(deal_id, krr_def_id, krr_def_name, valuation_date)

    def run_portfolio_krr(
        self,
        portfolio_name: str,
        valuation_date: date,
        krr_def_id: str = KRR_DEFINITION_ID,
        krr_def_name: str = KRR_DEFINITION_NAME,
    ) -> KrrResult:
        return self._repo.run_portfolio_krr(
            portfolio_name, krr_def_id, krr_def_name, valuation_date,
        )

    @classmethod
    def from_settings(cls) -> KrrService:
        if settings.demo_mode:
            return cls(KrrDemoRepository())
        client = MarsClient(settings)
        return cls(KrrLiveRepository(client))
