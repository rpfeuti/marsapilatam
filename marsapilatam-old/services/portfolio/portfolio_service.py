from datetime import date
from typing import Dict, Tuple

import pandas as pd

from bloomberg import pricing_result as mpr
from bloomberg.webapi import Client
from configs.configs import web_credentials


class PortfolioService:
    def __init__(self):
        self.mars = Client(web_credentials)

    def create(self, body: Dict) -> Tuple[str, str]:
        response = self.mars.send("POST", "/enterprise/common/portfolios", body)

        if "error" in response:
            return "", response["error_description"]

        portfolioId = response["createPortfolioResponse"]["portfolioId"]

        return portfolioId, ""

    def price(self, body) -> Tuple[pd.DataFrame, str]:
        response = self.mars.send("POST", "/marswebapi/v1/portfolioPricing", body)

        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        df = pd.DataFrame(mpr.to_dict(pricingResponse=response))

        return df, ""
