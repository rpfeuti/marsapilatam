from datetime import date
from typing import List, Tuple

import pandas as pd
import streamlit as st

from services.portfolio.portfolio_service import PortfolioService


@st.cache_data
def get_portfolio_metrics(
    _portfolio_service: PortfolioService, valuation_date: str, portfolio_currency: str, portfolio_name: str, requested_fields: List[str]
) -> Tuple[dict, str]:
    return_values = {}

    body = {
        "portfolioPricingRequest": {
            "pricingParameter": {
                "valuationDate": valuation_date,
                "dealSession": "",
                "marketDataSession": "",
                "requestedField": requested_fields,
                "portfolioCurrency": portfolio_currency,
            },
            "portfolioDescription": {"portfolioName": portfolio_name, "portfolioSource": "PORTFOLIO"},
        },
    }

    response = _portfolio_service.price(body)
    if len(response[0]) == 0:
        return return_values, response[1]
    else:
        return_values["portfolio_metrics"] = response[0]
        return return_values, ""


@st.cache_data
def get_mars_api_fields():
    df = pd.read_csv("configs/mars_api_fields.csv")
    return df


def main():
    st.set_page_config(page_title="Portfolio Pricing", page_icon="🏦", layout="wide")
    st.markdown("# Portfolio")
    st.write("""This demo shows how to use MARS API to price an entire portfolio and get selected metrics.""")

    # make pandas show everything
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    portfolio_name = st.text_input("Portfolio Name", "MARS_API")
    valuation_date = st.date_input("Valuation Date", date.today())
    portfolio_currency = st.text_input("Portfolio Currency", "USD")

    pre_selected_fields = [
        "AccruedInterest",
        "MktFX",
        "Notional",
        "Principal",
        "MktPx",
        "MktVal",
        "MktValPortCcy",
        "MktPx",
        "YTM",
        "YTW",
        "YieldtoNextCall",
        "I-Spread",
        "G-Spread",
        "DV01",
        "YASDuration",
        "Convexity",
        "OAS",
        "Gamma",
        "Vega",
        "Theta",
    ]

    all_fields = list(get_mars_api_fields()["Input Fields"])
    requested_fields = st.multiselect("Which metrics do you want retrieve", all_fields, pre_selected_fields)

    portfolio_service = PortfolioService()
    results = get_portfolio_metrics(portfolio_service, valuation_date, portfolio_currency, portfolio_name, requested_fields)

    st.dataframe(results[0]["portfolio_metrics"], use_container_width=True, height=None)


if __name__ == "__main__":
    main()
