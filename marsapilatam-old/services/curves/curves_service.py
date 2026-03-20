from datetime import date
from typing import List, Tuple

import pandas as pd

from bloomberg.webapi.mars_webapi import Client
from configs import configs
from configs.configs import web_credentials


class CurvesService:
    def __init__(self, market_date: date):
        web_credentials["market_date"] = market_date  # X-Market Platform market date
        self.mars = Client(web_credentials)

    def download_curve(
        self,
        curve_type: str,
        curve_id: str,
        curve_date: date,
        side: str,
        requested_dates: List[date],
        interpolation: str,
    ) -> Tuple[pd.DataFrame, str]:
        # check if curve is csa
        if curve_id.upper() in configs.csa_curves_ids.values():
            raise Exception("CSA Curves are available in MARS API, but not implemented in this demo")

        match curve_type:
            case "Raw Curve":
                partial_body = {
                    "rawCurve": {
                        "curveDate": curve_date,
                        "settleDate": curve_date,
                        "parRate": [],
                    }
                }

            case "Zero Coupon":
                partial_body = {
                    "interpolatedCurve": {
                        "zeroRate": [{"date": dt, "rate": 0} for dt in requested_dates],
                        "interpolationMethodOverride": interpolation,
                    }
                }

            case "Discount Factor":
                partial_body = {
                    "interpolatedCurve": {
                        "discountFactor": [{"date": dt, "factor": 0} for dt in requested_dates],
                        "interpolationMethodOverride": interpolation,
                        "discountToDateType": "CUSTOM_DATE",
                        "discountToDate": curve_date,
                    }
                }

            case _:
                raise Exception("Curve type don't exists")

        body = {
            "getDataRequest": {
                "sessionId": self.mars.xmarket_session_id(),
                "keyAndData": [
                    {
                        "key": {"rateCurveKey": {"curveId": curve_id}},
                        "data": {
                            "marketData": {
                                "side": side,
                                "data": {"rateCurve": partial_body},
                            }
                        },
                    }
                ],
            }
        }

        response = self.mars.send("POST", "/marswebapi/v1/dataDownload", body)
        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        # Invalid curve id error test
        if "error" in response["getDataResponse"]["keyAndData"][0]["data"]["marketData"]["data"]:
            error_msg = "ERRORS - POSSIBLY CURVE ID DOESN'T EXISTS"
            error_msg = error_msg & response["getDataResponse"]["keyAndData"][0]["data"]["marketData"]["data"]["error"]
            return pd.DataFrame(), error_msg

        api_curve_type: str = configs.curve_api_fields[curve_type][2]
        api_rate_type: str = configs.curve_api_fields[curve_type][3]

        result = response["getDataResponse"]["keyAndData"][0]["data"]["marketData"]["data"]["rateCurve"][api_curve_type]

        return pd.DataFrame(result[api_rate_type]), ""
