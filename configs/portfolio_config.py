"""
Portfolio configuration for the MARS_VIBE_CODING demo portfolio.

Defines the default portfolio name and the deal composition used by the
demo repository to load pre-saved pricing snapshots.

Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from configs.derivatives_config import (
    FX_KI_SPECS,
    FX_KO_SPECS,
    FX_RR_SPECS,
    FX_VANILLA_SPECS,
)
from configs.swaps_config import OIS_SWAP_SPECS, XCCY_SWAP_SPECS

PORTFOLIO_NAME: str = "MARS_VIBE_CODING"

AssetClass = Literal["OIS", "XCCY", "FX_VANILLA", "FX_RR", "FX_KI", "FX_KO"]

_SWAP_CLASSES: frozenset[str] = frozenset({"OIS", "XCCY"})
_FX_CLASSES: frozenset[str] = frozenset({"FX_VANILLA", "FX_RR", "FX_KI", "FX_KO"})


@dataclass(frozen=True)
class PortfolioDealDef:
    """One deal to include in the portfolio."""

    asset_class: AssetClass
    key: str
    label: str

    @property
    def is_swap(self) -> bool:
        return self.asset_class in _SWAP_CLASSES

    @property
    def is_fx(self) -> bool:
        return self.asset_class in _FX_CLASSES

    @property
    def demo_filename(self) -> str:
        """Filename under demo_data/ for this deal's pre-saved snapshot."""
        if self.is_swap:
            return f"{self.key}_5Y.json"
        return f"{self.asset_class}_{self.key}.json"

    @property
    def demo_subdir(self) -> str:
        """Subdirectory under demo_data/ for this deal type."""
        return "swaps" if self.is_swap else "fx_derivatives"


def _build_deals() -> list[PortfolioDealDef]:
    deals: list[PortfolioDealDef] = []

    for key, spec in OIS_SWAP_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="OIS", key=key, label=spec.label))
    for key, spec in XCCY_SWAP_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="XCCY", key=key, label=spec.label))

    for key, spec in FX_VANILLA_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="FX_VANILLA", key=key, label=spec.label))
    for key, spec in FX_RR_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="FX_RR", key=key, label=spec.label))
    for key, spec in FX_KI_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="FX_KI", key=key, label=spec.label))
    for key, spec in FX_KO_SPECS.items():
        deals.append(PortfolioDealDef(asset_class="FX_KO", key=key, label=spec.label))

    return deals


PORTFOLIO_DEALS: list[PortfolioDealDef] = _build_deals()

# ---------------------------------------------------------------------------
# MARS API portfolio pricing fields catalog
# Mapping: requestedField input name → short description.
# Source: Bloomberg MARS API documentation.
# ---------------------------------------------------------------------------

