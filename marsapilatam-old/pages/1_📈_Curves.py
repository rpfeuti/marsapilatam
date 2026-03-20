from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from configs import configs
from services.curves.curves_service import CurvesService


@st.cache_data
def get_curve(
    _curves_ws: CurvesService,
    curve_id: str,
    curve_date: date,
    curve_type: str,
    interval: str,
    side: str,
    interpolation: str,
):
    requested_dates = []
    if curve_type != "Raw Curve":
        # date list generator, must start always on T+1 of the curve date, otherwise API return error
        curve_date_gen = curve_date + timedelta(days=1)
        while curve_date_gen < curve_date + timedelta(configs.curve_size):
            requested_dates.append(curve_date_gen)
            if interval == "Daily":
                curve_date_gen = curve_date_gen + timedelta(1)
            if interval == "Weekly":
                curve_date_gen = curve_date_gen + timedelta(7)
            if interval == "Monthly":
                curve_date_gen = curve_date_gen + timedelta(30)

    return _curves_ws.download_curve(
        curve_type,
        curve_id,
        curve_date,
        side,
        requested_dates,
        interpolation,
    )


def main():
    # make pandas show everything
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    st.set_page_config(page_title="Curves Api Demo", page_icon="📈", layout="wide")
    st.markdown("# Curves Api Demo")
    st.write(
        """This demo shows how MARS API can be applied on a 
        web application to present curves data """
    )

    curve_id = st.text_input("Curve Id", "S490")

    curve_date = st.date_input("Curve date", date.today())

    curve_type = st.selectbox(
        "Curve Type",
        configs.curve_type,
    )

    interpolation_key = st.selectbox(
        "Interpolation Method",
        configs.interpolation_method.keys(),
    )

    interpolation: str = configs.interpolation_method[interpolation_key]

    interpolation_interval = st.selectbox("Interpolation interval", configs.interpolation_interval)

    side = st.selectbox("Side", configs.curve_side)

    curves_ws = CurvesService(date.today())

    response = get_curve(curves_ws, curve_id, curve_date, curve_type, interpolation_interval, side, interpolation)

    result = response[0]

    st.caption("CURVE")
    api_date_field: str = configs.curve_api_fields[curve_type][0]
    api_value_field: str = configs.curve_api_fields[curve_type][1]
    graph_dataset = result[[api_date_field, api_value_field]]
    fig = px.line(graph_dataset, x=api_date_field, y=api_value_field)
    st.plotly_chart(fig)

    st.caption("CURVE DATA")
    st.write(result)
    st.write("Finished with no error messages")


if __name__ == "__main__":
    main()
