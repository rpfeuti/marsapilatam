from dataclasses import dataclass
from typing import List


@dataclass
class EquityOption:
    deal_type: str
    call_put: str
    direction: str
    exercise_type: str
    underlying_ticker: str
    strike: float
    notional: float
    expiry_date: str
    settlement_date: str


def param_builder(equity_option: EquityOption) -> List[any]:
    param = []
    if equity_option.direction != "":
        param.append({"name": "Direction", "value": {"selectionVal": {"value": equity_option.direction}}})

    if equity_option.exercise_type != "":
        param.append({"name": "ExerciseType", "value": {"selectionVal": {"value": equity_option.exercise_type}}})

    if equity_option.underlying_ticker != "":
        param.append({"name": "UnderlyingTicker", "value": {"stringVal": equity_option.underlying_ticker}})

    if equity_option.strike != "":
        param.append({"name": "Strike", "value": {"doubleVal": equity_option.strike}})

    if equity_option.notional != "":
        param.append({"name": "Notional", "value": {"doubleVal": equity_option.notional}})

    if equity_option.expiry_date != "":
        param.append({"name": "ExpiryDate", "value": {"dateVal": equity_option.expiry_date}})

    if equity_option.settlement_date != "":
        param.append({"name": "SettlementDate", "value": {"dateVal": equity_option.settlement_date}})

    return param
