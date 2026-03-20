"""
PortfolioService — create and price Bloomberg MARS portfolios.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from bloomberg import pricing_result as pr
from bloomberg.exceptions import MarsApiError, PricingError
from bloomberg.webapi import MarsClient
from configs.settings import settings


class PortfolioService:
    """
    Service for portfolio-level operations against the Bloomberg MARS API.

    Args:
        client: Optional pre-constructed :class:`MarsClient`.
    """

    def __init__(self, client: MarsClient | None = None) -> None:
        self._client = client or MarsClient(settings)

    def create(self, body: dict[str, Any]) -> str:
        """
        Create a new Bloomberg portfolio.

        Args:
            body: A ``createPortfolioRequest`` dict.

        Returns:
            The ``portfolioId`` string assigned by Bloomberg.

        Raises:
            MarsApiError: On API error.
        """
        response = self._client.send("POST", "/enterprise/common/portfolios", body)

        if "error" in response:
            raise MarsApiError(response.get("error_description", str(response["error"])))

        try:
            return response["createPortfolioResponse"]["portfolioId"]
        except KeyError as exc:
            raise MarsApiError(f"Unexpected create portfolio response: {response}") from exc

    def price(self, body: dict[str, Any]) -> pd.DataFrame:
        """
        Price a portfolio and return results as a DataFrame.

        Args:
            body: A ``portfolioPricingRequest`` dict.

        Returns:
            DataFrame with one row per security.

        Raises:
            PricingError: On pricing failure.
        """
        response = self._client.send("POST", "/marswebapi/v1/portfolioPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return pr.to_dataframe(response)

    async def price_async(self, body: dict[str, Any]) -> pd.DataFrame:
        """Async version of :meth:`price`."""
        response = await self._client.send_async("POST", "/marswebapi/v1/portfolioPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return pr.to_dataframe(response)
