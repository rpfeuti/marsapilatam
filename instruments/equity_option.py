"""
Equity option instrument model for the Bloomberg MARS API.

Backed by the ``EQ.VA`` deal type.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from instruments.base import MarsInstrument, MarsParam


class EquityOption(MarsInstrument):
    """
    Equity vanilla option for the Bloomberg MARS API.

    Example::

        opt = EquityOption(
            deal_type="EQ.VA",
            call_put="Call",
            direction="Buy",
            exercise_type="European",
            underlying_ticker="AAPL US",
            strike=180.0,
            notional=1_000_000.0,
            expiry_date=date(2024, 12, 20),
            settlement_date=date(2024, 12, 23),
        )
    """

    deal_type: str
    call_put: Literal["Call", "Put"] | None = None
    direction: Literal["Buy", "Sell"] | None = None
    exercise_type: Literal["European", "American"] | None = None
    underlying_ticker: str | None = None
    strike: float | None = None
    notional: float | None = None
    expiry_date: date | None = None
    settlement_date: date | None = None

    def to_mars_params(self) -> list[MarsParam]:
        """Return a flat list of MARS param dicts for the ``structureRequest``."""
        params: list[MarsParam] = []

        if self.call_put:
            params.append(self._selection_param("CallPut", self.call_put))
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
        if self.expiry_date:
            params.append(self._date_param("ExpiryDate", self.expiry_date.strftime("%Y-%m-%d")))
        if self.settlement_date:
            settlement_str = self.settlement_date.strftime("%Y-%m-%d")
            params.append(self._date_param("SettlementDate", settlement_str))

        return params
