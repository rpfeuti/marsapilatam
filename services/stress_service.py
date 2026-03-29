"""
IRRBB stress testing service.

Creates SHOC scenarios via the MARS API, prices a deal under each scenario,
and returns base-case vs stressed metrics for comparison.

Architecture:
    StressScenario      -- one scenario: name + per-tenor bp shifts
    StressResult        -- base-case + per-scenario pricing results
    StressRepository    -- structural Protocol
    StressLiveRepository -- live Bloomberg MARS implementation
    StressDemoRepository -- offline demo-data implementation
    StressService       -- thin orchestrator with from_settings() factory

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

from bloomberg import pricing_result as pr
from bloomberg.exceptions import MarsApiError
from bloomberg.webapi import MarsClient
from configs.settings import settings
from configs.stress_config import (
    IRRBB_MATRIX,
    IRRBB_SCENARIOS,
    STRESS_PRICING_FIELDS,
    STRESS_SCENARIO_FIELDS,
)

log = logging.getLogger(__name__)


# ===========================================================================
# Value objects
# ===========================================================================


@dataclass
class StressScenario:
    """One IRRBB scenario: a named swap-curve shift with per-tenor bp values."""

    name: str
    tenor_shifts: dict[str, float]  # {tenor_label: shift_bp}
    currency: str = "USD"


@dataclass
class ScenarioOutput:
    """Pricing results for a single scenario."""

    name: str
    tenor_shifts: dict[str, float]
    metrics: dict[str, str] = field(default_factory=dict)


@dataclass
class StressResult:
    """Full stress test output: base case + all scenarios."""

    base_metrics: dict[str, str] = field(default_factory=dict)
    scenario_results: list[ScenarioOutput] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ===========================================================================
# Repository Protocol
# ===========================================================================


class StressRepository(Protocol):
    def run_stress_test(
        self,
        deal_id: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult: ...


# ===========================================================================
# Live repository
# ===========================================================================


class StressLiveRepository:
    """Live Bloomberg MARS stress testing via SHOC scenarios."""

    def __init__(self, client: MarsClient) -> None:
        self._client = client

    def _create_scenario(
        self,
        name: str,
        description: str,
        currency: str,
        tenor_shifts: dict[str, float],
    ) -> str:
        """Create a SHOC scenario with per-tenor swapCurveShift nodes and return its ID.

        The shiftWhat filter uses Bloomberg's key=value syntax:
            "Currency=USD,Tenor=1Y"  — shifts only the 1Y tenor of USD swap curve.
        Absolute mode with bp values (200 = +200bp).
        """
        shift_nodes = [
            {
                "shiftWhat": f"Currency={currency},Tenor={tenor}",
                "shiftMode": {"absolute": {}},
                "shiftValue": {"scalarShift": shift_bp},
            }
            for tenor, shift_bp in tenor_shifts.items()
            if shift_bp != 0.0
        ]

        if not shift_nodes:
            # If all tenors are 0 bp, create a no-op scenario (zero scalar shift).
            shift_nodes = [
                {
                    "shiftWhat": f"Currency={currency}",
                    "shiftMode": {"absolute": {}},
                    "shiftValue": {"scalarShift": 0.0},
                }
            ]

        body: dict[str, Any] = {
            "createScenarioRequest": {
                "scenario": {
                    "header": {
                        "name": name,
                        "description": description,
                    },
                    "setting": {},
                    "content": {
                        "regularScenario": {
                            "swapCurveShift": shift_nodes,
                        }
                    },
                }
            }
        }
        resp = self._client.send("POST", "/marswebapi/v1/scenarios", body)
        create_resp = (
            resp.get("scenarioResponse", {})
                .get("createScenarioResponse", {})
        )
        scenario_id = create_resp.get("scenarioId", "")
        status = create_resp.get("returnStatus", {}).get("status", "")
        if not scenario_id or status == "S_FAILURE":
            raise MarsApiError(f"Failed to create scenario '{name}': {resp}")
        log.info("Created SHOC scenario %s (%s)", scenario_id, name)
        return scenario_id

    def _delete_scenarios(self, scenario_ids: list[str]) -> None:
        """Delete SHOC scenarios by ID (best-effort cleanup)."""
        if not scenario_ids:
            return
        body: dict[str, Any] = {
            "deleteScenariosRequest": {
                "scenarioIds": scenario_ids,
            }
        }
        try:
            self._client.send("DELETE", "/marswebapi/v1/scenarios", body)
            log.info("Deleted %d SHOC scenarios", len(scenario_ids))
        except MarsApiError:
            log.warning("Failed to delete scenarios %s (non-fatal)", scenario_ids)

    def _price_with_scenarios(
        self,
        deal_id: str,
        scenario_ids: list[str],
        valuation_date: date,
    ) -> dict[str, Any]:
        """Price a deal with base case + scenario overlays."""
        body: dict[str, Any] = {
            "securitiesPricingRequest": {
                "pricingParameter": {
                    "valuationDate": str(valuation_date),
                    "requestedField": STRESS_PRICING_FIELDS,
                    "useBbgRecommendedSettings": True,
                },
                "scenarioParameter": {
                    "scenario": [{"scenarioId": sid} for sid in scenario_ids],
                    "requestedField": STRESS_SCENARIO_FIELDS,
                },
                "security": [
                    {
                        "identifier": {"bloombergDealId": deal_id},
                        "position": 1,
                    }
                ],
            }
        }
        return self._client.send(
            "POST", "/marswebapi/v1/securitiesPricing", body,
        )

    def _price_portfolio_with_scenarios(
        self,
        portfolio_name: str,
        scenario_ids: list[str],
        valuation_date: date,
    ) -> dict[str, Any]:
        """Price an entire portfolio under base case + scenario overlays."""
        body: dict[str, Any] = {
            "portfolioPricingRequest": {
                "pricingParameter": {
                    "valuationDate": str(valuation_date),
                    "requestedField": STRESS_PRICING_FIELDS,
                    "useBbgRecommendedSettings": True,
                },
                "scenarioParameter": {
                    "scenario": [{"scenarioId": sid} for sid in scenario_ids],
                    "requestedField": STRESS_SCENARIO_FIELDS,
                },
                "portfolioDescription": {
                    "portfolioName": portfolio_name,
                    "portfolioSource": "PORTFOLIO",
                },
            }
        }
        return self._client.send("POST", "/marswebapi/v1/portfolioPricing", body)

    def run_portfolio_stress_test(
        self,
        portfolio_name: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        created_ids: list[str] = []
        id_to_scenario: dict[str, StressScenario] = {}

        try:
            for sc in scenarios:
                sid = self._create_scenario(
                    name=sc.name,
                    description=f"IRRBB {sc.name} - per-tenor absolute swap curve shift ({sc.currency})",
                    currency=sc.currency,
                    tenor_shifts=sc.tenor_shifts,
                )
                created_ids.append(sid)
                id_to_scenario[sid] = sc

            resp = self._price_portfolio_with_scenarios(portfolio_name, created_ids, valuation_date)

            if "error" in resp:
                return StressResult(error=resp.get("error_description", str(resp["error"])))

            raw_results = pr.get_security_results(resp)
            if not raw_results:
                prr_items = [
                    item.get("pricingResultResponse", {})
                    for item in resp.get("results", [])
                    if "pricingResultResponse" in item
                ]
                prr = prr_items[0] if prr_items else {}
                return StressResult(
                    error=f"No pricing results. errorCode={prr.get('errorCode', 'n/a')}, "
                          f"errorMessage={prr.get('errorMessage', '')!r}"
                )

            # Aggregate base-case and scenario fields across all deals in the portfolio.
            base_totals: dict[str, float] = {}
            scenario_totals: dict[str, dict[str, float]] = {}

            for raw in raw_results:
                sec = pr.parse_security(raw)
                if sec.error_message:
                    continue
                for fname, val_str in sec.fields.items():
                    try:
                        base_totals[fname] = base_totals.get(fname, 0.0) + float(val_str)
                    except (ValueError, TypeError):
                        pass
                for scenario_entry in sec.scenarios:
                    for sid, fields in scenario_entry.items():
                        if sid not in scenario_totals:
                            scenario_totals[sid] = {}
                        for fname, val_str in fields.items():
                            try:
                                scenario_totals[sid][fname] = (
                                    scenario_totals[sid].get(fname, 0.0) + float(val_str)
                                )
                            except (ValueError, TypeError):
                                pass

            base_metrics = {k: str(v) for k, v in base_totals.items()}
            scenario_outputs: list[ScenarioOutput] = []
            for sid in created_ids:
                sc = id_to_scenario.get(sid)
                if sc:
                    totals = scenario_totals.get(sid, {})
                    scenario_outputs.append(ScenarioOutput(
                        name=sc.name,
                        tenor_shifts=sc.tenor_shifts,
                        metrics={k: str(v) for k, v in totals.items()},
                    ))

            return StressResult(base_metrics=base_metrics, scenario_results=scenario_outputs)

        except MarsApiError as exc:
            return StressResult(error=str(exc))

        finally:
            self._delete_scenarios(created_ids)

    def run_stress_test(
        self,
        deal_id: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        created_ids: list[str] = []
        id_to_scenario: dict[str, StressScenario] = {}

        try:
            for sc in scenarios:
                sid = self._create_scenario(
                    name=sc.name,
                    description=f"IRRBB {sc.name} - per-tenor absolute swap curve shift ({sc.currency})",
                    currency=sc.currency,
                    tenor_shifts=sc.tenor_shifts,
                )
                created_ids.append(sid)
                id_to_scenario[sid] = sc

            resp = self._price_with_scenarios(deal_id, created_ids, valuation_date)

            if "error" in resp:
                return StressResult(
                    error=resp.get("error_description", str(resp["error"])),
                )

            raw_results = pr.get_security_results(resp)
            if not raw_results:
                prr = resp.get("results", [{}])[0].get("pricingResultResponse", {})
                err_code = prr.get("errorCode", "n/a")
                err_msg = prr.get("errorMessage", "")
                sec_results = prr.get("securityResult", [])
                return StressResult(
                    error=f"No pricing results returned. "
                          f"errorCode={err_code}, errorMessage={err_msg!r}, "
                          f"securityResult count={len(sec_results)}, "
                          f"pricingResultResponse keys={list(prr.keys())}"
                )

            sec = pr.parse_security(raw_results[0])
            if sec.error_message:
                return StressResult(error=sec.error_message)

            scenario_outputs: list[ScenarioOutput] = []
            for scenario_entry in sec.scenarios:
                for sid, fields in scenario_entry.items():
                    sc = id_to_scenario.get(sid)
                    if sc:
                        scenario_outputs.append(ScenarioOutput(
                            name=sc.name,
                            tenor_shifts=sc.tenor_shifts,
                            metrics=fields,
                        ))

            return StressResult(
                base_metrics=sec.fields,
                scenario_results=scenario_outputs,
            )

        except MarsApiError as exc:
            return StressResult(error=str(exc))

        finally:
            self._delete_scenarios(created_ids)


# ===========================================================================
# Demo repository
# ===========================================================================


class StressDemoRepository:
    """Offline demo stress test with hardcoded results."""

    def run_portfolio_stress_test(
        self,
        portfolio_name: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        base = {
            "MktValPortCcy": "0.00",
            "DV01PortCcy": "21345.75",
        }
        outputs: list[ScenarioOutput] = []
        for sc in scenarios:
            shifts = list(sc.tenor_shifts.values())
            avg_bp = sum(shifts) / len(shifts) if shifts else 0.0
            factor = avg_bp / 100.0
            mtm = -21345.75 * factor
            outputs.append(ScenarioOutput(
                name=sc.name,
                tenor_shifts=sc.tenor_shifts,
                metrics={
                    "MktValPortCcy": f"{mtm:.2f}",
                    "DV01PortCcy": f"{21345.75 * (1 - abs(factor) * 0.02):.2f}",
                    "Delta": "0.00",
                },
            ))
        return StressResult(base_metrics=base, scenario_results=outputs)

    def run_stress_test(
        self,
        deal_id: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        base = {
            "MktValPortCcy": "0.00",
            "DV01PortCcy": "4523.15",
            "PV01": "4510.00",
            "MktPx": "100.00",
            "AccruedInterest": "1250.00",
            "Delta": "0.00",
        }
        outputs: list[ScenarioOutput] = []
        for sc in scenarios:
            shifts = list(sc.tenor_shifts.values())
            avg_bp = sum(shifts) / len(shifts) if shifts else 0.0
            factor = avg_bp / 100.0
            mtm = -4523.15 * factor
            outputs.append(ScenarioOutput(
                name=sc.name,
                tenor_shifts=sc.tenor_shifts,
                metrics={
                    "MktValPortCcy": f"{mtm:.2f}",
                    "DV01PortCcy": f"{4523.15 * (1 - abs(factor) * 0.02):.2f}",
                    "PV01": f"{4510.00 * (1 - abs(factor) * 0.02):.2f}",
                    "Delta": "0.00",
                },
            ))
        return StressResult(base_metrics=base, scenario_results=outputs)


# ===========================================================================
# Service (orchestrator)
# ===========================================================================


class StressService:
    """Orchestrator for IRRBB stress testing."""

    def __init__(self, repository: StressRepository) -> None:
        self._repo = repository

    def run_stress_test(
        self,
        deal_id: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        return self._repo.run_stress_test(deal_id, scenarios, valuation_date)

    def run_portfolio_stress_test(
        self,
        portfolio_name: str,
        scenarios: list[StressScenario],
        valuation_date: date,
    ) -> StressResult:
        return self._repo.run_portfolio_stress_test(portfolio_name, scenarios, valuation_date)

    @classmethod
    def default_scenarios(cls) -> list[StressScenario]:
        """Return the 6 IRRBB preset scenarios with per-tenor shifts from IRRBB_MATRIX."""
        return [
            StressScenario(
                name=name,
                tenor_shifts=dict(IRRBB_MATRIX[name]),
            )
            for name in IRRBB_SCENARIOS
        ]

    @classmethod
    def from_settings(cls) -> StressService:
        if settings.demo_mode:
            return cls(StressDemoRepository())
        client = MarsClient(settings)
        return cls(StressLiveRepository(client))
