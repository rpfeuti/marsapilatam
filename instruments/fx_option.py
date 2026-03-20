"""
FX vanilla option instrument model for the Bloomberg MARS API.

Backed by the ``FX.VA`` deal type (Bloomberg OVML).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from instruments.base import MarsInstrument, MarsParam


class FxOption(MarsInstrument):
    """
    FX vanilla option for the Bloomberg MARS API.

    Example::

        opt = FxOption(
            deal_type="FX.VA",
            call_put="Call",
            call_put_currency="USD",
            direction="Buy",
            exercise_type="European",
            underlying_ticker="CLPUSD",
            strike=1000.0,
            notional=5_000_000.0,
            notional_currency="USD",
            expiry_date=date(2024, 12, 31),
            settlement_date=date(2025, 1, 2),
            settlement_type="Cash",
            settlement_currency="CLP",
        )
    """

    deal_type: str
    call_put: Literal["Call", "Put"] | None = None
    call_put_currency: str | None = None
    direction: Literal["Buy", "Sell"] | None = None
    exercise_type: Literal["European", "American"] | None = None
    underlying_ticker: str | None = None
    strike: float | None = None
    notional: float | None = None
    notional_currency: str | None = None
    expiry_date: date | None = None
    settlement_date: date | None = None
    settlement_type: Literal["Cash", "Physical"] | None = None
    settlement_currency: str | None = None

    def to_mars_params(self) -> list[MarsParam]:
        """Return a flat list of MARS param dicts for the ``structureRequest``."""
        params: list[MarsParam] = []

        if self.call_put:
            params.append(self._selection_param("CallPut", self.call_put))
        if self.call_put_currency:
            params.append(self._str_param("CallPutCurrency", self.call_put_currency))
        if self.direction:
            params.append(self._selection_param("Direction", self.direction))
        if self.exercise_type:
            params.append(self._selection_param("ExerciseType", self.exercise_type))
        if self.underlying_ticker:
            params.append(self._str_param("UnderlyingTicker", self.underlying_ticker))
        if self.strike is not None:
            params.append(self._double_param("Strike", self.strike))
        if self.notional is not None:
            params.append(self._double_param("Notional", self.notional))
        if self.notional_currency:
            params.append(self._str_param("NotionalCurrency", self.notional_currency))
        if self.expiry_date:
            params.append(self._date_param("ExpiryDate", self.expiry_date.strftime("%Y-%m-%d")))
        if self.settlement_date:
            settlement_str = self.settlement_date.strftime("%Y-%m-%d")
            params.append(self._date_param("SettlementDate", settlement_str))
        if self.settlement_type:
            params.append(self._selection_param("SettlementType", self.settlement_type))
        if self.settlement_currency:
            params.append(self._str_param("SettlementCurrency", self.settlement_currency))

        return params
