from datetime import date
from typing import Tuple

import pandas as pd

from services.portfolio.portfolio_service import PortfolioService

# make pandas show everything
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def create(portfolio_name: str) -> Tuple[str, str]:
    try:
        portfolio_service = PortfolioService()

        body = {
            "coreTerms": {"portfolioName": portfolio_name},
            "uploadSettings": {
                "isSwpmCdswPositionExpressedAsUnits": False,
                "isOvmlPositionExpressedAsNotional": False,
                "isMtgeExpressedAsCurrentFace": False,
                "isGovtCreditBondExpressedAsCurrentFace": False,
                "isUnitTradedBondExpressedAsNotional": False,
                "isCdxExpressedAsCurrentFace": False,
            },
        }

        response = portfolio_service.create(body)
        if response[0] == "":
            print("Error creating portfolio")
            print(response[0])
            print(response[1])
            return
        else:
            print(response[0])

        print("FINISHED")

    except Exception as err:
        print(err)


def price(portfolio_name: str, valuation_date: date):
    try:
        portfolio_currency = "USD"
        portfolio_name = "MARS_API"
        pre_selected_fields = [
            "AccruedInterest",
            "BenchmarkYield",
            "Convexity",
            "DV01",
            "G-Spread",
            "Gamma",
            "I-Spread",
            "MktFX",
            "MktPx",
            "MktVal",
            "MktValPortCcy",
            "ModifiedDuration",
            "Notional",
            "OAS",
            "Principal",
            "SpreadDuration",
            "Theta",
            "Vega",
            "YASConvexity",
            "YASDuration",
            "YASModifiedDuration",
            "YieldtoNextCall",
            "YTW",
        ]

        portfolio_service = PortfolioService()

        body = {
            "portfolioPricingRequest": {
                "pricingParameter": {
                    "valuationDate": valuation_date,
                    "dealSession": "",
                    "marketDataSession": "",
                    "requestedField": pre_selected_fields,
                    "portfolioCurrency": portfolio_currency,
                },
                "portfolioDescription": {"portfolioName": portfolio_name, "portfolioSource": "PORTFOLIO"},
            },
        }

        response = portfolio_service.price(body)
        if len(response[0]) == 0:
            print("Error getting deal schema")
            print(response[0])
            print(response[1])
            return
        else:
            print(response[0])

        print("FINISHED")

    except Exception as err:
        print(err)


def main():
    price("MARS_API", date(2023, 10, 10))


if __name__ == "__main__":
    main()
