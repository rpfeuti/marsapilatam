from datetime import date

import pandas as pd

from services.security.security_service import SecurityService

# make pandas show everything
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def main():
    try:
        security_service = SecurityService()

        valuation_date = date(2023, 8, 31)
        curve_date = date(2023, 8, 31)

        securities = [
            {
                "identifier": {"CUSIP": "037833BX7"},
                "position": 100,
                "marketPrice": 99.268,
            },
            {"identifier": {"bloombergDealId": "AAPL US Equity"}, "position": 100},
            {
                "identifier": {"ISIN": "US91282CGM73"},
                "position": 100,
                "marketPrice": 99.16,
            },
        ]

        requested_field = [
            "AccruedInterest",
            "BenchmarkYield",
            "DV01",
            "G-Spread",
            "Gamma",
            "MktFX",
            "MktPx",
            "MktVal",
            "MktValPortCcy",
            "ModifiedDuration",
            "Notional",
            "Principal",
            "Theta",
            "Vega",
            "YASConvexity",
            "YASDuration",
            "YTM",
            "YTW",
        ]

        price_body = {
            "securitiesPricingRequest": {
                "pricingParameter": {
                    "valuationDate": valuation_date,
                    "marketDataDate": curve_date,
                    "requestedField": requested_field,
                    "useBbgRecommendedSettings": True,
                },
                "security": securities,
            }
        }

        deal_metrics = security_service.price(price_body)
        if len(deal_metrics[0]) == 0:
            print("Error pricing the deal")
            print(str(deal_metrics[1]))
            return
        else:
            print("")
            print("DEAL METRICS")
            print(deal_metrics[0])

        print("FINISHED")

    except Exception as err:
        print(err)


if __name__ == "__main__":
    main()
