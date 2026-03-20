import asyncio
import json
from datetime import date, datetime, timedelta

import aiohttp
import pandas as pd

from bloomberg.webapi import bbg_jwt
from configs.configs import web_credentials
from instruments.swap import Swap, param_builder


async def swap_structure(session: aiohttp.ClientSession, mars_session_id: str, tenor, effective_date):
    swap = Swap(
        deal_type="IR.OIS",
        effective_date=effective_date,
        maturity_date=effective_date + timedelta(days=30 * tenor),
        csa_collateral_currency="N/A",
        leg1_direction="Pay",
        leg1_notional=100,
        leg1_currency="COP",
        leg1_pay_frequency="Monthly",
        leg1_day_count="ACT/360",
        leg2_notional=100,
        leg2_currency="COP",
        leg2_pay_frequency="Monthly",
        leg2_day_count="ACT/360",
    )

    body = json.dumps(
        {
            "sessionId": mars_session_id,
            "tail": swap.deal_type,
            "dealStructureOverride": {
                "param": param_builder(swap)[0],
                "leg": [
                    {"param": param_builder(swap)[1]},
                    {"param": param_builder(swap)[2]},
                ],
            },
        }
    )

    end_point = "/marswebapi/v1/deals/temporary"

    jwt = jwt_factory.generate(method="POST", path=end_point, kvp={"uuid": web_credentials["uuid"]})

    headers = {"Content-Type": "application/json", "jwt": jwt}

    async with session.post(web_credentials["host"] + end_point, headers=headers, data=body) as resp:
        response = await resp.json()
        return response["results"][0]["structureResponse"]["dealHandle"]


async def swap_solve(session: aiohttp.ClientSession, mars_session_id: str, deal_handle: str, market_data_date: date, valuation_date: date):
    body = json.dumps(
        {
            "solveRequest": {
                "identifier": {"dealHandle": deal_handle},
                "input": {
                    "name": "Premium",
                    "value": {"doubleVal": 0},
                },
                "solveFor": "Coupon",
                "solveForLeg": 1,
                "valuationDate": valuation_date.strftime("%Y-%m-%d"),
                "dealSession": mars_session_id,
                "marketDataDate": market_data_date.strftime("%Y-%m-%d"),
            }
        }
    )

    end_point = "/marswebapi/v1/securitiesPricing"
    jwt = jwt_factory.generate(method="POST", path=end_point, kvp={"uuid": web_credentials["uuid"]})
    headers = {"Content-Type": "application/json", "jwt": jwt}

    async with session.post(web_credentials["host"] + end_point, data=body, headers=headers) as resp:
        response = await resp.json()
        return response["results"][0]["solveResponse"]


async def main():
    async with aiohttp.ClientSession() as aiohttp_session:
        # get session id
        end_point = "/marswebapi/v1/sessions"
        jwt = jwt_factory.generate(method="POST", path=end_point, kvp={"uuid": web_credentials["uuid"]})
        header = {"Content-Type": "application/json", "jwt": jwt}
        body = json.dumps({"startSession": {}})

        async with aiohttp_session.post(web_credentials["host"] + end_point, headers=header, data=body) as resp:
            response = await resp.json()
            mars_session_id = response["startSession"]["sessionId"]

        # strucuture deals
        struct_tasks = []
        effective_date = date(2023, 12, 1)

        for tenor in range(1, 37):
            struct_tasks.append(asyncio.ensure_future(swap_structure(aiohttp_session, mars_session_id, tenor, effective_date)))

        deal_handlers = await asyncio.gather(*struct_tasks)

        # solve deals
        market_data_date = date(2023, 10, 30)
        valuation_date = date(2023, 10, 31)

        solve_tasks = []
        for deal_handler in deal_handlers:
            solve_tasks.append(
                asyncio.ensure_future(swap_solve(aiohttp_session, mars_session_id, deal_handler, market_data_date, valuation_date))
            )

        solve_requests = await asyncio.gather(*solve_tasks)

        coupons = []
        for request in solve_requests:
            coupons.append(request["solveResult"]["value"]["doubleVal"])

        final_results = {}
        final_results["tenors"] = range(1, 37)
        final_results["coupons"] = coupons

        df = pd.DataFrame(final_results)
        print(df)


if __name__ == "__main__":
    jwt_factory = bbg_jwt.JwtFactory(
        web_credentials["host"],
        web_credentials["client_id"],
        web_credentials["client_secret"],
    )

    start_time = datetime.now()
    asyncio.run(main())
    end_time = datetime.now()
    print("Duration: {}".format(end_time - start_time))
