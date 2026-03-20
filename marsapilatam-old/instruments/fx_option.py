from dataclasses import dataclass
from typing import List


@dataclass
class FxOption:
    deal_type: str
    call_put: str
    call_put_currency: str
    direction: str
    exercise_type: str
    underlying_ticker: str
    strike: float
    notional: float
    notional_currency: str
    expiry_date: str
    settlement_date: str
    settlement_type: str
    settlement_currency: str


def param_builder(fx_option: FxOption) -> List[any]:
    param = []
    if fx_option.call_put != "":
        param.append({"name": "CallPut", "value": {"selectionVal": {"value": fx_option.call_put}}})

    if fx_option.call_put_currency != "":
        param.append({"name": "CallPutCurrency", "value": {"stringVal": fx_option.call_put_currency}})

    if fx_option.direction != "":
        param.append({"name": "Direction", "value": {"selectionVal": {"value": fx_option.direction}}})

    if fx_option.exercise_type != "":
        param.append({"name": "ExerciseType", "value": {"selectionVal": {"value": fx_option.exercise_type}}})

    if fx_option.underlying_ticker != "":
        param.append({"name": "UnderlyingTicker", "value": {"stringVal": fx_option.underlying_ticker}})

    if fx_option.strike != "":
        param.append({"name": "Strike", "value": {"doubleVal": fx_option.strike}})

    if fx_option.notional != "":
        param.append({"name": "Notional", "value": {"doubleVal": fx_option.notional}})

    if fx_option.notional_currency != "":
        param.append({"name": "NotionalCurrency", "value": {"stringVal": fx_option.notional_currency}})

    if fx_option.expiry_date != "":
        param.append({"name": "ExpiryDate", "value": {"dateVal": fx_option.expiry_date}})

    if fx_option.settlement_date != "":
        param.append({"name": "SettlementDate", "value": {"dateVal": fx_option.settlement_date}})

    if fx_option.settlement_type != "":
        param.append({"name": "SettlementType", "value": {"selectionVal": {"value": fx_option.settlement_type}}})

    if fx_option.settlement_currency != "":
        param.append({"name": "SettlementCurrency", "value": {"stringVal": fx_option.settlement_currency}})

    return param
