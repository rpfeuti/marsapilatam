from typing import Dict, List, Tuple

import pandas as pd

from bloomberg import pricing_result as mpr
from bloomberg.webapi import Client
from configs.configs import web_credentials


class RiskService:
    def __init__(self):
        self.mars = Client(web_credentials)

    def key_rate_risk(self, valuation_date: str, deal_handle: str, requested_field: List[str]) -> Tuple[Dict[str, float], str]:
        body = {
            "securitiesKrrRequest": {
                "pricingParameter": {"valuationDate": valuation_date, "requestedField": requested_field},
                "krrDefinition": {
                    "id": "7238983182415036420",  # tenor mode, two-sided, bump:10bp, tenors:1M,2M,3M,18M,1Y,2Y,3Y,4Y,5Y,10Y,15Y,20Y,30Y
                    "externalName": "",
                },
                "security": [
                    {
                        "identifier": {"dealHandle": deal_handle},
                    }
                ],
            }
        }

        response = self.mars.send("POST", "/marswebapi/v1/securitiesKrr", body)

        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        df = pd.json_normalize(data=mpr.get_security_results(pricingResponse=response), meta=["krrResult", ["krrRiskResults"]])

        df = df.explode("krrResult.krrRiskResults")

        df["krrResult.krrRiskResults"] = df.apply(
            lambda row: {
                "BloombergDealID": row["identifiers.bloombergDealId"],
                "krrs": row["krrResult.krrRiskResults"]["krrs"],
                "valuationCurrency": row["krrResult.krrRiskResults"]["valuationCurrency"],
                "underlyingIRCurrency": row["krrResult.krrRiskResults"]["valuationCurrency"],
            },
            axis=1,
        )

        df = pd.json_normalize(
            df["krrResult.krrRiskResults"], record_path=["krrs"], meta=["BloombergDealID", "valuationCurrency", "underlyingIRCurrency"]
        )

        return df, ""
