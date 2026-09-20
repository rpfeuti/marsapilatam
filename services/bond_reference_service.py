"""
Bond reference data via Bloomberg Desktop API (BLPAPI).

Fetches YTM (mid), coupon, maturity, currency, payment frequency, and day-count
for use in asset-swap pricing — **fixed USD leg should use YTM, not coupon**.
Demo mode returns hardcoded snapshots for known IDs.

Copyright 2026, Bloomberg Finance L.P.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from bloomberg.exceptions import BlpapiError
from configs.mars_bbg_mappings import cpn_freq_to_mars_pay_frequency, day_cnt_des_to_mars
from configs.settings import settings

log = logging.getLogger(__name__)

_BOND_FIELDS = [
    "SECURITY_NAME",
    "CRNCY",
    "CPN",
    "YLD_YTM_MID",
    "MATURITY",
    "CPN_FREQ",
    "DAY_CNT_DES",
    "AMT_OUTSTANDING",
]

# Demo snapshots — key = normalized identifier (uppercase, stripped)
_DEMO_BONDS: dict[str, dict[str, Any]] = {
    "AN9676742 CORP": {
        "name": "CHILE 3.86 06/21/47",
        "currency": "USD",
        "coupon_pct": 3.86,
        "ytm_pct": 5.5876,
        "maturity": "2047-06-21",
        "cpn_freq_raw": 2,
        "day_cnt_des_raw": "30/360",
        "pay_frequency": "SemiAnnual",
        "day_count": "30/360",
        "amt_outstanding_usd": 1_051_796_000.0,
    },
}


def _norm_id(identifier: str) -> str:
    return identifier.strip().upper()


def _parse_maturity(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, datetime):
        return val.date().isoformat()
    s = str(val).strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def _parse_coupon_pct(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


class BondReferenceService:
    """Bond reference lookup: live BLPAPI or demo table."""

    def __init__(self, use_demo: bool) -> None:
        self._demo = use_demo

    def lookup(self, identifier: str) -> dict[str, Any]:
        key = _norm_id(identifier)
        if self._demo:
            return self._demo_lookup(key, original=identifier.strip())

        from bloomberg.blpapi_client import BlpapiClient

        try:
            with BlpapiClient(host=settings.blpapi_host, port=settings.blpapi_port) as client:
                raw = client.bdp([identifier.strip()], _BOND_FIELDS)
        except BlpapiError as exc:
            log.warning("Bond BLPAPI lookup failed: %s", exc)
            return {
                "identifier": identifier.strip(),
                "error": f"Bloomberg Desktop API indisponível: {exc}",
            }

        row = raw.get(identifier.strip()) or raw.get(identifier.strip().upper())
        if not row:
            row = next(iter(raw.values()), {}) if raw else {}

        if not row:
            return {
                "identifier": identifier.strip(),
                "error": "Nenhum dado retornado para este identificador no Bloomberg.",
            }

        name = row.get("SECURITY_NAME")
        ccy  = row.get("CRNCY")
        cpn  = _parse_coupon_pct(row.get("CPN"))
        ytm  = _parse_coupon_pct(row.get("YLD_YTM_MID"))
        mat  = _parse_maturity(row.get("MATURITY"))
        cpn_raw = row.get("CPN_FREQ")
        dc_raw  = row.get("DAY_CNT_DES")
        pay     = cpn_freq_to_mars_pay_frequency(cpn_raw)
        dc      = day_cnt_des_to_mars(dc_raw)
        amt  = row.get("AMT_OUTSTANDING")

        out: dict[str, Any] = {
            "identifier": identifier.strip(),
            "name":         name,
            "currency":     ccy,
            "ytm_pct":      ytm,
            "coupon_pct":   cpn,
            "maturity":     mat,
            "cpn_freq_raw": cpn_raw,
            "day_cnt_des_raw": str(dc_raw).strip() if dc_raw is not None else None,
            "pay_frequency": pay,
            "day_count":    dc,
        }
        if isinstance(amt, (int, float)) and amt > 0:
            out["amt_outstanding_usd"] = float(amt)

        if ccy and str(ccy).upper() != "USD":
            out["warning"] = (
                "Bond não é USD — confira se o par de asset swap (XCCY) está correto."
            )
        if pay is None and cpn_raw is not None:
            out.setdefault("warnings", []).append(
                f"CPN_FREQ={cpn_raw} não tem PayFrequency suportada no MARS; "
                "ajuste manual ou outro título pode ser necessário."
            )
        if dc is None and dc_raw is not None:
            out.setdefault("warnings", []).append(
                f"DAY_CNT_DES não mapeado para MARS: {dc_raw!r}."
            )

        return out

    def _demo_lookup(self, key: str, original: str) -> dict[str, Any]:
        snap = _DEMO_BONDS.get(key)
        if not snap:
            return {
                "identifier": original,
                "error": (
                    f"Demo: bond {original!r} não encontrado. "
                    "Use AN9676742 Corp ou rode em modo live com Bloomberg."
                ),
            }
        out_demo: dict[str, Any] = {
            "identifier": original,
            "name": snap["name"],
            "currency": snap["currency"],
            "ytm_pct": snap["ytm_pct"],
            "coupon_pct": snap["coupon_pct"],
            "maturity": snap["maturity"],
            "pay_frequency": snap["pay_frequency"],
            "day_count": snap["day_count"],
            "amt_outstanding_usd": snap["amt_outstanding_usd"],
            "demo": True,
        }
        if "cpn_freq_raw" in snap:
            out_demo["cpn_freq_raw"] = snap["cpn_freq_raw"]
        if "day_cnt_des_raw" in snap:
            out_demo["day_cnt_des_raw"] = snap["day_cnt_des_raw"]
        return out_demo

    @classmethod
    def from_settings(cls) -> BondReferenceService:
        if settings.demo_mode:
            return cls(use_demo=True)
        return cls(use_demo=False)
