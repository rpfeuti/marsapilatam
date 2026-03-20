from datetime import date, timedelta

import pandas as pd

from configs import configs
from services.curves.curves_service import CurvesService

# make pandas show everything
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def main():
    try:
        curve_date = date(2023, 12, 12)

        curves_ws = CurvesService(curve_date)
        curve_id: str = "I25"

        # curve_type_options = ["Raw Curve", "Zero Coupon", "Discount Factor"]
        curve_type = "Raw Curve"

        # curve_interval_options = ["Daily", "Weekly", "Monthly"]
        interval: str = "Monthly"

        # curve_side_options = ["Mid", "Bid", "Ask"]
        side: str = "Mid"

        # "Piecewise Linear (Simple)", "Smooth Forward (Cont)", "Step Forward (Cont)", "Piecewise Linear (Cont)"
        interpolation: str = configs.interpolation_method["Piecewise Linear (Simple)"]

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

        response = curves_ws.download_curve(
            curve_type,
            curve_id,
            curve_date,
            side,
            requested_dates,
            interpolation,
        )

        if response[1] == "":
            print(response[0])
            print("Finished with no error messages")
            return
        else:
            print(response[1])

    except Exception as err:
        print(err)


if __name__ == "__main__":
    main()
