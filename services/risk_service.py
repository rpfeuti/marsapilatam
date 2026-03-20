"""
RiskService — Key Rate Risk (KRR) calculations via the Bloomberg MARS API.

KRR measures the sensitivity of a deal's value to shifts in individual
points on the yield curve (e.g. 1M, 3M, 1Y, 5Y, 10Y, 30Y buckets).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from bloomberg import pricing_result as pr
from bloomberg.exceptions import PricingError
from bloomberg.webapi import MarsClient
from configs.settings import settings

# Default KRR definition from the old project:
# tenor mode, two-sided, bump: 10bp
# tenors: 1M, 2M, 3M, 18M, 1Y, 2Y, 3Y, 4Y, 5Y, 10Y, 15Y, 20Y, 30Y
_DEFAULT_KRR_DEFINITION_ID = "7238983182415036420"


class RiskService:
    """
    Service for Key Rate Risk calculations.

    Args:
        client: Optional pre-constructed :class:`MarsClient`.
    """

    def __init__(self, client: MarsClient | None = None) -> None:
        self._client = client or MarsClient(settings)

    def key_rate_risk(
        self,
        valuation_date: date | str,
        identifiers: list[dict[str, Any]],
        requested_fields: list[str],
        krr_definition_id: str = _DEFAULT_KRR_DEFINITION_ID,
    ) -> pd.DataFrame:
        """
        Calculate Key Rate Risk for one or more securities.

        Args:
            valuation_date:    Pricing date as a ``date`` object or ISO string.
            identifiers:       List of identifier dicts, e.g.
                               ``[{"dealHandle": "ABC123"}]`` or
                               ``[{"bloombergDealId": "IBM 2.85 05/15/2040 Corp"}]``.
            requested_fields:  MARS field names to include in the result.
            krr_definition_id: Bloomberg KRR definition ID (controls tenors and bump size).

        Returns:
            DataFrame with columns: ``BloombergDealID``, ``valuationCurrency``,
            ``underlyingIRCurrency``, plus one column per KRR tenor.

        Raises:
            PricingError: If the API returns a pricing error.
        """
        val_date_str = str(valuation_date) if isinstance(valuation_date, date) else valuation_date

        body: dict[str, Any] = {
            "securitiesKrrRequest": {
                "pricingParameter": {
                    "valuationDate": val_date_str,
                    "requestedField": requested_fields,
                },
                "krrDefinition": {
                    "id": krr_definition_id,
                    "externalName": "",
                },
                "security": [{"identifier": ident} for ident in identifiers],
            }
        }

        response = self._client.send("POST", "/marswebapi/v1/securitiesKrr", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return self._parse_krr_response(response)

    async def key_rate_risk_async(
        self,
        valuation_date: date | str,
        identifiers: list[dict[str, Any]],
        requested_fields: list[str],
        krr_definition_id: str = _DEFAULT_KRR_DEFINITION_ID,
    ) -> pd.DataFrame:
        """Async version of :meth:`key_rate_risk`."""
        val_date_str = str(valuation_date) if isinstance(valuation_date, date) else valuation_date

        body: dict[str, Any] = {
            "securitiesKrrRequest": {
                "pricingParameter": {
                    "valuationDate": val_date_str,
                    "requestedField": requested_fields,
                },
                "krrDefinition": {
                    "id": krr_definition_id,
                    "externalName": "",
                },
                "security": [{"identifier": ident} for ident in identifiers],
            }
        }

        response = await self._client.send_async("POST", "/marswebapi/v1/securitiesKrr", body)

        if "error" in response:
            raise PricingError(response.get("error_description", str(response["error"])))

        return self._parse_krr_response(response)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_krr_response(response: dict[str, Any]) -> pd.DataFrame:
        security_results = pr._get_security_results(response)

        if not security_results:
            raise PricingError("KRR response contained no security results.")

        rows: list[dict[str, Any]] = []
        for security in security_results:
            identifiers = security.get("identifiers", {})
            deal_id = (
                identifiers.get("bloombergDealId")
                or identifiers.get("bloombergUniqueId")
                or identifiers.get("dealHandle")
                or ""
            )

            if "errorMessage" in security:
                rows.append({"BloombergDealID": deal_id, "errorMessage": security["errorMessage"]})
                continue

            krr_risk_results: list[dict[str, Any]] = (
                security.get("krrResult", {}).get("krrRiskResults", [])
            )

            for risk in krr_risk_results:
                valuation_currency = risk.get("valuationCurrency", "")
                underlying_ir_currency = risk.get("underlyingIRCurrency", valuation_currency)

                for krr in risk.get("krrs", []):
                    row: dict[str, Any] = {
                        "BloombergDealID": deal_id,
                        "valuationCurrency": valuation_currency,
                        "underlyingIRCurrency": underlying_ir_currency,
                    }
                    row.update(krr)
                    rows.append(row)

        return pd.DataFrame(rows)
