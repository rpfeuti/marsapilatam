"""Copyright 2026, Bloomberg Finance L.P.

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

from configs.curves_catalog import CURVES_BY_ID, CURVES_BY_LABEL, CURVES_CATALOG
from configs.curves_config import (
    BOND_TO_SWPM_PAY_FREQUENCY,
    CURVE_SIDES,
    CURVE_SIZE,
    CURVE_SPECS,
    CURVE_TYPES,
    DEMO_CURVES,
    FLOAT_INDICES,
    INTERPOLATION_INTERVALS,
    INTERPOLATION_METHODS,
    CurveSpec,
    CurveType,
    DemoCurve,
    Side,
)
from configs.i18n import LANGUAGES, lang_selector, t
from configs.settings import settings
from configs.swaps_config import (
    OIS_BY_LABEL,
    OIS_DEMO_SNAPSHOTS,
    OIS_LABELS,
    OIS_SWAP_SPECS,
    SWAP_DAY_COUNTS,
    SWAP_DIRECTIONS,
    SWAP_PAY_FREQUENCIES,
    XCCY_BY_LABEL,
    XCCY_DEMO_SNAPSHOTS,
    XCCY_LABELS,
    XCCY_SWAP_SPECS,
    SwapDemoSnapshot,
    SwapSpec,
)

__all__ = [
    # credentials
    "settings",
    # curve types and specs
    "CurveType", "CurveSpec", "DemoCurve", "Side",
    "CURVE_SPECS", "CURVE_TYPES", "CURVE_SIDES", "CURVE_SIZE",
    "INTERPOLATION_METHODS", "INTERPOLATION_INTERVALS",
    "DEMO_CURVES",
    # instrument constants
    "FLOAT_INDICES", "BOND_TO_SWPM_PAY_FREQUENCY",
    # curve catalog
    "CURVES_CATALOG", "CURVES_BY_LABEL", "CURVES_BY_ID",
    # swap config
    "SwapSpec", "SwapDemoSnapshot",
    "OIS_SWAP_SPECS", "XCCY_SWAP_SPECS",
    "OIS_LABELS", "XCCY_LABELS",
    "OIS_BY_LABEL", "XCCY_BY_LABEL",
    "SWAP_DIRECTIONS", "SWAP_PAY_FREQUENCIES", "SWAP_DAY_COUNTS",
    "OIS_DEMO_SNAPSHOTS", "XCCY_DEMO_SNAPSHOTS",
    # i18n
    "t", "lang_selector", "LANGUAGES",
]
