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
### Parse pricing response


def get_security_results(pricingResponse, errors="raise"):
    security_results = []
    for result in pricingResponse["results"]:
        if "pricingResultResponse" in result:
            if "errorMessage" in result and errors == "raise":
                raise Exception(
                    "Pricing failed with error {}".format(result["errorMessage"])
                )
            elif "errorMessage" in result and errors == "ignore":
                continue
            else:
                security_results += result["pricingResultResponse"]["securityResult"]
    return security_results


def to_dict(pricingResponse, errors="raise") -> dict:
    """
    transform pricingResultResponse to dict(dict())
    """
    return _parse_pricing_result_reponse(get_security_results(pricingResponse, errors))


def _parse_pricing_result_reponse(security_results) -> dict:

    results = []
    for security in security_results:
        result_dict = dict()
        if "errorMessage" in security:
            result_dict["errorMessage"] = security["errorMessage"]
        if "pricingResult" in security: 
            result_dict = _parse_pricing_result(security["pricingResult"], result_dict)
        if "BloombergDealID" not in result_dict:
            if "bloombergDealId" in security["identifiers"]:
                result_dict["BloombergDealID"] = security["identifiers"][
                    "bloombergDealId"
                ]
            if "bloombergUniqueId" in security["identifiers"]:
                result_dict["BloombergDealID"] = security["identifiers"][
                    "bloombergUniqueId"
                ]
        # if 'leg' in security:
        #    for leg in security['leg']:
        #        self._parse_pricing_result_web(leg)
        if "portfolioSourceDetails" in security:
            result_dict["Portfolio"] = (
                security["portfolioSourceDetails"]["portfolioSource"]
                + ":"
                + security["portfolioSourceDetails"]["portfolioName"]
            )
        if "cashflowResult" in security:
            cashflow_result_dict = _parse_cashflow_result(security["cashflowResult"])
            result_dict["cashflow"] = cashflow_result_dict
        if "scenarioResult" in security:
            scenario_result_dict = _parse_scenario_result(security["scenarioResult"])
            result_dict["scenario"] = scenario_result_dict
        results.append(result_dict)

    return results


def _parse_pricing_result(params, result_dict: dict) -> dict:

    for param in params:
        result_dict[param["name"]] = _get_param_value_as_string(param)
    return result_dict


def _parse_cashflow_result(params) -> dict:

    cfs = []
    for cashflowResult in params:

        # resetRate = cashflowResult['resetRate']
        # resetDate = cashflowResult['resetDate']

        cfs.append(
            dict(
                {
                    "paymentType": str(cashflowResult["paymentType"]),
                    "paymentDate": cashflowResult["paymentDate"],
                    "currency": cashflowResult["currency"],
                    "amount": cashflowResult["amount"],
                }
            )
        )
    return cfs


def _parse_scenario_result(params) -> dict:

    scenarios = []
    for scenarioResult in params:
        result_dict = dict()
        scenario_id = scenarioResult["scenario"]["scenarioId"]
        if "errorMessage" in scenarioResult:
            result_dict["errorMessage"] = scenarioResult["errorMessage"]
        if "pricingResult" in scenarioResult:
            result_dict = _parse_pricing_result(
                scenarioResult["pricingResult"], result_dict
            )
        scenarios.append(dict({scenario_id: result_dict}))
    return scenarios


def _get_param_value_as_string(param) -> str:
    """
    private method used to parse responses from MARS API
    """
    if "doubleVal" in param["value"]:
        return str(param["value"]["doubleVal"])
    elif "stringVal" in param["value"]:
        return str(param["value"]["stringVal"])
    elif "dateVal" in param["value"]:
        return str(param["value"]["dateVal"])
    elif "selectionVal" in param["value"]:
        return str(param["value"]["selectionVal"]["value"])
    elif "intVal" in param["value"]:
        return str(param["value"]["intVal"])
    return ""
