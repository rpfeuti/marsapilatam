"""
Structure and save Goldman CLF/CLP non-deliverable fixed-fixed swaps (IR.NDSFX) on Bloomberg MARS.

Source: term sheet Goldman.xlsx

Leg 1: CLF fixed, Pay, rate 0%, At Maturity, ACT/360
Leg 2: CLP fixed, Receive, rate 0%, At Maturity, ACT/360
Counterparty: CLI_GS
CustomId: ITAU_<id>

Run from project root (live credentials required):
    python scripts/structure_goldman_clf_clp_ndsfx.py

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

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloomberg.exceptions import StructuringError
from bloomberg.webapi.mars_client import MarsClient
from configs.settings import settings
from services.swaps_service import _build_leg_params

DEAL_TYPE    = "IR.NDSFX"
COUNTERPARTY = "CLI_GS"
PAY_FREQ     = "At Maturity"
DAY_COUNT    = "ACT/360"
FIXED_RATE   = 0.0

# Source: term sheet Goldman.xlsx — Hoja1
SWAPS: list[dict[str, Any]] = [
    {
        "id":           11504129,
        "effective":    date(2025, 11, 28),
        "maturity":     date(2026,  8,  7),
        "notional_clf": 900_000,
        "notional_clp": 36_311_400_000,
    },
    {
        "id":           11935957,
        "effective":    date(2026,  3, 11),
        "maturity":     date(2027, 11,  9),
        "notional_clf": 300_000,
        "notional_clp": 12_624_000_000,
    },
    {
        "id":           11953382,
        "effective":    date(2026,  3, 16),
        "maturity":     date(2027,  9,  9),
        "notional_clf": 300_000,
        "notional_clp": 12_522_300_000,
    },
    {
        "id":           11953383,
        "effective":    date(2026,  3, 16),
        "maturity":     date(2027, 11,  9),
        "notional_clf": 300_000,
        "notional_clp": 12_612_000_000,
    },
    {
        "id":           12069614,
        "effective":    date(2026,  4, 14),
        "maturity":     date(2028,  1,  7),
        "notional_clf": 300_000,
        "notional_clp": 12_813_000_000,
    },
]


def build_body(session_id: str, swap: dict[str, Any]) -> dict[str, Any]:
    """Build dealStructureOverride body for a single CLF/CLP NDSFX swap."""
    leg1 = _build_leg_params(
        direction="Pay",
        notional=swap["notional_clf"],
        currency="CLF",
        effective=swap["effective"],
        maturity=swap["maturity"],
        fixed_rate=FIXED_RATE,
        float_index=None,
        pay_frequency=PAY_FREQ,
        day_count=DAY_COUNT,
    )
    leg2 = _build_leg_params(
        direction="Receive",
        notional=swap["notional_clp"],
        currency="CLP",
        effective=swap["effective"],
        maturity=swap["maturity"],
        fixed_rate=FIXED_RATE,
        float_index=None,
        pay_frequency=PAY_FREQ,
        day_count=DAY_COUNT,
    )
    return {
        "sessionId": session_id,
        "tail": DEAL_TYPE,
        "dealStructureOverride": {
            "param": [
                {"name": "CustomId",     "value": {"stringVal": f"ITAU_{swap['id']}"}},
                {"name": "Counterparty", "value": {"stringVal": COUNTERPARTY}},
            ],
            "leg": [{"param": leg1}, {"param": leg2}],
        },
    }


def structure_and_save(client: MarsClient, body: dict[str, Any]) -> tuple[str, str]:
    """Structure a temporary deal and save it permanently. Returns (deal_handle, deal_id)."""
    struc_resp = client.send("POST", "/marswebapi/v1/deals/temporary", body)

    if "error" in struc_resp:
        raise StructuringError(struc_resp.get("error_description", str(struc_resp["error"])))

    try:
        sr = struc_resp["results"][0]["structureResponse"]
        deal_handle = sr["dealHandle"]
    except (KeyError, IndexError) as exc:
        raise StructuringError(f"Unexpected structure response: {struc_resp}") from exc

    if not deal_handle:
        notifications = sr.get("returnStatus", {}).get("notifications", [])
        errors = [n["message"] for n in notifications if n.get("type") == "S_ERROR"]
        raise StructuringError(errors[0] if errors else "Unknown structuring failure")

    save_resp = client.send("PATCH", f"/marswebapi/v1/deals/temporary/{deal_handle}", {})
    if "error" in save_resp:
        raise StructuringError(save_resp.get("error_description", str(save_resp["error"])))

    try:
        deal_id = save_resp["results"][0]["saveResponse"]["dealId"]
    except (KeyError, IndexError):
        deal_id = deal_handle

    return deal_handle, deal_id


def main() -> None:
    if settings.demo_mode:
        print("ERROR: Save requires live MARS credentials (demo_mode=False).")
        sys.exit(1)

    client = MarsClient(settings)
    results = []

    for swap in SWAPS:
        custom_id = f"ITAU_{swap['id']}"
        print(f"Structuring {custom_id} ...", end=" ", flush=True)
        try:
            body = build_body(client.session_id, swap)
            deal_handle, bloomberg_deal_id = structure_and_save(client, body)
            entry = {
                "bloomberg_deal_id": bloomberg_deal_id,
                "deal_handle":       deal_handle,
                "custom_id":         custom_id,
                "effective":         str(swap["effective"]),
                "maturity":          str(swap["maturity"]),
                "notional_clf":      swap["notional_clf"],
                "notional_clp":      swap["notional_clp"],
                "counterparty":      COUNTERPARTY,
                "deal_type":         DEAL_TYPE,
            }
            print(f"OK -> {bloomberg_deal_id}")
        except StructuringError as exc:
            entry = {"custom_id": custom_id, "error": str(exc)}
            print(f"ERROR: {exc}")

        results.append(entry)

    print("\n=== RESULTS ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
