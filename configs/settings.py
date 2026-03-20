from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Bloomberg MARS API credentials and runtime constants.
    Values are read from environment variables or a .env file at project root.
    When credentials are absent the app automatically enters demo mode.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bbg_client_id: str = Field(default="", description="Bloomberg Enterprise Console client ID")
    bbg_client_secret: str = Field(
        default="", description="Bloomberg Enterprise Console client secret (hex)"
    )
    bbg_uuid: int = Field(default=0, description="Bloomberg user UUID")
    bbg_host: str = Field(default="https://api.bloomberg.com", description="MARS API base URL")

    @property
    def demo_mode(self) -> bool:
        """True when Bloomberg credentials are not configured."""
        return not self.bbg_client_id or not self.bbg_client_secret or self.bbg_uuid == 0


settings = Settings()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Static constants (not credentials — safe to keep in source)
# ---------------------------------------------------------------------------

FLOAT_INDICES: list[str] = [
    "BZDIOVRA",
    "CLICP",
    "COOVIBR",
    "ESTRON",
    "MXIBTIIE",
    "SOFRRATE",
]

BOND_TO_SWPM_PAY_FREQUENCY: dict[int, str] = {
    0: "At Maturity",
    1: "Annual",
    2: "SemiAnnual",
    4: "Quarterly",
    12: "Monthly",
    28: "28 Days",
    52: "Weekly",
    360: "Daily",
}

CURVE_SIZE: int = 12000

CURVE_TYPES: list[str] = ["Raw Curve", "Zero Coupon", "Discount Factor"]

CURVE_API_FIELDS: dict[str, tuple[str, str, str, str]] = {
    "Raw Curve": ("maturityDate", "rate", "rawCurve", "parRate"),
    "Zero Coupon": ("date", "rate", "interpolatedCurve", "zeroRate"),
    "Discount Factor": ("date", "factor", "interpolatedCurve", "discountFactor"),
}

INTERPOLATION_METHODS: dict[str, str] = {
    "Piecewise Linear (Simple)": "INTERPOLATION_METHOD_LINEAR_SIMPLE",
    "Smooth Forward (Cont)": "INTERPOLATION_METHOD_SMOOTH_FWD",
    "Step Forward (Cont)": "INTERPOLATION_METHOD_STEP_FWD",
    "Piecewise Linear (Cont)": "INTERPOLATION_METHOD_LINEAR_CONT",
}

CURVE_SIDES: list[str] = ["Mid", "Bid", "Ask"]

INTERPOLATION_INTERVALS: list[str] = ["Daily", "Weekly", "Monthly"]

# Currency → CSA OIS curve ID mapping
CSA_CURVE_IDS: dict[str, str] = {
    "USD": "S400",
    "CAD": "S401",
    "CHF": "S418",
    "EUR": "S403",
    "GBP": "S405",
    "JPY": "S404",
    "SEK": "S417",
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

# Curves available in demo mode (pre-saved JSON files in demo_data/)
DEMO_CURVES: list[dict[str, str]] = [
    {"curve_id": "S329", "profile": "COP.OIS",     "label": "Colombia OIS",       "filename": "S329_COP.OIS.json"},
    {"curve_id": "S490", "profile": "USD.SOFR",    "label": "USD SOFR",            "filename": "S490_USD.SOFR.json"},
    {"curve_id": "S89",  "profile": "BRL.BM&F",    "label": "Brazil Pre x DI",     "filename": "S89_BRL.BMandF.json"},
    {"curve_id": "S583", "profile": "MXN.OIS.TIIE","label": "Mexico OIS TIIE",     "filename": "S583_MXN.OIS.TIIE.json"},
    {"curve_id": "S193", "profile": "CLP.6m",      "label": "Chile CLP 6m",        "filename": "S193_CLP.6m.json"},
    {"curve_id": "S514", "profile": "EUR.OIS.ESTR","label": "EUR OIS ESTR",        "filename": "S514_EUR.OIS.ESTR.json"},
    {"curve_id": "S374", "profile": "PEN.OIS",     "label": "Peru OIS",            "filename": "S374_PEN.OIS.json"},
]
