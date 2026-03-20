from dataclasses import dataclass
from datetime import date
from typing import List, Tuple


@dataclass
class Swap:
    deal_type: str = ""
    effective_date: date = ""
    maturity_date: date = ""
    csa_collateral_currency: str = ""
    settlement_currency: str = ""

    leg1_direction: str = ""
    leg1_notional: float = ""
    leg1_currency: str = ""
    leg1_spread: float = ""
    leg1_fixed_rate: float = ""
    leg1_floating_index: str = ""
    leg1_pay_frequency: str = ""
    leg1_day_count: str = ""

    leg2_direction: str = ""
    leg2_notional: float = ""
    leg2_currency: str = ""
    leg2_spread: float = ""
    leg2_fixed_rate: float = ""
    leg2_floating_index: str = ""
    leg2_pay_frequency: str = ""
    leg2_day_count: str = ""

    leg1_forward_curve: str = ""
    leg1_discount_curve: str = ""
    leg2_forward_curve: str = ""
    leg2_discount_curve: str = ""


def param_builder(swap: Swap) -> Tuple[List[any], List[any], List[any]]:
    param = []
    if swap.settlement_currency != "":
        param.append({"name": "SettlementCurrency", "value": {"stringVal": swap.settlement_currency}})

    if swap.csa_collateral_currency != "":
        param.append({"name": "CSACollateralCurrency", "value": {"stringVal": swap.csa_collateral_currency}})

    param_leg1 = []
    if swap.leg1_direction != "":
        param_leg1.append({"name": "Direction", "value": {"selectionVal": {"value": swap.leg1_direction}}})

    if swap.leg1_notional != "":
        param_leg1.append({"name": "Notional", "value": {"doubleVal": float(swap.leg1_notional)}})

    if swap.leg1_currency != "":
        param_leg1.append({"name": "Currency", "value": {"stringVal": swap.leg1_currency}})

    if swap.effective_date != "":
        param_leg1.append({"name": "EffectiveDate", "value": {"dateVal": swap.effective_date.strftime("%Y-%m-%d")}})

    if swap.maturity_date != "":
        param_leg1.append({"name": "MaturityDate", "value": {"dateVal": swap.maturity_date.strftime("%Y-%m-%d")}})

    if swap.leg1_fixed_rate != "":
        param_leg1.append({"name": "FixedRate", "value": {"doubleVal": float(swap.leg1_fixed_rate)}})

    if swap.leg1_spread != "":
        param_leg1.append({"name": "Spread", "value": {"doubleVal": float(swap.leg1_spread)}})

    if swap.leg1_floating_index != "":
        param_leg1.append({"name": "FloatingIndex", "value": {"stringVal": swap.leg1_floating_index}})

    if swap.leg1_pay_frequency != "":
        param_leg1.append({"name": "PayFrequency", "value": {"selectionVal": {"value": swap.leg1_pay_frequency}}})

    if swap.leg1_day_count != "":
        param_leg1.append({"name": "DayCount", "value": {"selectionVal": {"value": swap.leg1_day_count}}})

    param_leg2 = []
    if swap.leg2_direction != "":
        param_leg2.append({"name": "Direction", "value": {"selectionVal": {"value": swap.leg2_direction}}})

    if swap.leg2_notional != "":
        param_leg2.append({"name": "Notional", "value": {"doubleVal": float(swap.leg2_notional)}})

    if swap.leg2_currency != "":
        param_leg2.append({"name": "Currency", "value": {"stringVal": swap.leg2_currency}})

    if swap.effective_date != "":
        param_leg2.append({"name": "EffectiveDate", "value": {"dateVal": swap.effective_date.strftime("%Y-%m-%d")}})

    if swap.maturity_date != "":
        param_leg2.append({"name": "MaturityDate", "value": {"dateVal": swap.maturity_date.strftime("%Y-%m-%d")}})

    if swap.leg2_fixed_rate != "":
        param_leg2.append({"name": "FixedRate", "value": {"doubleVal": float(swap.leg2_fixed_rate)}})

    if swap.leg2_spread != "":
        param_leg2.append({"name": "Spread", "value": {"doubleVal": float(swap.leg2_spread)}})

    if swap.leg2_floating_index != "":
        param_leg2.append({"name": "FloatingIndex", "value": {"stringVal": swap.leg2_floating_index}})

    if swap.leg2_pay_frequency != "":
        param_leg2.append({"name": "PayFrequency", "value": {"selectionVal": {"value": swap.leg2_pay_frequency}}})

    if swap.leg2_day_count != "":
        param_leg2.append({"name": "DayCount", "value": {"selectionVal": {"value": swap.leg2_day_count}}})

    return param, param_leg1, param_leg2
