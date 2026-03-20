########################################################################################################
# Copyright 2023 Bloomberg Finance L.P.

# Sample code provided by Bloomberg is made available for illustration purposes only. Sample code
# is modifiable by individual users and is not reviewed for reliability, accuracy and
# is not supported as part of any Bloomberg service. Users are solely responsible for the selection
# of and use or intended use of the sample code, its applicability, accuracy and adequacy,
# and the resultant output thereof. Sample code is proprietary and confidential to Bloomberg
# and neither the recipient nor any of its representatives may distribute, publish or display such code
# to any other party, other than information disclosed to its employees on a need-to-know basis
# in connection with the purpose for which such code was provided.
# Sample code provided by Bloomberg is provided without any representations or warranties and subject
# to modification by Bloomberg in its sole discretion.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL BLOOMBERG BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
########################################################################################################

import json
import time
from datetime import date, datetime

import requests

from . import bbg_jwt


class Client:
    """
    A sample code that implements concepts required to interact with MARSAPI
    """

    def __init__(
        self,
        config,
    ) -> None:
        if not "client_id" in config or not "client_secret" in config or not "uuid" in config:
            example_config = {
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                "uuid": 123456,
                "host": "https://api.bloomberg.com",
                "market_date": "2023-01-28",
            }
            raise Exception(f"A valid config should look like this: {json.dumps(example_config, indent=4)}")
        if not "host" in config:
            config["host"] = "https://api.bloomberg.com"  # Default to PROD

        if "market_date" in config:
            self.__xmarket_market_date = config["market_date"]
        else:
            self.__xmarket_market_date = None

        self.__config = config
        self.__xmarket_session_id = None
        self.__session_id = None
        self.__market_data_session = None

        self.__jwt_factory = bbg_jwt.JwtFactory(
            self.__config["host"],
            self.__config["client_id"],
            self.__config["client_secret"],
        )

        self.__is_my_ip_whitelisted()

        if self.__xmarket_market_date != None:
            self.__xmarket_session_id = self.__start_data_session()

    def __del__(self):
        """
        destructor will close
        """
        if self.__market_data_session:
            self.send(
                method="DELETE",
                end_point="/marswebapi/v1/sessions/" + self.__market_data_session,
            )
        if self.__session_id:
            self.send(
                method="DELETE",
                end_point="/marswebapi/v1/sessions/" + self.__session_id,
            )

    def __repr__(self):
        def _default(obj):
            if isinstance(obj, (datetime, date)):
                return obj.strftime("%Y-%m-%d-%H:%M")
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        des = f"WebAPI Config: {json.dumps(self.__config, indent=4, default=_default)}\n"
        if self.__session_id:
            des += f"Session ID: {self.__session_id}\n"
        if self.__xmarket_market_date:
            des += f"XMarket Market Date: {self.__xmarket_market_date}\n"
        if self.__xmarket_session_id:
            des += f"XMarket Session ID: {self.__xmarket_session_id}\n"
        if self.__market_data_session:
            des += f"Market Data Session: {self.__market_data_session}\n"
        return des

    def __str__(self):
        return self.__repr__()

    def send_async(self, method, end_point, body=None):
        url = self.__config["host"] + end_point
        try:
            jwt = self.__jwt_factory.generate(method=method, path=end_point, kvp={"uuid": self.__config["uuid"]})
        except:
            raise Exception(f"Something is not right with your credentials {self.__config}")
        headers = {"jwt": jwt}

        data = {}
        if body != None:
            headers = {"Content-Type": "application/json", "jwt": jwt}

            def _default(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.strftime("%Y-%m-%d-%H:%M")
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            data = json.dumps(body, default=_default)

        if method == "GET":
            return requests.get(
                url=url,
                data=data,
                headers=headers,
            ).json()
        if method == "POST":
            return requests.post(
                url=url,
                data=data,
                headers=headers,
            ).json()
        if method == "PATCH":
            return requests.patch(
                url=url,
                data=data,
                headers=headers,
            ).json()
        if method == "PUT":
            return requests.put(
                url=url,
                data=data,
                headers=headers,
            ).json()
        if method == "DELETE":
            return requests.delete(
                url=url,
                data=data,
                headers=headers,
            ).json()
        raise Exception(f"Not supported HTTP method: {method}")

    def send(self, method, end_point, body=None, results_end_point=None):
        response = self.send_async(method, end_point, body)

        if results_end_point == None:
            if end_point == "/marswebapi/v1/deals":
                results_end_point = "/marswebapi/v1/results/Upload"
            elif (
                end_point == "/marswebapi/v1/securitiesPricing"
                or end_point == "/marswebapi/v1/portfolioPricing"
                or end_point == "/marswebapi/v1/securitiesKrr"
            ):
                results_end_point = "/marswebapi/v1/results/Pricing"
            else:
                results_end_point = end_point

        return self.response_polling(response, results_end_point)

    def response_polling(self, response, results_end_point, sleep_time=10):
        result_retrieval_id = None
        while True:
            if "results" in response and "resultNotReadyResponse" in response["results"][0]:
                result_retrieval_id = response["results"][0]["resultNotReadyResponse"]["resultRetrievalId"]
            elif "resultNotReadyResponse" in response:
                result_retrieval_id = response["resultNotReadyResponse"]["resultRetrievalId"]
            elif (
                "results" in response
                and "uploadResponse" in response["results"][0]
                and response["results"][0]["uploadResponse"].get("error", {}).get("errorCode") == 0
                and result_retrieval_id == None
                and "assetClassesResponse" not in response["results"][0]["uploadResponse"]
            ):
                result_retrieval_id = response["results"][0]["uploadResponse"]["status"]["key_vals"][0]["value"]["str_value"]
            elif (
                "uploadResponse" in response
                and response["uploadResponse"].get("error", {}).get("errorCode") == 104  # The request is still in progress
            ):
                pass
            else:
                break
            time.sleep(sleep_time)
            response = self.send_async(
                method="GET",
                end_point=results_end_point + "/" + result_retrieval_id,
            )
        if isinstance(response, dict):
            response["requestId"] = result_retrieval_id
        return response

    def session_id(self):
        """
        Get the deal session ID.

        Returns:
            str: Deal session ID.
        """
        if self.__session_id == None:
            self.__session_id = self.__start_session()
        return self.__session_id

    def xmarket_session_id(self):
        """
        Get the XMarket session ID.

        Returns:
            str: XMarket session ID.
        """
        return self.__xmarket_session_id

    def market_data_session(self):
        """
        Get the market data session ID.

        Returns:
            str: Market data session ID.
        """
        if self.__market_data_session == None:
            self.__market_data_session = self.__start_market_data_session()
        return self.__market_data_session

    def __start_session(self):
        """
        Start a deal session.

        Returns:
            str: Deal session ID.
        """
        response = self.send(
            method="POST",
            end_point="/marswebapi/v1/sessions",
            body={"startSession": {}},
        )
        return response["startSession"]["sessionId"]

    def __start_data_session(self):
        """
        Start a XMKT session.

        Returns:
            str: XMKT session ID.
        """
        response = self.send(
            method="POST",
            end_point="/marswebapi/v1/dataSessions",
            body={"startSessionRequest": {"marketDate": self.__xmarket_market_date}},
        )
        return response["startSessionResponse"]["sessionId"]

    def __start_market_data_session(self):
        """
        Start a market data session.

        Returns:
            str: Market data session ID.
        """
        response = self.send(
            method="POST",
            end_point="/marswebapi/v1/sessions",
            body={"startMarketDataSession": {}}
            if self.__xmarket_session_id == None
            else {"startMarketDataSession": {"marketId": self.__xmarket_session_id}},
        )
        return response["startMarketDataSessionResponse"]["marketDataSession"]

    def __is_my_ip_whitelisted(self):
        """
        Check if the IP is whitelisted.

        Raises:
            Exception: If the IP is not whitelisted.
        """
        response = self.send(
            method="GET",
            end_point="/marswebapi/v1/scenarios/12345",
        )
        if "errors" in response and "detail" in response["errors"][0]:
            raise Exception(response["errors"][0]["detail"])
