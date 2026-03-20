from typing import Dict, Tuple

import pandas as pd

from bloomberg import pricing_result as mpr
from bloomberg.webapi import Client

from configs.configs import web_credentials


class SecurityService:
    def __init__(self):
        self.mars = Client(web_credentials)

    def structure(self, body: Dict) -> Tuple[str, str]:
        body["sessionId"] = self.mars.session_id()

        response = self.mars.send("POST", "/marswebapi/v1/deals/temporary", body)

        if "error" in response:
            return "", response["error_description"]

        return response["results"][0]["structureResponse"]["dealHandle"], ""

    def price(self, body: Dict) -> Tuple[pd.DataFrame, str]:
        body["securitiesPricingRequest"]["pricingParameter"]["dealSession"] = self.mars.session_id()

        response = self.mars.send("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        return pd.DataFrame(mpr.to_dict(pricingResponse=response)), ""

    def solver(
        self,
        body: Dict,
    ) -> Tuple[dict, str]:
        body["solveRequest"]["dealSession"] = self.mars.session_id()

        response = self.mars.send("POST", "/marswebapi/v1/securitiesPricing", body)

        if "error" in response:
            return {}, response["error_description"]

        return response["results"][0]["solveResponse"], ""

    def save(self, deal_handle: str) -> Tuple[str, str]:
        response = self.mars.send("PATCH", "/marswebapi/v1/deals/temporary/" + deal_handle, {})

        if "error" in response:
            return "", response["error_description"]

        return response["results"][0]["saveResponse"]["dealId"], ""

    def get_terms_and_conditions(self, body: Dict) -> Tuple[Dict, str]:
        body["sessionId"] = self.mars.session_id()

        response = self.mars.send("POST", "/marswebapi/v1/deals/temporary", body)

        if "error" in response:
            return {}, response["error_description"]

        return response["results"][0]["structureResponse"], ""

    def get_deal_schema(self, body: Dict) -> Tuple[pd.DataFrame, str]:
        response = self.mars.send("GET", "/marswebapi/v1/dealSchema", body)

        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        deal_schema = response["schemaResponse"]["dealStructure"]["param"]
        df = pd.DataFrame(deal_schema, columns=["name", "value", "description", "mode", "solvableTarget", "category"]).set_index("name")

        return df, ""

    def get_deal_type(self) -> Tuple[pd.DataFrame, str]:
        response = self.mars.send("GET", "/marswebapi/v1/dealType", {"voidName": ""})

        if "error" in response:
            return pd.DataFrame(), response["error_description"]

        deal_schema = response["getDealTypesResponse"]["dealType"]

        return pd.DataFrame(deal_schema), ""