MARS_API_FIELDS: dict[str, str] = {
    "AccruedInterest": "Accrued interest in deal currency",
    "AccruedInterestPortCcy": "Accrued interest in portfolio currency",
    "AsOfTimestamp": "Pricing timestamp",
    "AssetClass": "Asset class",
    "AssetType": "Security type description",
    "BaseCurrency": "Base currency",
    "BloombergDealId": "Bloomberg deal identifier",
    "Call/Put": "Call or Put indicator",
    "Convexity": "Second-order rate sensitivity",
    "ContractSz": "Contract size / notional multiplier",
    "CostFX": "FX rate at time of booking",
    "CostPx": "Unit cost price",
    "CostVal": "Total cost in deal currency",
    "CostValPortCcy": "Total cost in portfolio currency",
    "Coupon": "Coupon rate",
    "CouponType": "Coupon type",
    "CreditDV01": "Credit DV01 in deal currency",
    "CreditDV01PortCcy": "Credit DV01 in portfolio currency",
    "CreditSprd": "Credit spread",
    "Currency": "Currency",
    "DayCount": "Day count convention",
    "DealCcy": "Deal currency of denomination",
    "Delta": "Delta — MV sensitivity to underlying price",
    "DeltaCcy1": "Delta in currency 1 (FX deals)",
    "DeltaCcy2": "Delta in currency 2 (FX deals)",
    "DeltaHedge": "Delta hedge quantity",
    "DeltaHome": "Delta in portfolio currency (FX deals)",
    "DeltaNotional": "Delta notional (dollar delta)",
    "DeltaSensitivity": "Delta sensitivity per unit",
    "Description": "Security description",
    "Direction": "Direction (pay/receive, buy/sell)",
    "DV01": "DV01 in deal currency",
    "DV01PortCcy": "DV01 in portfolio currency",
    "EffectiveDate": "Effective / start date",
    "EquityMoneyD": "Equity money delta",
    "EquityNotional": "Equity notional",
    "ErrorCode": "Error code",
    "ErrorMessage": "Error message",
    "Exercise": "Exercise style (European/American/Bermudan)",
    "ExpiryDate": "Expiry date",
    "FaceAmount": "Face amount in deal currency",
    "FaceAmountPortCcy": "Face amount in portfolio currency",
    "FloatIndex": "Floating rate index ticker",
    "Frequency": "Payment frequency",
    "FXMoneyD": "FX money delta",
    "FX_CCY1": "FX currency 1",
    "FX_CCY2": "FX currency 2",
    "Gamma": "Gamma — delta sensitivity to underlying",
    "GammaCcy1": "Gamma in currency 1 (FX deals)",
    "GammaCcy2": "Gamma in currency 2 (FX deals)",
    "GammaHome": "Gamma in portfolio currency (FX deals)",
    "G-Spread": "G-Spread",
    "I-Spread": "I-Spread",
    "IVal": "Intrinsic value in deal currency",
    "IValPortCcy": "Intrinsic value in portfolio currency",
    "Long/Short": "Long or short indicator",
    "MarketDataDate": "Market data date",
    "MaturityDate": "Maturity date",
    "MktFX": "Market FX rate (deal ccy → portfolio ccy)",
    "MktPx": "Market price",
    "MktVal": "Market value in deal currency",
    "MktValCcy1": "Market value in currency 1 (FX deals)",
    "MktValCcy2": "Market value in currency 2 (FX deals)",
    "MktValPortCcy": "Market value in portfolio currency",
    "ModifiedDuration": "Modified duration",
    "MoneyD": "Money delta (1% underlying move)",
    "MoneyDPortCcy": "Money delta in portfolio currency",
    "Multiplier": "Price-to-value multiplier",
    "Notional": "Notional (contract size × position)",
    "NotionalCcy": "Notional currency",
    "NotionalCcy1": "Notional currency 1 (FX deals)",
    "NotionalCcy2": "Notional currency 2 (FX deals)",
    "OAS": "Option-adjusted spread",
    "ParCoupon": "Par coupon",
    "PayCcy": "Pay leg currency",
    "PayFrequency": "Pay leg frequency",
    "PayLegRate": "Pay leg rate",
    "Phi": "Phi — IR sensitivity (FX deals)",
    "PhiPortCcy": "Phi in portfolio currency",
    "Position": "Position quantity",
    "Principal": "Clean market value",
    "PrincipalPortCcy": "Principal in portfolio currency",
    "PV01": "PV01 — 1bp fixed coupon sensitivity",
    "ReceiveCcy": "Receive leg currency",
    "ReceiveLegRate": "Receive leg rate",
    "Rho": "Rho — MV sensitivity to 1% IR shift",
    "RhoCcy1": "Rho in currency 1 (FX deals)",
    "RhoCcy2": "Rho in currency 2 (FX deals)",
    "RhoPortCcy": "Rho in portfolio currency",
    "Security": "Security ticker",
    "SecurityCustomID": "Custom security identifier",
    "SpreadDuration": "Spread duration (OAS-based)",
    "Strike": "Strike price",
    "Theta": "Theta — time decay per day",
    "ThetaPortCcy": "Theta in portfolio currency",
    "Ticker": "Bloomberg ticker",
    "TVal": "Time value in deal currency",
    "TValPortCcy": "Time value in portfolio currency",
    "Underlying": "Underlying security ticker",
    "UnderlyingCcy": "Underlying currency",
    "UndFwdPx": "Underlying forward price",
    "UndPx": "Underlying spot price",
    "UniqueID": "Unique identifier",
    "ValuationDate": "Valuation date",
    "Vanna": "Vanna — vega sensitivity to underlying",
    "VannaCcy1": "Vanna in currency 1 (FX deals)",
    "VannaCcy2": "Vanna in currency 2 (FX deals)",
    "Vega": "Vega — MV sensitivity to 1% vol shift",
    "VegaPortCcy": "Vega in portfolio currency",
    "Vol": "Implied volatility (%)",
    "Volga": "Volga — vega sensitivity to vol",
    "VolgaCcy1": "Volga in currency 1 (FX deals)",
    "VolgaCcy2": "Volga in currency 2 (FX deals)",
    "YASDuration": "Macaulay duration (YAS)",
    "YieldtoNextCall": "Yield to next call",
    "YTM": "Yield to maturity",
    "YTW": "Yield to worst",
}
