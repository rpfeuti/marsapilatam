"""
Page — Deal Information

Browse all MARS deal types and inspect their full parameter schemas
(deal-level and per-leg), including field names, types, modes,
solvable targets, and allowed values for selection fields.

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

import pandas as pd
import streamlit as st

from configs.i18n import t
from configs.settings import DEMO_DATE, settings
from services.deal_info_service import DealInfoService

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title(t("dealinfo.title"))
st.caption(t("dealinfo.caption"))

IS_DEMO = settings.demo_mode

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")

# ---------------------------------------------------------------------------
# Cached service
# ---------------------------------------------------------------------------

_SVC_VERSION = "5"


@st.cache_resource(show_spinner=t("dealinfo.spinner_types"))
def _get_service(v: str = _SVC_VERSION) -> DealInfoService:
    return DealInfoService.from_settings()


@st.cache_data(ttl=3600, show_spinner=t("dealinfo.spinner_types"))
def _get_deal_types(v: str = _SVC_VERSION) -> list[tuple[str, str]]:
    return _get_service().fetch_deal_types()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _params_to_df(params: list[dict]) -> pd.DataFrame:
    """Convert a list of schema parameter dicts to a display DataFrame."""
    rows: list[dict[str, str]] = []
    for p in params:
        val_info = p.get("value", {})
        val_type = val_info.get("type", "")

        allowed = ""
        if val_type == "SELECTION_VAL":
            items = (
                val_info.get("valueInfo", {})
                .get("selection", {})
                .get("items", [])
            )
            allowed = ", ".join(it.get("value", "") for it in items)

        rows.append({
            t("dealinfo.col_name"):        p.get("name", ""),
            t("dealinfo.col_type"):        val_type,
            t("dealinfo.col_mode"):        p.get("mode", ""),
            t("dealinfo.col_solvable"):    t("common.yes") if p.get("solvableTarget") else "",
            t("dealinfo.col_category"):    p.get("category", ""),
            t("dealinfo.col_description"): p.get("description", ""),
            t("dealinfo.col_allowed"):     allowed,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

deal_types = _get_deal_types()
type_labels = [f"{code} — {desc}" if desc else code for code, desc in deal_types]
type_codes = [code for code, _ in deal_types]

default_idx = type_codes.index("IR.OIS") if "IR.OIS" in type_codes else 0

col_sel, _, _ = st.columns(3)
with col_sel:
    selected_label = st.selectbox(
        t("dealinfo.deal_type_label"),
        options=type_labels,
        index=default_idx,
    )
    selected_type = type_codes[type_labels.index(selected_label)]
    st.caption(t("dealinfo.types_available", n=len(deal_types)))
    load_clicked = st.button(
        t("dealinfo.btn_load"),
        type="primary",
    )

# ---------------------------------------------------------------------------
# MARS API capabilities reference
# ---------------------------------------------------------------------------

_API_DOCS = """
## Bloomberg MARS API — Deal Schemas & Structuring

Bloomberg MARS supports pricing and risk analytics for every major asset class — interest rate
derivatives, FX options, inflation swaps, credit default swaps, equity derivatives, mortgages,
and more. Every deal type in MARS has a fully documented parameter schema accessible via the API:
field names, value types, usage modes, and enumeration values. This is the same schema engine that
drives Bloomberg's Excel toolkits (Swap Toolkit, Derivative Toolkit) and the SWPM, OVML, and DLIB
Terminal functions. Making schemas available via API means developers can programmatically discover
valid deal structures, validate payloads before sending them to the pricing engine, and build
client-facing structuring interfaces without any dependency on the Bloomberg Terminal.

### Why deal schemas matter

When building integrations with the MARS pricing engine, every `dealStructureOverride` payload must
use exactly the right field names, value type keys, and enumeration strings — there is no tolerance
for guessing. The `/dealSchema` endpoint is the authoritative source for all of this, enabling:

- **Discovery** — find out which parameters exist for any deal type across IR, FX, credit, equity
- **Validation** — check that your override payloads use the correct field names before sending
- **Solvable field identification** — know which parameters the engine can solve for
  (e.g. find the par rate that makes MktVal = 0, or the notional that targets a given DV01)
- **Enumeration browsing** — see all allowed values for selection fields like day count,
  frequency, stub convention, and compounding type
- **Schema-driven UI** — build dynamic forms that adapt to the selected deal type automatically

### Asset classes and deal types (sample)

