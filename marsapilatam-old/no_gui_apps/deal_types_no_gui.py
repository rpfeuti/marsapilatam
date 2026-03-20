import pandas as pd

from services.security.security_service import SecurityService

# make pandas show everything
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def main():
    try:
        security_service = SecurityService()
        response = security_service.get_deal_type()
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


if __name__ == "__main__":
    main()
