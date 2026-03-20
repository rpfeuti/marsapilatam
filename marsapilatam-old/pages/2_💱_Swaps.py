from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
import streamlit as st

from instruments.swap import Swap, param_builder
from services.security.security_service import SecurityService


@st.cache_data
def price_swap(
    _struc_service: SecurityService,
    swap: Swap,
    valuation_date: date,
    market_data_date: date,
    requested_field: List[str],
    solver_on: bool,
    solve_for: str,
    solve_for_leg: float,
    solve_where: str,
    solve_where_value: float,
    calculate_krr: bool,
    save_deal: bool,
) -> Tuple[dict, str]:
    return_values = {}

    struc_body = {
        "sessionId": "",
        "tail": swap.deal_type,
        "dealStructureOverride": {
            "param": param_builder(swap)[0],
            "leg": [
                {"param": param_builder(swap)[1]},
                {"param": param_builder(swap)[2]},
            ],
        },
    }

    response_deal_structure = _struc_service.structure(struc_body)
    if len(response_deal_structure[0]) == 0:
        return (return_values, response_deal_structure[1])
    else:
        return_values["Deal handler"] = response_deal_structure[0]

    price_body = {
        "securitiesPricingRequest": {
            "pricingParameter": {
                "valuationDate": valuation_date,
                "marketDataDate": market_data_date,
                "dealSession": "",
                "requestedField": requested_field,
                "useBbgRecommendedSettings": True,
            },
            "security": [{"identifier": {"dealHandle": response_deal_structure[0]}, "position": 1}],
        }
    }

    deal_metrics = _struc_service.price(price_body)
    if len(deal_metrics[0]) == 0:
        return (return_values, deal_metrics[1])
    else:
        return_values["Pricing results"] = deal_metrics[0]

    if solver_on:
        solver_body = {
            "solveRequest": {
                "identifier": {"dealHandle": response_deal_structure[0]},
                "input": {
                    "name": solve_where,
                    "value": {"doubleVal": solve_where_value},
                },
                "solveFor": solve_for,
                "solveForLeg": solve_for_leg,
                "valuationDate": valuation_date,
                "dealSession": "",
                "marketDataDate": market_data_date,
            }
        }

        solve_result = _struc_service.solver(solver_body)
        if len(solve_result[0]) == 0:
            return (return_values, solve_result[1])
        else:
            return_values["Solver results"] = solve_result[0]

    if save_deal:
        save_result = _struc_service.save(response_deal_structure[0])
        if len(save_result[0]) == 0:
            return (return_values, save_result[1])
        else:
            return_values["Deal saved id"] = save_result[0]

    return return_values, ""


def main():
    st.set_page_config(page_title="Swaps Pricing", page_icon="💱", layout="wide")

    st.markdown("# Swaps Pricing")
    st.write("""This demo shows how to use MARS API to create a swap calculator using Bloomberg SWPM<GO> back-end.""")

    settlement_currency: str = ""
    leg1_forward_curve: str = ""
    leg1_discount_curve: str = ""
    leg2_forward_curve: str = ""
    leg2_discount_curve: str = ""
    leg2_fixed_rate: str = ""
    leg1_spread = ""
    leg1_floating_index = ""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.subheader("Common")
        valuation_date = st.date_input("Valuation", date.today(), key=10)
        market_data_date = st.date_input("Curve Date", date.today(), key=11)
        deal_type = st.text_input("Deal Type", "IR.OIS", key=20)
        effective_date = st.date_input("Effective", date.today(), key=30)
        maturity_date = st.date_input("Maturity", date.today() + timedelta(days=1800), key=40)
        csa_collateral_currency = st.text_input("CSA Col Ccy", "USD", key=50)

    with col2:
        st.subheader("Leg1")
        leg1_direction = st.text_input("Pay Receive", "Receive", key=60)
        leg1_notional = st.number_input("Notional", value=100_000_000, key=70)
        leg1_currency = st.text_input("Currency", "USD", key=80)
        # leg1_floating_index = st.selectbox(
        #     "Index",
        #     float_index,
        # )
        leg1_fixed_rate = st.text_input("Coupon", value=9, key=100)
        leg1_pay_frequency = st.text_input("Pay Freq", "Annual", key=110)
        leg1_day_count = st.text_input("Day Count", "ACT/360", key=120)

    with col3:
        st.subheader("Leg2")
        leg2_direction = st.text_input("Pay Receive", "Pay", key=130)
        leg2_notional = st.number_input("Notional", value=100_000_000, key=140)
        leg2_currency = st.text_input("Currency", "USD", key=150)
        leg2_spread = st.number_input("Spread", 0, key=160)
        leg2_floating_index = st.text_input("Index", "SOFRRATE", key=170)
        leg2_pay_frequency = st.text_input("Pay Freq", "Annual", key=180)
        leg2_day_count = st.text_input("Day Count", "ACT/360", key=190)

    with col4:
        solver_on = st.checkbox("Solver", False, key=200)
        solve_for = st.text_input("Find", "Coupon", key=210)
        solve_for_leg = st.number_input("Leg", value=1, key=220)
        solve_where = st.text_input("Where", "Premium", key=230)
        solve_where_value = st.number_input("Where value", 0, key=240)

        calculate_krr = st.checkbox("KRR", False, key=250)
        save_deal = st.checkbox("Save Deal", True, key=260)

    generic_swap = Swap(
        deal_type,
        effective_date,
        maturity_date,
        csa_collateral_currency,
        settlement_currency,
        leg1_direction,
        leg1_notional,
        leg1_currency,
        leg1_spread,
        leg1_fixed_rate,
        leg1_floating_index,
        leg1_pay_frequency,
        leg1_day_count,
        leg2_direction,
        leg2_notional,
        leg2_currency,
        leg2_spread,
        leg2_fixed_rate,
        leg2_floating_index,
        leg2_pay_frequency,
        leg2_day_count,
        leg1_forward_curve,
        leg1_discount_curve,
        leg2_forward_curve,
        leg2_discount_curve,
    )

    requested_field = [
        "AccruedInterest",
        "DV01",
        "MktFX",
        "MktPx",
        "MktVal",
        "MktValPortCcy",
        "ModifiedDuration",
        "MktPx",
        "YTM",
        "YTW",
        "YieldtoNextCall",
        "I-Spread",
        "G-Spread",
        "YASDuration",
        "YASConvexity",
        "YASModifiedDuration",
        "BenchmarkYield",
        "ModifiedDuration",
        "Convexity",
        "OAS",
        "Delta",
        "Gamma",
        "Vega",
        "Theta",
        "DV01",
        "Credit DV01",
        "SpreadDuration",
        "Notional",
        "Principal",
        "AccruedInterest",
        "MktVal",
    ]

    struc_service = SecurityService()
    result = price_swap(
        struc_service,
        generic_swap,
        valuation_date,
        market_data_date,
        requested_field,
        solver_on,
        solve_for,
        solve_for_leg,
        solve_where,
        solve_where_value,
        calculate_krr,
        save_deal,
    )

    st.subheader("Pricing Results")
    df = pd.DataFrame(result[0]["Pricing results"])
    st.dataframe(df)

    if solver_on:
        st.subheader("Solver Results")
        st.write(result[0]["Solver results"]["solveResult"])

    if save_deal:
        st.subheader("Saved deal id")
        st.write(result[0]["Deal saved id"])


if __name__ == "__main__":
    main()
