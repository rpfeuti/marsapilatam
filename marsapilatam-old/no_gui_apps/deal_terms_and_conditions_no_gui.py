from services.security.security_service import SecurityService


def main():
    try:
        security_service = SecurityService()

        deal_cusip = "SL5606GY"

        body = {
            "sessionId": "",
            "tail": deal_cusip,
        }

        response = security_service.get_terms_and_conditions(body)
        if len(response[0]) == 0:
            print("Error structuring the deal")
            print(response[0])
            print(response[1])
            return
        else:
            print(response[0])

        print("FINISHED")

    except Exception as err:
        print(err)


if __name__ == "__main__":
    main()
