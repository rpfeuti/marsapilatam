"""
MARS API response parsers.

Converts raw JSON pricing responses into clean Python structures and DataFrames.

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

from typing import Any

import pandas as pd
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class PricingField(BaseModel):
    name: str
    value: dict[str, Any]

    def as_scalar(self) -> str:
        """Return the value as a plain string regardless of the inner type key."""
        v = self.value
        for key in ("doubleVal", "stringVal", "dateVal", "intVal"):
            if key in v:
                return str(v[key])
        if "selectionVal" in v:
            return str(v["selectionVal"].get("value", ""))
        return ""


class SecurityResult(BaseModel):
    bloomberg_deal_id: str = ""
    portfolio: str = ""
    fields: dict[str, str] = {}
    cashflows: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    error_message: str = ""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _get_security_results(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the list of raw securityResult dicts from a pricing response."""
    results: list[dict[str, Any]] = []
    for item in response.get("results", []):
        if "pricingResultResponse" in item:
            results.extend(item["pricingResultResponse"].get("securityResult", []))
    return results


def _parse_pricing_fields(params: list[dict[str, Any]]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for param in params:
        field = PricingField.model_validate(param)
        parsed[field.name] = field.as_scalar()
    return parsed


def _parse_security(raw: dict[str, Any]) -> SecurityResult:
    result = SecurityResult()

    if "errorMessage" in raw:
        result.error_message = raw["errorMessage"]

    if "pricingResult" in raw:
        result.fields = _parse_pricing_fields(raw["pricingResult"])

    identifiers = raw.get("identifiers", {})
    if "BloombergDealID" not in result.fields:
        result.bloomberg_deal_id = (
            identifiers.get("bloombergDealId")
            or identifiers.get("bloombergUniqueId")
            or ""
        )
    else:
        result.bloomberg_deal_id = result.fields.pop("BloombergDealID")

    if "portfolioSourceDetails" in raw:
        psd = raw["portfolioSourceDetails"]
        result.portfolio = f"{psd.get('portfolioSource', '')}:{psd.get('portfolioName', '')}"

    if "cashflowResult" in raw:
        result.cashflows = [
            {
                "paymentType": str(cf.get("paymentType", "")),
                "paymentDate": cf.get("paymentDate", ""),
                "currency": cf.get("currency", ""),
                "amount": cf.get("amount", 0),
            }
            for cf in raw["cashflowResult"]
        ]

    if "scenarioResult" in raw:
        for sr in raw["scenarioResult"]:
            scenario_id = sr.get("scenario", {}).get("scenarioId", "")
            fields = _parse_pricing_fields(sr.get("pricingResult", []))
            result.scenarios.append({scenario_id: fields})

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_security_results(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the list of raw securityResult dicts from a pricing response."""
    return _get_security_results(response)


def parse_security(raw: dict[str, Any]) -> SecurityResult:
    """Parse a single raw securityResult dict into a SecurityResult."""
    return _parse_security(raw)


def to_records(response: dict[str, Any]) -> list[dict[str, str]]:
    """
    Parse a MARS pricing response into a list of flat dicts (one per security).
    Each dict has the security identifier plus all priced fields.
    """
    records: list[dict[str, str]] = []
    for raw in _get_security_results(response):
        sec = _parse_security(raw)
        row: dict[str, str] = {"BloombergDealID": sec.bloomberg_deal_id}
        if sec.portfolio:
            row["Portfolio"] = sec.portfolio
        if sec.error_message:
            row["errorMessage"] = sec.error_message
        row.update(sec.fields)
        records.append(row)
    return records


def to_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """Return a :class:`pandas.DataFrame` from a MARS pricing response."""
    return pd.DataFrame(to_records(response))
