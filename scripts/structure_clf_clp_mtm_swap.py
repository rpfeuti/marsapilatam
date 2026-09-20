"""
Structure and save a mark-to-market CLF fixed / CLP floating swap on Bloomberg MARS.

Leg 1: CLF fixed rate (direction controlled by --direction flag)
Leg 2: CLP floating (CLICP, opposite direction)
Deal-level: IsMTMSwap=true, MTMSwapCurrency=CLP

Run from project root (live credentials required):
    python scripts/structure_clf_clp_mtm_swap.py
    python scripts/structure_clf_clp_mtm_swap.py --direction Pay

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

import argparse
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

DEAL_TYPE = "IR.FXFL"
DIRECTION = "Receive"
NOTIONAL_CLF = 10_000.0
CLFCLP_RATE = 40_809.44
NOTIONAL_CLP = NOTIONAL_CLF * CLFCLP_RATE
FIXED_RATE = 0.03
FLOAT_INDEX = "CLICP"
PAY_FREQUENCY = "SemiAnnual"
DAY_COUNT = "ACT/360"
MTM_CURRENCY = "CLP"

EFFECTIVE_DATE = date(2026, 6, 26)
MATURITY_DATE = date(2031, 6, 26)


def build_clf_clp_mtm_body(
    session_id: str,
    *,
    effective: date,
    maturity: date,
    direction: str = DIRECTION,
    notional_clf: float = NOTIONAL_CLF,
    notional_clp: float = NOTIONAL_CLP,
    fixed_rate: float = FIXED_RATE,
    mtm_currency: str = MTM_CURRENCY,
) -> dict[str, Any]:
    """Build dealStructureOverride for a CLF fixed / CLP float FXFL MtM swap.

    The fixed leg takes *direction*; the floating leg is automatically assigned the opposite.
    """
    opposite = "Pay" if direction == "Receive" else "Receive"

    leg1 = _build_leg_params(
        direction=direction,
        notional=notional_clf,
        currency="CLF",
        effective=effective,
        maturity=maturity,
        fixed_rate=fixed_rate,
        float_index=None,
        pay_frequency=PAY_FREQUENCY,
        day_count=DAY_COUNT,
    )
    leg2 = _build_leg_params(
        direction=opposite,
        notional=notional_clp,
        currency="CLP",
        effective=effective,
        maturity=maturity,
        fixed_rate=None,
        float_index=FLOAT_INDEX,
        pay_frequency=PAY_FREQUENCY,
        day_count=DAY_COUNT,
    )

    return {
        "sessionId": session_id,
        "tail": DEAL_TYPE,
        "dealStructureOverride": {
            "param": [
                {"name": "IsMTMSwap", "value": {"boolVal": True}},
                {"name": "MTMSwapCurrency", "value": {"stringVal": mtm_currency}},
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
    parser = argparse.ArgumentParser(description="Structure a CLF/CLP FXFL MtM swap on Bloomberg MARS.")
    parser.add_argument(
        "--direction",
        choices=["Receive", "Pay"],
        default=DIRECTION,
        help="Direction of the fixed CLF leg (default: %(default)s). "
             "The floating CLP leg takes the opposite direction automatically.",
    )
    args = parser.parse_args()

    if settings.demo_mode:
        print("ERROR: Save requires live MARS credentials (demo_mode=False).")
        sys.exit(1)

    client = MarsClient(settings)
    body = build_clf_clp_mtm_body(
        client.session_id,
        effective=EFFECTIVE_DATE,
        maturity=MATURITY_DATE,
        direction=args.direction,
    )

    deal_handle, bloomberg_deal_id = structure_and_save(client, body)

    fixed_direction = args.direction
    float_direction = "Pay" if fixed_direction == "Receive" else "Receive"
    out = {
        "bloomberg_deal_id": bloomberg_deal_id,
        "deal_handle": deal_handle,
        "deal_type": DEAL_TYPE,
        "is_mtm": True,
        "mtm_currency": MTM_CURRENCY,
        "clfclp_rate": CLFCLP_RATE,
        "leg1": {"currency": "CLF", "type": "fixed", "direction": fixed_direction, "notional": NOTIONAL_CLF},
        "leg2": {"currency": "CLP", "type": "float", "index": FLOAT_INDEX, "direction": float_direction, "notional": NOTIONAL_CLP},
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nBloomberg deal ID: {bloomberg_deal_id}")


if __name__ == "__main__":
    main()
