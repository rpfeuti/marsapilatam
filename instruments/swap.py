"""
Swap instrument model for the Bloomberg MARS API.

Supports all IR.* deal types: plain vanilla IRS, OIS, NDS, NDSFX, FXFL, etc.
Each leg's parameters are built separately because MARS expects them in a
``legs`` list inside the ``structureRequest``.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import model_validator

from instruments.base import MarsInstrument, MarsParam


class Swap(MarsInstrument):
    """
    Bloomberg MARS swap instrument.

    Only required fields are ``deal_type``, ``effective_date``, and
    ``maturity_date``. All other fields are optional — omit any field that
    MARS should derive from its defaults or from the deal type definition.
    """

    deal_type: str
    effective_date: date
    maturity_date: date

    # Deal-level parameters
    csa_collateral_currency: str | None = None
    settlement_currency: str | None = None

    # Leg 1
    leg1_direction: Literal["Pay", "Receive"] | None = None
    leg1_notional: float | None = None
    leg1_currency: str | None = None
    leg1_spread: float | None = None
    leg1_fixed_rate: float | None = None
    leg1_floating_index: str | None = None
    leg1_pay_frequency: str | None = None
    leg1_day_count: str | None = None
    leg1_forward_curve: str | None = None
    leg1_discount_curve: str | None = None

    # Leg 2
    leg2_direction: Literal["Pay", "Receive"] | None = None
    leg2_notional: float | None = None
    leg2_currency: str | None = None
    leg2_spread: float | None = None
    leg2_fixed_rate: float | None = None
    leg2_floating_index: str | None = None
    leg2_pay_frequency: str | None = None
    leg2_day_count: str | None = None
    leg2_forward_curve: str | None = None
    leg2_discount_curve: str | None = None

    @model_validator(mode="after")
    def _effective_before_maturity(self) -> Swap:
        if self.maturity_date <= self.effective_date:
            raise ValueError("maturity_date must be after effective_date")
        return self

    def to_mars_params(self) -> tuple[list[MarsParam], list[MarsParam], list[MarsParam]]:
        """
        Return ``(deal_params, leg1_params, leg2_params)`` ready for the
        MARS ``structureRequest``.
        """
        deal: list[MarsParam] = []
        leg1: list[MarsParam] = []
        leg2: list[MarsParam] = []

        # Deal-level
        if self.settlement_currency:
            deal.append(self._str_param("SettlementCurrency", self.settlement_currency))
        if self.csa_collateral_currency:
            deal.append(self._str_param("CSACollateralCurrency", self.csa_collateral_currency))

        eff = self.effective_date.strftime("%Y-%m-%d")
        mat = self.maturity_date.strftime("%Y-%m-%d")

        def _build_leg(
            direction: str | None,
            notional: float | None,
            currency: str | None,
            spread: float | None,
            fixed_rate: float | None,
            floating_index: str | None,
            pay_frequency: str | None,
            day_count: str | None,
            forward_curve: str | None,
            discount_curve: str | None,
        ) -> list[MarsParam]:
            params: list[MarsParam] = []
            if direction:
                params.append(self._selection_param("Direction", direction))
            if notional is not None:
                params.append(self._double_param("Notional", notional))
            if currency:
                params.append(self._str_param("Currency", currency))
            params.append(self._date_param("EffectiveDate", eff))
            params.append(self._date_param("MaturityDate", mat))
            if fixed_rate is not None:
                params.append(self._double_param("FixedRate", fixed_rate))
            if spread is not None:
                params.append(self._double_param("Spread", spread))
            if floating_index:
                params.append(self._str_param("FloatingIndex", floating_index))
            if pay_frequency:
                params.append(self._selection_param("PayFrequency", pay_frequency))
            if day_count:
                params.append(self._selection_param("DayCount", day_count))
            if forward_curve:
                params.append(self._str_param("ForwardCurve", forward_curve))
            if discount_curve:
                params.append(self._str_param("DiscountCurve", discount_curve))
            return params

        leg1 = _build_leg(
            self.leg1_direction,
            self.leg1_notional,
            self.leg1_currency,
            self.leg1_spread,
            self.leg1_fixed_rate,
            self.leg1_floating_index,
            self.leg1_pay_frequency,
            self.leg1_day_count,
            self.leg1_forward_curve,
            self.leg1_discount_curve,
        )
        leg2 = _build_leg(
            self.leg2_direction,
            self.leg2_notional,
            self.leg2_currency,
            self.leg2_spread,
            self.leg2_fixed_rate,
            self.leg2_floating_index,
            self.leg2_pay_frequency,
            self.leg2_day_count,
            self.leg2_forward_curve,
            self.leg2_discount_curve,
        )

        return deal, leg1, leg2
