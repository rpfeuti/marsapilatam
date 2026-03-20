web_credentials = {
    "client_id": "ba1375b41416b480202ab87dc40da028",
    "client_secret": "f0d59fe8cf8e155069a812c50357d3c4652bb0806ef30cabbf907f59ca055513",
    "uuid": 31117082,
    "host": "https://api.bloomberg.com",
}

blpapi_config = {
    "app_name": "RPFEUTI_MARSAPI_LATAM",
    "connection_type": "DAPI",
    "host": "localhost",
    "port": 8194,
}

blpapi_services = {
    "mars_service": "//blp/marsxsvc",
    "mars_upload_service": "//blp/marsupd",
    "reference_data_service": "//blp/refdata",
}

float_index = ["BZDIOVRA", "CLICP", "COOVIBR", "ESTRON", "MXIBTIIE", "SOFRRATE"]

bond_to_swpm_pay_frequency = {
    0: "At Maturity",
    1: "Annual",
    2: "SemiAnnual",
    3: "NOT SUPPORTED",
    4: "Quarterly",
    6: "NOT SUPPORTED",
    7: "NOT SUPPORTED",
    12: "Monthly",
    28: "28 Days",
    35: "NOT SUPPORTED",
    49: "NOT SUPPORTED",
    52: "Weekly",
    360: "Daily",
}

curve_size = 12000

curve_type = ["Raw Curve", "Zero Coupon", "Discount Factor"]

curve_api_fields = {
    "Raw Curve": ("maturityDate", "rate", "rawCurve", "parRate"),
    "Zero Coupon": ("date", "rate", "interpolatedCurve", "zeroRate"),
    "Discount Factor": ("date", "factor", "interpolatedCurve", "discountFactor"),
}

interpolation_method = {
    "Piecewise Linear (Simple)": "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    "Smooth Forward (Cont)": "INTERPOLATION_METHOD_SMOOTH_FWD",
    "Step Forward (Cont)": "INTERPOLATION_METHOD_STEP_FWD",
    "Piecewise Linear (Cont)": "INTERPOLATION_METHOD_LINEAR_CONT",
}

curve_side = ["Mid", "Bid", "Ask"]

interpolation_interval = ["Daily", "Weekly", "Monthly"]

csa_curves_ids = {
    "USD": "S400",
    "CAD": "S401",
    "CHF": "S418",
    "EUR": "S403",
    "GPB": "S405",
    "JPY": "S404",
    "SEK": "S417",
    "USD": "S400",
    "AED": "S436",
    "ARS": "S419",
    "AUD": "S406",
    "BGN": "S422",
    "BRL": "S442",
    "CLP": "S423",
    "CLF": "S440",
    "CNY": "S407",
    "CNH": "S432",
    "COP": "S438",
    "COU": "S441",
    "CZK": "S424",
    "DKK": "S408",
    "HKD": "S409",
    "HUF": "S410",
    "ILS": "S426",
    "INR": "S412",
    "ISK": "S411",
    "KRW": "S421",
    "MXN": "S428",
    "MYR": "S427",
    "NOK": "S413",
    "NZD": "S402",
    "PEN": "S439",
    "PHP": "S433",
    "PLN": "S414",
    "QAR": "S437",
    "RUB": "S415",
    "SAR": "S429",
    "SGD": "S416",
    "THB": "S431",
    "TRY": "S420",
    "TWD": "S434",
    "UYU": "S445",
    "UYI": "S446",
    "ZAR": "S430",
}
