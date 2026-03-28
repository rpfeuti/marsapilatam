"""
Deal Information service — browse deal types and inspect deal schemas.

Wraps two MARS API endpoints:
  GET /marswebapi/v1/dealType    — list all supported deal type strings
  GET /marswebapi/v1/dealSchema  — retrieve full parameter schema for a deal type
"""

from __future__ import annotations

import logging
from typing import Any

from bloomberg.exceptions import MarsApiError
from bloomberg.webapi import MarsClient
from configs.settings import settings

log = logging.getLogger(__name__)

# Deal types that return S_FAILURE from dealSchema ("not supported in MARSAPI (new)").
_LEGACY_DEAL_TYPES: set[str] = {
    "AC", "CAP", "CS", "EQ.BF", "EQ.BFS", "EQ.BW", "EQ.CL", "EQ.CP",
    "EQ.CR", "EQ.CRS", "EQ.CS", "EQ.CUSTOM", "EQ.DS", "EQ.PP", "EQ.PPS",
    "EQ.RR", "EQ.SD", "EQ.SF", "EQ.SN", "FLFL", "FLR", "FXFL", "FXFX",
    "LOIS", "OIS", "OV", "RC", "TICKER", "XA.EQ.PBAN", "XA.FX.ASIAN",
    "XA.FX.KIKOS", "XA.FX.KOKINS", "XA.FX.RRF", "XA.FXEXFWD",
    "XA.FXKIFWD", "XA.FXKIKOFWD", "XA.FXVASTR", "XA.IR.CMSSTR",
    "XA.IR.LZC", "XA.STRNOTE", "ZERO",
}

# Hardcoded subset shown when running in demo mode (no live credentials).
_DEMO_DEAL_TYPES: list[tuple[str, str]] = [
    ("CR.CDS", "CDS singlename standard contract"),
    ("CR.CDSI", "CDS index"),
    ("EQ.VA", "OVME Vanilla Option style"),
    ("FX.FWD", "Forward"),
    ("FX.VA", "Vanilla"),
    ("IR.FLFL", "Basis Swap"),
    ("IR.FRA", "FRA"),
    ("IR.FXFL", "Fixed Float Swap"),
    ("IR.NDS", "Non-Deliverable XCCY Fixed Float Swap"),
    ("IR.OIS", "Overnight Index Swap"),
    ("IR.OIS.RFR", "Fixed vs RFR"),
    ("IR.OIS.SOFR", "Fixed vs SOFR"),
    ("IR.OV", "Swaption"),
    ("IR.ZERO", "Zero Coupon Swap"),
]


class DealInfoService:
    """Thin wrapper around MarsClient for deal-type and deal-schema queries."""

    def __init__(self, client: MarsClient | None = None) -> None:
        self._client = client

    def fetch_deal_types(self) -> list[tuple[str, str]]:
        """Return a sorted list of ``(code, description)`` tuples for every
        deal type supported by the MARS API.

        The API returns entries like ``"IR.OIS:Overnight Index Swap"``.
        Falls back to ``_DEMO_DEAL_TYPES`` in demo mode.
        """
        if self._client is None:
            return list(_DEMO_DEAL_TYPES)
        try:
            resp = self._client.send(
                "GET", "/marswebapi/v1/dealType", {"voidName": ""},
            )
            raw: list[str] = (
                resp.get("getDealTypesResponse", {}).get("dealType", [])
                or resp.get("dealType", [])
            )
            pairs: list[tuple[str, str]] = []
            for entry in raw:
                if ":" in entry:
                    code, desc = entry.split(":", 1)
                    pairs.append((code.strip(), desc.strip()))
                else:
                    pairs.append((entry.strip(), ""))
            pairs = [(c, d) for c, d in pairs if c not in _LEGACY_DEAL_TYPES]
            return sorted(pairs) or list(_DEMO_DEAL_TYPES)
        except Exception as exc:
            log.warning("Failed to fetch deal types: %s", exc)
            return list(_DEMO_DEAL_TYPES)

    def fetch_deal_schema(self, deal_type: str) -> dict[str, Any]:
        """Return the full ``schemaResponse`` dict for *deal_type*.

        The returned dict always contains ``dealStructure`` (possibly empty)
        and ``returnStatus``.  The caller should check ``returnStatus.status``
        for ``"S_FAILURE"`` to detect unsupported deal types.
        """
        if self._client is None:
            return {}
        resp = self._client.send(
            "GET", "/marswebapi/v1/dealSchema", {"tail": deal_type},
        )
        return resp.get("schemaResponse", {})

    @classmethod
    def from_settings(cls) -> DealInfoService:
        if settings.demo_mode:
            return cls(client=None)
        return cls(client=MarsClient(settings))
