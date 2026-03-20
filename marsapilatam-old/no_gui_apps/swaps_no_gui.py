from datetime import date

from instruments.swap import Swap, param_builder
from services.security.security_service import SecurityService


def main():
    try:
        security_service = SecurityService("BLPAPI")

        valuation_date = date(2023, 8, 31)
        curve_date = date(2023, 8, 31)

        deal_type = "IR.NDSFX"
        effective_date = date(2023, 8, 31)
        maturity_date = date(2028, 8, 31)
        csa_collateral_currency = "USD"
        settlement_currency = "USD"

        leg1_direction = "Receive"
        leg1_notional = 100_000_000.0
        leg1_currency = "USD"
        leg1_spread = ""
        leg1_fixed_rate = 3.0
        leg1_floating_index = ""
        leg1_pay_frequency = "Monthly"
        leg1_day_count = "ACT/360"

        leg2_direction = "Pay"
        leg2_notional = ""
        leg2_currency = "USD"
        leg2_spread = ""
        leg2_fixed_rate = 0
        leg2_floating_index = ""
        leg2_pay_frequency = "Monthly"
        leg2_day_count = "ACT/360"

        leg1_forward_curve = ""
        leg1_discount_curve = ""
        leg2_forward_curve = ""
        leg2_discount_curve = ""

        solver_on = True
        solve_for = "Coupon"
        solve_for_leg = 2
        solve_where = "Premium"
        solve_where_value = 0

        save_deal = True

        swap = Swap(
            deal_type,
            effective_date,
            maturity_date,
            csa_collateral_currency,
            settlement_currency,
            leg1_direction,
            leg1_notional,
            leg1_currency,
            leg1_spread,
            leg1_fixed_rate,
            leg1_floating_index,
            leg1_pay_frequency,
            leg1_day_count,
            leg2_direction,
            leg2_notional,
            leg2_currency,
            leg2_spread,
            leg2_fixed_rate,
            leg2_floating_index,
            leg2_pay_frequency,
            leg2_day_count,
            leg1_forward_curve,
            leg1_discount_curve,
            leg2_forward_curve,
            leg2_discount_curve,
        )

        requested_field = [
            "AccruedInterest",
            "Convexity",
            "Duration",
            "DV01",
            "Gamma",
            "MktFX",
            "MktPx",
            "MktVal",
            "MktValPortCcy",
            "Notional",
            "Theta",
        ]

        struc_body = {
            "sessionId": "",
            "tail": swap.deal_type,
            "dealStructureOverride": {
                "param": param_builder(swap)[0],
                "leg": [
                    {"param": param_builder(swap)[1]},
                    {"param": param_builder(swap)[2]},
                ],
            },
        }

        response = security_service.structure(struc_body)
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

        if solver_on:
            print("")
            print("RUNNING SOLVER...")

            solver_body = {
                "solveRequest": {
                    "identifier": {"dealHandle": response[0]},
                    "input": {
                        "name": solve_where,
                        "value": {"doubleVal": solve_where_value},
                    },
                    "solveFor": solve_for,
                    "solveForLeg": solve_for_leg,
                    "valuationDate": valuation_date,
                    "dealSession": "",
                    "marketDataDate": curve_date,
                }
            }

            solve_result = security_service.solver(solver_body)

            if len(solve_result[0]) == 0:
                print("Error solving the deal")
                print(str(solve_result[1]))
                return
            else:
                print("For " + solve_where + " = " + str(solve_where_value))
                print(solve_result[0])

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
