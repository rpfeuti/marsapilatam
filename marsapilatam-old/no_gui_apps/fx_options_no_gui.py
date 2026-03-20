from datetime import date

import pandas as pd

from instruments.fx_option import FxOption, param_builder
from services.security.security_service import SecurityService

# make pandas show everything
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def main():
    try:
        security_service = SecurityService()

        valuation_date = date(2023, 8, 31)
        curve_date = date(2023, 8, 31)

        valuation_date = date(2023, 8, 31)
        deal_type = "FX.VA"
        call_put = "Call"
        call_put_currency = "EUR"
        direction = "Buy"
        exercise_type = "European"
        underlying_ticker = "EURUSD"
        strike = 1.2
        notional = 1_000_000
        notional_currency = "USD"
        expiry_date = date(2028, 8, 31)
        settlement_date = date(2028, 8, 31)
        settlement_type = "Cash"
        settlement_currency = "USD"
        save_deal = True

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

        body = {
            "sessionId": "",
            "tail": fx_option.deal_type,
            "dealStructureOverride": {
                "param": param_builder(fx_option),
            },
        }

        response = security_service.structure(body)
        if len(response[0]) == 0:
            print("Error structuring the deal")
            print(response[0])
            print(response[1])
            return
        else:
            print("Deal handler: " + str(response[0]))

        price_body = {
            "securitiesPricingRequest": {
                "pricingParameter": {
                    "valuationDate": valuation_date,
                    "marketDataDate": curve_date,
                    "dealSession": "",
                    "requestedField": requested_field,
                    "useBbgRecommendedSettings": True,
                },
                "security": [{"identifier": {"dealHandle": response[0]}, "position": 1}],
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

        if save_deal:
            save_result = security_service.save(response[0])
            if len(save_result[0]) == 0:
                print("Error saving the deal")
                print(str(save_result[1]))
            else:
                print("Deal saved deal id: " + str(save_result[0]))

        print("FINISHED")

    except Exception as err:
        print(err)


if __name__ == "__main__":
    main()
