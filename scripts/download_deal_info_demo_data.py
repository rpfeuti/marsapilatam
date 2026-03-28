"""
Download demo data for the Deal Information page: the full deal types list
and parameter schemas for commonly used deal types.

Run from the project root with live Bloomberg credentials in .env:
    python scripts/download_deal_info_demo_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configs.settings import settings
from services.deal_info_service import DealInfoService, _DEMO_DEAL_TYPES

DEMO_DATA_DIR  = Path(__file__).resolve().parent.parent / "demo_data" / "deal_info"
SCHEMAS_DIR    = DEMO_DATA_DIR / "schemas"


def download_all() -> None:
    if settings.demo_mode:
        print(
            "ERROR: Bloomberg credentials are not configured. "
            "Set BBG_CLIENT_ID, BBG_CLIENT_SECRET, and BBG_UUID in .env"
        )
        sys.exit(1)

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    svc = DealInfoService.from_settings()

    # --- Deal types list ---
    print("Fetching deal types ...")
    deal_types = svc.fetch_deal_types()
    print(f"  {len(deal_types)} deal types retrieved")

    types_path = DEMO_DATA_DIR / "deal_types.json"
    types_path.write_text(
        json.dumps(deal_types, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Saved -> deal_types.json\n")

    # --- Schemas for commonly used deal types ---
    schema_codes = [code for code, _ in _DEMO_DEAL_TYPES]
    print(f"Downloading schemas for {len(schema_codes)} deal types ...\n")

    for code in schema_codes:
        print(f"  {code}")
        try:
            schema = svc.fetch_deal_schema(code)
        except Exception as exc:
            print(f"    ERROR: {exc}")
            continue

        if not schema:
            print("    SKIP: empty schema")
            continue

        filename = code.replace(".", "_") + ".json"
        out_path = SCHEMAS_DIR / filename
        out_path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(f"    Saved -> schemas/{filename}")

    print("\nDone.")


if __name__ == "__main__":
    download_all()
