"""
IRRBB stress testing configuration.

Defines the tenor x scenario matrix for IRRBB interest rate shock scenarios
and the default deal used for stress testing.

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

DEFAULT_DEAL_ID: str = "SLLVJ42Q Corp"
DEFAULT_PORTFOLIO_NAME: str = "MARS_VIBE_CODING"

STRESS_PRICING_FIELDS: list[str] = [
    "MktVal", "MktValPortCcy", "DV01", "DV01PortCcy", "PV01", "MktPx", "AccruedInterest", "Delta",
]

STRESS_SCENARIO_FIELDS: list[str] = [
    "MktVal", "MktValPortCcy", "DV01", "DV01PortCcy", "Delta",
]

IRRBB_TENORS: list[str] = [
    "1D", "7D", "1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y", "20Y",
]

IRRBB_SCENARIOS: list[str] = [
    "Parallel Up",
    "Parallel Down",
    "Steepener",
    "Flattener",
    "Short Rate Up",
    "Short Rate Down",
]

# Tenor x Scenario bp shift matrix.
# Structure: {scenario_name: {tenor: shift_bp}}
# Cells not specified default to 0.
# Values based on Basel III / EBA IRRBB standard shock approximations.
IRRBB_MATRIX: dict[str, dict[str, float]] = {
    "Parallel Up": {
        "1D": 200.0, "7D": 200.0, "1M": 200.0, "3M": 200.0, "6M": 200.0,
        "1Y": 200.0, "2Y": 200.0, "3Y": 200.0, "5Y": 200.0, "7Y": 200.0,
        "10Y": 200.0, "15Y": 200.0, "20Y": 200.0,
    },
    "Parallel Down": {
        "1D": -200.0, "7D": -200.0, "1M": -200.0, "3M": -200.0, "6M": -200.0,
        "1Y": -200.0, "2Y": -200.0, "3Y": -200.0, "5Y": -200.0, "7Y": -200.0,
        "10Y": -200.0, "15Y": -200.0, "20Y": -200.0,
    },
    "Steepener": {
        "1D": -100.0, "7D": -90.0, "1M": -80.0, "3M": -70.0, "6M": -60.0,
        "1Y": -40.0, "2Y": -20.0, "3Y": 0.0, "5Y": 20.0, "7Y": 50.0,
        "10Y": 80.0, "15Y": 90.0, "20Y": 100.0,
    },
    "Flattener": {
        "1D": 100.0, "7D": 90.0, "1M": 80.0, "3M": 70.0, "6M": 60.0,
        "1Y": 40.0, "2Y": 20.0, "3Y": 0.0, "5Y": -20.0, "7Y": -50.0,
        "10Y": -80.0, "15Y": -90.0, "20Y": -100.0,
    },
    "Short Rate Up": {
        "1D": 300.0, "7D": 290.0, "1M": 280.0, "3M": 250.0, "6M": 200.0,
        "1Y": 130.0, "2Y": 80.0, "3Y": 40.0, "5Y": 10.0, "7Y": 0.0,
        "10Y": 0.0, "15Y": 0.0, "20Y": 0.0,
    },
    "Short Rate Down": {
        "1D": -300.0, "7D": -290.0, "1M": -280.0, "3M": -250.0, "6M": -200.0,
        "1Y": -130.0, "2Y": -80.0, "3Y": -40.0, "5Y": -10.0, "7Y": 0.0,
        "10Y": 0.0, "15Y": 0.0, "20Y": 0.0,
    },
}
