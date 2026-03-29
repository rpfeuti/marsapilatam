"""
KRR (Key Rate Risk) configuration.

Default Greek Definition ID and fields for Bloomberg MARS KRR requests.

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

# ---------------------------------------------------------------------------
# KRR Greek Definition
# To obtain your own ID: MARS <GO> → Settings → User Settings →
# Key Rate Risk → Greek Definition ID
# ---------------------------------------------------------------------------

KRR_DEFINITION_ID: str = "7609023221901295616"
KRR_DEFINITION_NAME: str = "mars api per currency krr shift zero annual"

# ---------------------------------------------------------------------------
# Default targets (matching the stress testing page defaults)
# ---------------------------------------------------------------------------

DEFAULT_DEAL_ID: str = "SLLVJ42Q Corp"
DEFAULT_PORTFOLIO_NAME: str = "MARS_VIBE_CODING"

# ---------------------------------------------------------------------------
# Fields to request alongside KRR (returned in pricingResult)
# ---------------------------------------------------------------------------

KRR_PRICING_FIELDS: list[str] = ["DV01", "Notional", "Ticker", "BloombergDealID"]

# ---------------------------------------------------------------------------
# Demo-mode fallback tenors (used when constructing synthetic KRR data).
# Live responses return their own per-curve tenor labels dynamically.
# ---------------------------------------------------------------------------

DEMO_KRR_TENORS_USD: list[str] = [
    "1 MO", "3 MO", "6 MO", "1 YR", "2 YR", "3 YR", "4 YR", "5 YR",
    "7 YR", "10 YR", "20 YR", "30 YR",
]

DEMO_KRR_TENORS_LOCAL: list[str] = [
    "92 DY", "184 DY", "366 DY", "549 DY", "2 YR", "3 YR", "4 YR", "5 YR",
]
