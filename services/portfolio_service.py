"""
Portfolio pricing service.

Price any named Bloomberg portfolio via portfolioPricingRequest and
aggregate per-deal results into portfolio-level risk metrics.

Architecture:
    PortfolioResult         — result of the pricing phase
    PortfolioRepository     — structural Protocol
    PortfolioLiveRepository — live Bloomberg MARS implementation
    PortfolioDemoRepository — offline demo-data implementation
    PortfolioPricingService — thin orchestrator with from_settings() factory

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

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from bloomberg import pricing_result as pr
from bloomberg.exceptions import MarsApiError, PricingError
from bloomberg.webapi import MarsClient
from configs.portfolio_config import MARS_API_FIELDS, PORTFOLIO_NAME
from configs.settings import settings

log = logging.getLogger(__name__)

_DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"

_PORTFOLIO_PRICING_FIELDS = list(MARS_API_FIELDS.keys())

_NUMERIC_AGGREGATE_FIELDS = [
    "MktValPortCcy", "DV01PortCcy", "PV01",
    "Notional", "Delta", "Gamma", "Vega", "Theta",
]


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass
class PortfolioResult:
    """Result of the portfolio pricing phase."""

    deals: list[dict[str, str]] = field(default_factory=list)
    aggregate: dict[str, float] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.deals)


# ===========================================================================
# Repository Protocol
# ===========================================================================


class PortfolioRepository(Protocol):
    def list_portfolios(self) -> list[str]: ...
    def price_portfolio(
        self, portfolio_name: str, valuation_date: date,
    ) -> PortfolioResult: ...


# ===========================================================================
# Pure helper functions
# ===========================================================================


def _aggregate_metrics(deals: list[dict[str, str]]) -> dict[str, float]:
    """Sum numeric fields across all deals."""
    totals: dict[str, float] = {}
    for field_name in _NUMERIC_AGGREGATE_FIELDS:
        total = 0.0
        for deal in deals:
            raw = deal.get(field_name, "")
            if raw:
                try:
                    total += float(raw)
                except (ValueError, TypeError):
                    pass
        totals[field_name] = total
    totals["DealCount"] = float(len(deals))
    return totals


# ===========================================================================
# Repository implementations
# ===========================================================================


class PortfolioLiveRepository:
    """Live Bloomberg MARS portfolio pricing."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def list_portfolios(self) -> list[str]:
        """Fetch existing portfolio IDs via the enterprise endpoint.

        Returns an empty list if the endpoint is unavailable (401/403).
        """
        try:
            resp = self._client.send(
                "GET", "/enterprise/common/portfolio-ids",
            )
            return resp.get("portfolioIds", [])
        except MarsApiError:
            log.warning(
                "Could not list portfolios — enterprise endpoint unavailable",
            )
            return []

    def price_portfolio(
        self, portfolio_name: str, valuation_date: date,
    ) -> PortfolioResult:
        """Price a named portfolio via portfolioPricingRequest."""
        body: dict[str, Any] = {
            "portfolioPricingRequest": {
                "pricingParameter": {
                    "valuationDate":             str(valuation_date),
                    "requestedField":            _PORTFOLIO_PRICING_FIELDS,
                    "portfolioCurrency":         "USD",
                    "useBbgRecommendedSettings": True,
                },
                "portfolioDescription": {
                    "portfolioName":  portfolio_name,
                    "portfolioSource": "PORTFOLIO",
                    "portfolioDate":  str(valuation_date),
                },
            }
        }

        resp = self._client.send(
            "POST", "/marswebapi/v1/portfolioPricing", body,
        )

        if "error" in resp:
            raise PricingError(
                resp.get("error_description", str(resp["error"])),
            )

        records = pr.to_records(resp)

        for record in records:
            label = (
                record.get("Ticker")
                or record.get("BloombergDealID")
                or "—"
            )
            record.setdefault("_label", label)

        aggregate = _aggregate_metrics(records)
        return PortfolioResult(deals=records, aggregate=aggregate)


class PortfolioDemoRepository:
    """Offline portfolio backed by existing demo snapshots."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def list_portfolios(self) -> list[str]:
        return [PORTFOLIO_NAME]

    def price_portfolio(
        self, portfolio_name: str, valuation_date: date,
    ) -> PortfolioResult:
        from configs.portfolio_config import PORTFOLIO_DEALS

        records: list[dict[str, str]] = []

        for deal_def in PORTFOLIO_DEALS:
            subdir = self._data_dir / deal_def.demo_subdir
            path = subdir / deal_def.demo_filename
            if not path.exists():
                log.warning("Demo snapshot not found: %s", path)
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                metrics = payload.get("metrics", {})
                metrics["_label"] = deal_def.label
                records.append(metrics)
            except Exception as exc:
                log.warning("Failed to load %s: %s", path, exc)

        aggregate = _aggregate_metrics(records)
        return PortfolioResult(deals=records, aggregate=aggregate)


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class PortfolioPricingService:
    """
    Orchestrator for portfolio pricing.

    Usage::

        svc = PortfolioPricingService.from_settings()
        portfolios = svc.list_portfolios()
        result = svc.price_portfolio("MARS_VIBE_CODING", date.today())
    """

    def __init__(self, repository: PortfolioRepository) -> None:
        self._repo = repository

    def list_portfolios(self) -> list[str]:
        return self._repo.list_portfolios()

    def price_portfolio(
        self, portfolio_name: str, valuation_date: date,
    ) -> PortfolioResult:
        return self._repo.price_portfolio(portfolio_name, valuation_date)

    @classmethod
    def from_settings(cls) -> PortfolioPricingService:
        if settings.demo_mode:
            return cls(PortfolioDemoRepository(_DEMO_DATA_DIR))
        client = MarsClient(settings)
        return cls(PortfolioLiveRepository(client))
