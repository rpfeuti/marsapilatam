"""
Bloomberg BLPAPI field values → MARS dealStructureOverride strings.

Reference: internal BLPAPI ↔ MARS de-para tables (DAY_CNT_DES, CPN_FREQ).

Copyright 2026, Bloomberg Finance L.P.
"""

from __future__ import annotations

import re
from typing import Any

# CPN_FREQ (Bloomberg integer) → MARS PayFrequency selectionVal.
# Codes marked unsupported in MARS must map to None (caller may warn).
_CPN_FREQ_TO_MARS_PAY: dict[int, str | None] = {
    0:   "At Maturity",
    1:   "Annual",
    2:   "SemiAnnual",
    3:   None,  # NOT SUPPORTED in MARS AP
    4:   "Quarterly",
    6:   None,  # NOT SUPPORTED
    7:   None,  # NOT SUPPORTED
    12:  "Monthly",
    28:  "28 Days",
    35:  None,  # NOT SUPPORTED
    49:  None,  # NOT SUPPORTED
    52:  "Weekly",
    360: "Daily",
}


def cpn_freq_to_mars_pay_frequency(freq: Any) -> str | None:
    """Map Bloomberg CPN_FREQ integer to MARS PayFrequency string, or None if unsupported."""
    try:
        n = int(freq)
    except (TypeError, ValueError):
        return None
    val = _CPN_FREQ_TO_MARS_PAY.get(n)
    if val is None and n not in _CPN_FREQ_TO_MARS_PAY:
        return None
    return val


# Ordered (substring test, MARS DayCount). First match wins. Uppercase input.
_DAYCNT_RULES: list[tuple[str, str]] = [
    ("ISDA 30E/360", "30E/360"),
    ("30E/360", "30E/360"),
    ("BUS DAYS/252", "DU/252"),
    ("BUS DAY/252NON-EOM", "DU/252"),
    ("BUSINESS/252", "DU/252"),
    ("BD/252", "DU/252"),
    ("BUS/252", "DU/252"),
    ("ACT/360 NON-EOM", "ACT/360"),
    ("30/360 NON-EOM", "30/360"),
    ("ISMA30/360 NON-EOM", "30/360"),
    ("ISMA-30/360", "30/360"),
    ("ISMA 30/360", "30/360"),
    ("ISDA SWAPS:30/360", "30/360"),
    ("US MUNI: 30/360", "30/360"),
    ("GERMAN:30/360", "30/360"),
    ("ISDA ACT/ACT", "ACT/ACT"),
    ("AFB ACT/ACT", "ACT/ACT"),
    ("NL/ACT", "NL/ACT"),
    ("NL/360", "NL/360"),
    ("NL/365", "NL/365"),
    ("30/ACT", "30/ACT"),
    ("30/365", "30/365"),
    ("ACT/364", "ACT/364"),
    ("28/360", "28/360"),
    ("ACT/ACT", "ACT/ACT"),
    ("ACT/360", "ACT/360"),
    ("ACT/365", "ACT/365"),
    ("30/360", "30/360"),
]


def day_cnt_des_to_mars(des: Any) -> str | None:
    """Map Bloomberg DAY_CNT_DES text to MARS DayCount selection string."""
    if des is None:
        return None
    s = str(des).strip().upper()
    s = re.sub(r"\(\d+\)\s*$", "", s).strip()
    s = re.sub(r"\s+", " ", s)

    for needle, mars in _DAYCNT_RULES:
        if needle in s:
            return mars

    if "ACT/ACT" in s or "ACT ACT" in s:
        return "ACT/ACT"
    if "ACT/360" in s or "ACT 360" in s:
        return "ACT/360"
    if "ACT/365" in s or "ACT 365" in s:
        return "ACT/365"
    if "30/360" in s or "30 360" in s:
        return "30/360"

    m = re.search(r"(ACT/\d+)", s)
    if m:
        return m.group(1)
    return None