| Asset Class | Example deal types |
|---|---|
| Interest Rates | `IR.OIS`, `IR.XCCY`, `IR.IRS`, `IR.BASIS`, `IR.NDS`, `IR.INFLATION` |
| FX | `FX.VANILLAOPT`, `FX.BARRIER`, `FX.DIGITAL`, `FX.FORWARD`, `FX.SWAP` |
| Credit | `CREDIT.CDS`, `CREDIT.CDX`, `CREDIT.TOTALRETURNSWAP` |
| Equity | `EQ.VANILLAOPT`, `EQ.BARRIER`, `EQ.TOTALRETURNSWAP` |
| Mortgages | `MORTGAGE.FIXEDRATE`, `MORTGAGE.ARM` |

### Endpoints

---

**`GET /marswebapi/v1/dealType`** — List all supported deal type strings

No request body required. Returns an array of all deal type strings available in MARS.
Use these strings as the `tail` parameter in `/dealSchema` and as the `tail` field in
`dealStructureOverride` payloads.

---

**`GET /marswebapi/v1/dealSchema`** — Retrieve the full parameter schema for a deal type

```json
{ "tail": "IR.OIS" }
```

Returns `dealStructure.param[]` (deal-level fields) and `dealStructure.leg[].param[]` (per-leg fields).

### Parameter object structure

Each parameter in the schema response has the following fields:

| Field | Description |
|---|---|
| `name` | **Exact** parameter name to use in `dealStructureOverride` — case-sensitive |
| `value` | Object with one key identifying the value type (see value types below) |
| `usage` | `INPUT` — must be provided to structure the deal; `SOLVABLE` — can be a solve target |
| `description` | Human-readable label displayed in Bloomberg Terminal |
| `default` | Default value applied by MARS if the parameter is omitted |

### Parameter value types

| Type key | Used for | Example |
|---|---|---|
| `doubleVal` | Numeric values: notional, rate, spread, strike | `{ "doubleVal": 10000000 }` |
| `stringVal` | Dates as strings, curve IDs, free text | `{ "stringVal": "2031-03-29" }` |
| `selectionVal` | Enumerated choices with a fixed list of valid values | `{ "selectionVal": { "value": "ACT/360" } }` |
| `dateVal` | Structured date objects | `{ "dateVal": { "year": 2031, "month": 3, "day": 29 } }` |
| `intVal` | Integer values | `{ "intVal": 2 }` |

### How to use schema data to build a pricing payload

1. Call `GET /dealSchema` with `{ "tail": "IR.OIS" }`
2. Find the parameters you want to override in `dealStructure.leg[].param[]`
3. Note the exact `name` string and the value type key in `value`
4. Construct your `dealStructureOverride` using those exact names and type keys
5. Send the override to `POST /deals/temporary` to structure the deal in-memory
6. Pass the returned `bloombergDealId` to `POST /securitiesPricing` to price it
"""

if not load_clicked:
    st.info(t("dealinfo.info_idle"))
    st.divider()
    with st.expander("About the MARS API", expanded=True):
        st.markdown(_API_DOCS)
    st.stop()

if IS_DEMO:
    st.warning(t("common.demo_banner", date=DEMO_DATE), icon="🔒")
    st.stop()

# ---------------------------------------------------------------------------
# Fetch and display schema
# ---------------------------------------------------------------------------

with st.spinner(t("dealinfo.spinner")):
    svc = _get_service()
    schema_resp = svc.fetch_deal_schema(selected_type)

if not schema_resp:
    st.error(t("dealinfo.no_params"))
    st.stop()

status = schema_resp.get("returnStatus", {})
if status.get("status") == "S_FAILURE":
    notifications = status.get("notifications", [])
    msg = notifications[0].get("message", "") if notifications else "Unknown error"
    st.error(f"**{selected_type}** is not supported: {msg}")
    st.stop()

structure = schema_resp.get("dealStructure", {})
if not structure:
    st.error(t("dealinfo.no_params"))
    st.stop()

deal_params = structure.get("param", [])
legs = structure.get("leg", [])

total_params = len(deal_params) + sum(len(leg.get("param", [])) for leg in legs)
solvable_count = (
    sum(1 for p in deal_params if p.get("solvableTarget"))
    + sum(1 for leg in legs for p in leg.get("param", []) if p.get("solvableTarget"))
)

st.markdown("---")
summary = t("dealinfo.summary").format(
    total=total_params, legs=len(legs), solvable=solvable_count,
)
st.caption(summary)

# Deal-level parameters
if deal_params:
    st.subheader(t("dealinfo.deal_params_header"))
    st.dataframe(
        _params_to_df(deal_params),
        use_container_width=True,
        hide_index=True,
    )

# Per-leg parameters
for i, leg in enumerate(legs, start=1):
    leg_params = leg.get("param", [])
    if not leg_params:
        continue
    header = t("dealinfo.leg_header").replace("{n}", str(i))
    st.subheader(header)
    st.dataframe(
        _params_to_df(leg_params),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
with st.expander("About the MARS API", expanded=True):
    st.markdown(_API_DOCS)
