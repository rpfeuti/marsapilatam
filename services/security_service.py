"""
SecurityService — structure, price, solve, save deals and retrieve deal metadata.

Supports any MARS deal type (IR.*, FX.*, EQ.*, etc.).
All methods raise :class:`bloomberg.exceptions.MarsApiError` on failure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from bloomberg import pricing_result as pr
from bloomberg.exceptions import MarsApiError, PricingError, StructuringError
from bloomberg.webapi import MarsClient
from configs.settings import settings
from instruments.base import MarsInstrument


class SecurityService:
    """
    High-level service for single-security operations.

    A single :class:`MarsClient` is reused across calls. The underlying deal
    session is started lazily on the first call that needs it.
    """

    def __init__(self, client: MarsClient | None = None) -> None:
        self._client = client or MarsClient(settings)

    # ------------------------------------------------------------------
    # Deal lifecycle
    # ------------------------------------------------------------------

    def structure(self, body: dict[str, Any]) -> str:
        """
        Structure a temporary deal and return its ``dealHandle``.

        Injects the current deal session ID automatically.

        Args:
            body: A ``structureRequest`` dict (without ``sessionId`` — added automatically).

        Returns:
            The ``dealHandle`` string for use in subsequent price/solve/save calls.

        Raises:
            StructuringError: If the API returns an error.
        """
        body["sessionId"] = self._client.session_id
        response = self._client.send("POST", "/marswebapi/v1/deals/temporary", body)

        if "error" in response:
            raise StructuringError(response.get("error_description", str(response["error"])))

        try:
            return response["results"][0]["structureResponse"]["dealHandle"]
        except (KeyError, IndexError) as exc:
            raise StructuringError(f"Unexpected structure response: {response}") from exc

    def structure_instrument(
        self, instrument: MarsInstrument, requested_fields: list[str] | None = None
    ) -> str:
        """
        Convenience wrapper: structure a deal from a :class:`MarsInstrument` model.

        Args:
            instrument:       A ``Swap``, ``FxOption``, or ``EquityOption`` instance.
            requested_fields: Optional list of MARS field names to pre-configure.

        Returns:
            The ``dealHandle`` string.
        """
        from instruments.equity_option import EquityOption
        from instruments.fx_option import FxOption
        from instruments.swap import Swap

        if isinstance(instrument, Swap):
            deal_params, leg1_params, leg2_params = instrument.to_mars_params()
            body: dict[str, Any] = {
                "tail": instrument.deal_type,
                "dealStructureOverride": {
                    "param": deal_params,
                    "leg": [{"param": leg1_params}, {"param": leg2_params}],
                },
            }
        elif isinstance(instrument, (FxOption, EquityOption)):
            params = instrument.to_mars_params()
            body = {
                "tail": instrument.deal_type,
                "dealStructureOverride": {
                    "param": params,
                },
            }
        else:
            raise ValueError(f"Unsupported instrument type: {type(instrument)}")

        return self.structure(body)

    def price(self, body: dict[str, Any]) -> pd.DataFrame:
        """
        Price one or more securities.

        Args:
            body: A ``securitiesPricingRequest`` dict. The ``dealSession`` is
                  injected automatically.

        Returns:
            DataFrame with one row per security and one column per requested field.

        Raises:
            PricingError: If the API returns a pricing error.
        """
        pricing_params = body["securitiesPricingRequest"]["pricingParameter"]
        pricing_params["dealSession"] = self._client.session_id
        response = self._client.send("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return pr.to_dataframe(response)

    async def price_async(self, body: dict[str, Any]) -> pd.DataFrame:
        """Async version of :meth:`price`."""
        pricing_params = body["securitiesPricingRequest"]["pricingParameter"]
        pricing_params["dealSession"] = self._client.session_id
        response = await self._client.send_async("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return pr.to_dataframe(response)

    def solve(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        Solve for a target field (e.g. find the fixed rate that sets NPV to 0).

        Args:
            body: A ``solveRequest`` dict. The ``dealSession`` is injected automatically.

        Returns:
            The raw ``solveResponse`` dict from the API.

        Raises:
            PricingError: If the API returns an error.
        """
        body["solveRequest"]["dealSession"] = self._client.session_id
        response = self._client.send("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        try:
            return response["results"][0]["solveResponse"]
        except (KeyError, IndexError) as exc:
            raise PricingError(f"Unexpected solve response: {response}") from exc

    async def solve_async(self, body: dict[str, Any]) -> dict[str, Any]:
        """Async version of :meth:`solve`."""
        body["solveRequest"]["dealSession"] = self._client.session_id
        response = await self._client.send_async("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        try:
            return response["results"][0]["solveResponse"]
        except (KeyError, IndexError) as exc:
            raise PricingError(f"Unexpected solve response: {response}") from exc

    def save(self, deal_handle: str) -> str:
        """
        Persist a temporary deal and return the permanent ``dealId``.

        Args:
            deal_handle: The handle returned by :meth:`structure`.

        Returns:
            Bloomberg deal ID string.

        Raises:
            StructuringError: If saving fails.
        """
        response = self._client.send("PATCH", f"/marswebapi/v1/deals/temporary/{deal_handle}", {})

        if "error" in response:
            raise StructuringError(response.get("error_description", str(response["error"])))

        try:
            return response["results"][0]["saveResponse"]["dealId"]
        except (KeyError, IndexError) as exc:
            raise StructuringError(f"Unexpected save response: {response}") from exc

    # ------------------------------------------------------------------
    # Reference data
    # ------------------------------------------------------------------

    def get_terms_and_conditions(self, body: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve terms & conditions for a booked deal (e.g. by CUSIP).

        Returns the raw ``structureResponse`` dict.
        """
        body["sessionId"] = self._client.session_id
        response = self._client.send("POST", "/marswebapi/v1/deals/temporary", body)

        if "error" in response:
            raise MarsApiError(response.get("error_description", str(response["error"])))

        try:
            return response["results"][0]["structureResponse"]
        except (KeyError, IndexError) as exc:
            raise MarsApiError(f"Unexpected response: {response}") from exc

    def get_deal_schema(self, deal_type: str) -> pd.DataFrame:
        """
        Return the parameter schema for a given deal type as a DataFrame.

        Columns: ``name``, ``description``, ``mode``, ``solvableTarget``, ``category``.
        """
        response = self._client.send("GET", "/marswebapi/v1/dealSchema", {"tail": deal_type})

        if "error" in response:
            raise MarsApiError(response.get("error_description", str(response["error"])))

        try:
            params = response["schemaResponse"]["dealStructure"]["param"]
        except KeyError as exc:
            raise MarsApiError(f"Unexpected schema response: {response}") from exc

        return pd.DataFrame(
            params,
            columns=["name", "value", "description", "mode", "solvableTarget", "category"],
        ).set_index("name")

    def get_deal_types(self) -> pd.DataFrame:
        """Return all available deal types as a DataFrame."""
        response = self._client.send("GET", "/marswebapi/v1/dealType", {"voidName": ""})

        if "error" in response:
            raise MarsApiError(response.get("error_description", str(response["error"])))

        try:
            deal_types = response["getDealTypesResponse"]["dealType"]
        except KeyError as exc:
            raise MarsApiError(f"Unexpected deal types response: {response}") from exc

        return pd.DataFrame(deal_types)
