from typing import Tuple

import numpy as np
import pandas as pd
import streamlit as st

from services.security.security_service import SecurityService


@st.cache_data
def get_terms_conditions(_security_service: SecurityService, deal_cusip: str) -> Tuple[dict, str]:
    return_values = {}

    body = {
        "sessionId": "",
        "tail": deal_cusip,
    }

    response = _security_service.get_terms_and_conditions(body)
    if len(response[0]) == 0:
        return return_values, response[1]
    else:
        return response[0], ""


@st.cache_data
def get_deal_schema(_security_service: SecurityService, deal_type: str) -> Tuple[dict, str]:
    return_values = {}

    body = {
        "tail": deal_type,
    }

    response = _security_service.get_deal_schema(body)
    if len(response[0]) == 0:
        return return_values, response[1]
    else:
        return response[0], ""


@st.cache_data
def get_deal_type(_security_service: SecurityService) -> Tuple[dict, str]:
    return_values = {}

    response = _security_service.get_deal_type()
    if len(response[0]) == 0:
        return return_values, response[1]
    else:
        return response[0], ""


def main():
    st.set_page_config(page_title="Deal information", page_icon="📃", layout="wide")

    # make pandas show everything
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    security_service = SecurityService()

    tab1, tab2, tab3 = st.tabs(["Deal Types", "Deal Schema", "Terms and conditions"])

    with tab1:
        tab1.subheader("Deal types available in the API")
        st.write("""This demo shows how which deals type are available in MARS API """)
        results = get_deal_type(security_service)
        st.dataframe(results[0])

    with tab2:
        tab2.subheader("Deal schema retrieving Demo")
        st.write("""This demo shows the schema of a specific deal type """)
        deal_cusip = st.text_input("Deal Type", "IR.FXFL")
        results = get_deal_schema(security_service, deal_cusip)
        st.dataframe(results[0])

    with tab3:
        tab3.subheader("Deal terms and conditions retrieving Demo")
        tab3.write(
            """This demo shows how MARS API can be used to retrieve
                the terms and conditions of a deal booked on Bloomberg's eco-system """
        )
        deal_cusip = st.text_input("Deal Cusip", "SL5606GY")
        results = get_terms_conditions(security_service, deal_cusip)
        st.json(results[0])


if __name__ == "__main__":
    main()
