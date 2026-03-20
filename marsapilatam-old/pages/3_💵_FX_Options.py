from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
import streamlit as st

from instruments.fx_option import FxOption, param_builder
from services.security.security_service import SecurityService


@st.cache_data
def price_fx_option(
    _security_service: SecurityService,
    fx_option: FxOption,
    valuation_date: date,
    market_data_date: date,
    requested_field: List[str],
    save_deal: bool,
) -> Tuple[dict, str]:
    return_values = {}

    struc_body = {
        "sessionId": "",
        "tail": fx_option.deal_type,
        "dealStructureOverride": {
            "param": param_builder(fx_option),
        },
    }

    response_deal_structure = _security_service.structure(struc_body)
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

    deal_metrics = _security_service.price(price_body)
    if len(deal_metrics[0]) == 0:
        return (return_values, deal_metrics[1])
    else:
        return_values["Pricing results"] = deal_metrics[0]

    if save_deal:
        save_result = _security_service.save(response_deal_structure[0])
        if len(save_result[0]) == 0:
            return (return_values, save_result[1])
        else:
            return_values["Deal saved id"] = save_result[0]

    return return_values, ""


def main():
    st.set_page_config(page_title="# FX Options Pricing", page_icon="💱", layout="wide")

    st.markdown("# FX Options Pricing")
    st.write("""This demo shows how to use MARS API to create a FX Option calculator using Bloomberg OVML<GO> back-end.""")

    st.subheader("Leg1")
    valuation_date = st.date_input("Valuation", date.today()).strftime("%Y-%m-%d")
    market_data_date = st.date_input("Curve Date", date.today()).strftime("%Y-%m-%d")
    deal_type = st.text_input("Deal Type", "FX.VA")
    call_put = st.selectbox("Call/Put", ["Call", "Put"])
    call_put_currency = st.text_input("Deal Currency", "CLP")
    direction = st.selectbox("Direction", ["Buy", "Sell"])
    exercise_type = st.selectbox("Direction", ["European", "American"])
    underlying_ticker = st.text_input("Underlying ticket", "CLPUSD")
    strike = st.number_input("Strike", value=1000)
    notional = st.number_input("Notional", value=5_000_000)
    notional_currency = st.text_input("Notional Currency", "USD")
    expiry_date = st.date_input("Expiry Date", date.today() + timedelta(days=180)).strftime("%Y-%m-%d")
    settlement_date = st.date_input("Settlement Date", date.today() + timedelta(days=182)).strftime("%Y-%m-%d")
    settlement_type = st.selectbox("Settlement Type", ["Cash", "Phisical"])
    settlement_currency = st.text_input("Settlement Currency", "USD")
    save_deal = st.checkbox("Save Deal", True)

    fx_option = FxOption(
        deal_type,
        call_put,
        call_put_currency,
        direction,
        exercise_type,
        underlying_ticker,
        strike,
        notional,
        notional_currency,
        expiry_date,
        settlement_date,
        settlement_type,
        settlement_currency,
    )

    requested_field = ["Delta", "Gamma", "ImplVol", "MktPx", "MktVal", "Premium", "Rho", "Theta", "UndFwdPx", "Vanna", "Vega", "Volga"]

    security_service = SecurityService()

    result = price_fx_option(
        security_service,
        fx_option,
        valuation_date,
        market_data_date,
        requested_field,
        save_deal,
    )

    st.subheader("Pricing Results")
    df = pd.DataFrame(result[0]["Pricing results"])
    st.dataframe(df)


if __name__ == "__main__":
    main()
