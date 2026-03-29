"""
SOFR Curve Bootstrap Service.

Architecture:
    PeriodInfo         — one accrual period from MARS AccrualSchedule (dates + year fraction)
    TenorSchedule      — full fixed-leg payment schedule for one OIS tenor
    BootstrapPoint     — single result row: par rate + bootstrapped P(0,T) + zero rate
    BootstrapResult    — complete bootstrap output
    BootstrapService   — orchestrator: async MARS schedule fetching + pure Python bootstrap

The bootstrap uses MARS swap structuring purely as a **calendar engine**: we structure a
temporary SOFR OIS deal at each tenor and extract the AccrualSchedule from the fixed leg of
the structuring response.  No pricing call is made and Bloomberg's S490 curve is never read
during the bootstrap.  The par rates come entirely from the user (or live BLPAPI).

Live par rate source:
    YCSW0490 Index   → INDX_MEMBERS → 32 USOSFR BGN Curncy tickers (the S490 input set)
    SOFRRATE Index   → 1D overnight fixing (prepended as anchor)
    PX_LAST          → par rate in % p.a. (already in % — no scaling needed)

The zero rates are expressed in the same convention Bloomberg uses for S490:
  continuous compounding, ACT/365
  z = −ln(P(0,T)) × 365 / days_to_maturity

Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is provided
to do so, subject to the following conditions:  The above copyright notice and
this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from bloomberg.exceptions import MarsApiError, StructuringError
from bloomberg.webapi import MarsClient
from configs.settings import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ticker map, tenor list, and default par rates
# ---------------------------------------------------------------------------

# Confirmed against live Bloomberg terminal (2026-03-29).
# Source: YCSW0490 Index → INDX_MEMBERS (32 entries) + SOFRRATE Index for 1D.
#
# Three USOSFR BGN ticker series:
#   Weeks  : USOSFR{n}Z BGN Curncy   (Z encodes weeks, not years)
#   Months : USOSFR{A–K} BGN Curncy  (A=1M, B=2M, …, K=11M; 1F=18M)
#   1Y–9Y  : USOSFR{n} BGN Curncy
#   10Y+   : USOSFR{n} BGN Curncy    (no Z suffix for long-end)
_SOFR_OIS_TICKERS: dict[str, str] = {
    "1D":  "SOFRRATE Index",
    "1W":  "USOSFR1Z BGN Curncy",
    "2W":  "USOSFR2Z BGN Curncy",
    "3W":  "USOSFR3Z BGN Curncy",
    "1M":  "USOSFRA BGN Curncy",
    "2M":  "USOSFRB BGN Curncy",
    "3M":  "USOSFRC BGN Curncy",
    "4M":  "USOSFRD BGN Curncy",
    "5M":  "USOSFRE BGN Curncy",
    "6M":  "USOSFRF BGN Curncy",
    "7M":  "USOSFRG BGN Curncy",
    "8M":  "USOSFRH BGN Curncy",
    "9M":  "USOSFRI BGN Curncy",
    "10M": "USOSFRJ BGN Curncy",
    "11M": "USOSFRK BGN Curncy",
    "1Y":  "USOSFR1 BGN Curncy",
    "18M": "USOSFR1F BGN Curncy",
    "2Y":  "USOSFR2 BGN Curncy",
    "3Y":  "USOSFR3 BGN Curncy",
    "4Y":  "USOSFR4 BGN Curncy",
    "5Y":  "USOSFR5 BGN Curncy",
    "6Y":  "USOSFR6 BGN Curncy",
    "7Y":  "USOSFR7 BGN Curncy",
    "8Y":  "USOSFR8 BGN Curncy",
    "9Y":  "USOSFR9 BGN Curncy",
    "10Y": "USOSFR10 BGN Curncy",
    "12Y": "USOSFR12 BGN Curncy",
    "15Y": "USOSFR15 BGN Curncy",
    "20Y": "USOSFR20 BGN Curncy",
    "25Y": "USOSFR25 BGN Curncy",
    "30Y": "USOSFR30 BGN Curncy",
    "40Y": "USOSFR40 BGN Curncy",
    "50Y": "USOSFR50 BGN Curncy",
}

# Ordered tenor list — same sequence as YCSW0490 plus overnight anchor.
SOFR_TENORS: list[str] = list(_SOFR_OIS_TICKERS.keys())

# Live market snapshot (2026-03-27) used as demo fallback and editor defaults.
# Source: YCSW0490 INDX_MEMBERS bdh PX_LAST 2026-03-27 + SOFRRATE Index (1D from prior day).
SOFR_DEFAULT_PAR_RATES: dict[str, float] = {
    "1D":  3.6500,
    "1W":  3.6694,
    "2W":  3.6645,
    "3W":  3.6660,
    "1M":  3.6635,
    "2M":  3.6740,
    "3M":  3.6873,
    "4M":  3.6970,
    "5M":  3.7070,
    "6M":  3.7180,
    "7M":  3.7317,
    "8M":  3.7456,
    "9M":  3.7580,
    "10M": 3.7688,
    "11M": 3.7773,
    "1Y":  3.7868,
    "18M": 3.7641,
    "2Y":  3.7266,
    "3Y":  3.6823,
    "4Y":  3.6895,
    "5Y":  3.7260,
    "6Y":  3.7718,
    "7Y":  3.8185,
    "8Y":  3.8627,
    "9Y":  3.9060,
    "10Y": 3.9488,
    "12Y": 4.0308,
    "15Y": 4.1319,
    "20Y": 4.2055,
    "25Y": 4.1960,
    "30Y": 4.1503,
    "40Y": 4.0330,
    "50Y": 3.9070,
}

# BLPAPI curve index that lists the 32 SOFR OIS swap constituents.
_SOFR_CURVE_INDEX = "YCSW0490 Index"
_SOFR_OVERNIGHT   = "SOFRRATE Index"

# Regex to extract tenor label from Bloomberg NAME, e.g.:
#   "USD OIS  ANN VS SOFR 18M" → "18M"
#   "USD OIS  ANN VS SOFR 10Y" → "10Y"
_TENOR_RE = re.compile(r'SOFR\s+(\d+[WMYD])', re.IGNORECASE)

# Tenors where the fixed leg has a single At-Maturity payment.
# Applies to all sub-1Y instruments (overnight, weeks, months 1–11).
_SUB_ANNUAL: set[str] = {
    "1D",
    "1W", "2W", "3W",
    "1M", "2M", "3M", "4M", "5M", "6M", "7M", "8M", "9M", "10M", "11M",
}


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PeriodInfo:
    """One accrual period from the MARS fixed-leg AccrualSchedule."""

    accrual_start: date
    accrual_end:   date
    payment_date:  date
    day_count:     int    # (accrual_end - accrual_start).days — raw ACT count
    year_fraction: float  # day_count / 360  (ACT/360 — SOFR OIS convention)


@dataclass(frozen=True)
class TenorSchedule:
    """Fixed-leg payment schedule for one OIS tenor, sourced from MARS structuring."""

    tenor:          str
    effective_date: date
    maturity_date:  date       # last AccrualEndDate (before business-day adjustment)
    periods:        tuple[PeriodInfo, ...]


@dataclass(frozen=True)
class BootstrapPoint:
    """One point on the bootstrapped zero curve."""

    tenor:             str
    maturity_date:     date    # last payment date (business-day adjusted)
    days_to_maturity:  int     # from valuation_date to maturity_date
    par_rate_pct:      float   # user-provided par rate in %
    discount_factor:   float   # P(0,T)  from bootstrap
    zero_rate_pct:     float   # continuous ACT/365 zero rate in %


@dataclass
class BootstrapResult:
    """Complete bootstrapped zero curve."""

    valuation_date: date
    points:         list[BootstrapPoint] = field(default_factory=list)
    error:          str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _parse_mars_date(raw: str) -> date:
    """Parse a MARS dateVal string like '2027-03-31+00:00' into a date."""
    return date.fromisoformat(raw[:10])


def _add_tenor(base: date, tenor: str) -> date:
    """Return base + tenor.  Supports 1D, 1W/2W/3W, 1M–18M, 1Y–50Y."""
    tenor = tenor.upper().strip()
    if tenor.endswith("D"):
        return base + timedelta(days=int(tenor[:-1]))
    if tenor.endswith("W"):
        return base + timedelta(days=7 * int(tenor[:-1]))
    if tenor.endswith("M"):
        months = int(tenor[:-1])
        year  = base.year + (base.month - 1 + months) // 12
        month = (base.month - 1 + months) % 12 + 1
        day   = min(base.day, _days_in_month(year, month))
        return date(year, month, day)
    if tenor.endswith("Y"):
        years = int(tenor[:-1])
        year  = base.year + years
        day   = min(base.day, _days_in_month(year, base.month))
        return date(year, base.month, day)
    raise ValueError(f"Unsupported tenor format: {tenor!r}")


def _days_in_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]


def _add_business_days(base: date, n: int) -> date:
    """Add *n* business days to *base*, skipping weekends."""
    d = base
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


# ---------------------------------------------------------------------------
# Accrual schedule parser (from MARS structuring response)
# ---------------------------------------------------------------------------


def _parse_accrual_schedule(
    tenor:          str,
    effective_date: date,
    table_val:      dict[str, Any],
) -> TenorSchedule:
    """
    Extract PeriodInfo list from the AccrualSchedule tableVal in MARS structuring response.

    MARS format:
      tableVal.axes[0].value.dateArrayVal  →  list of AccrualStartDates
      tableVal.tableData[i].data           →  [AccrualEndDate, PaymentDate, ...]
    """
    start_date_strs: list[str] = table_val["axes"][0]["value"]["dateArrayVal"]
    table_data: list[dict] = table_val["tableData"]

    periods: list[PeriodInfo] = []
    for i, entry in enumerate(table_data):
        data_map: dict[str, Any] = {}
        for item in entry["data"]:
            data_map[item["name"]] = item["value"]

        accrual_start = _parse_mars_date(start_date_strs[i])
        accrual_end   = _parse_mars_date(data_map["AccrualEndDate"]["dateVal"])
        payment_date  = _parse_mars_date(data_map["PaymentDate"]["dateVal"])
        day_count     = (accrual_end - accrual_start).days
        year_fraction = day_count / 360.0

        periods.append(PeriodInfo(
            accrual_start=accrual_start,
            accrual_end=accrual_end,
            payment_date=payment_date,
            day_count=day_count,
            year_fraction=year_fraction,
        ))

    maturity_date = periods[-1].accrual_end if periods else effective_date
    return TenorSchedule(
        tenor=tenor,
        effective_date=effective_date,
        maturity_date=maturity_date,
        periods=tuple(periods),
    )


# ---------------------------------------------------------------------------
# MARS structuring body builder
# ---------------------------------------------------------------------------


def _build_structure_body(
    tenor:          str,
    trade_date:     date,
    session_id:     str,
) -> dict[str, Any]:
    """Build the dealStructureOverride body for a temporary SOFR OIS at a given tenor.

    SOFR OIS swaps settle T+2 from the trade date.  The effective date passed to
    MARS is the settlement date, and the maturity is computed from settlement.
    Bloomberg uses Annual pay frequency for ALL tenors (including sub-1Y).
    SettlementLag=2 Business Days matches Bloomberg's S490 convention where
    payment_date = accrual_end + 2 BD (confirmed from Swap Manager screenshots).
    """
    settle_date   = _add_business_days(trade_date, 2)
    maturity_date = _add_tenor(settle_date, tenor)

    leg_common: list[dict[str, Any]] = [
        {"name": "Notional",           "value": {"doubleVal": 1_000_000}},
        {"name": "Currency",           "value": {"stringVal": "USD"}},
        {"name": "EffectiveDate",      "value": {"dateVal": str(settle_date)}},
        {"name": "MaturityDate",       "value": {"dateVal": str(maturity_date)}},
        {"name": "PayFrequency",       "value": {"selectionVal": {"value": "Annual"}}},
        {"name": "DayCount",           "value": {"selectionVal": {"value": "ACT/360"}}},
        {"name": "SettlementLag",      "value": {"intVal": 2}},
        {"name": "SettlementLagType",  "value": {"selectionVal": {"value": "Business Days"}}},
    ]

    return {
        "sessionId": session_id,
        "tail": "IR.OIS.SOFR",
        "dealStructureOverride": {
            "param": [],
            "leg": [
                {"param": [
                    {"name": "Direction",  "value": {"selectionVal": {"value": "Pay"}}},
                    {"name": "FixedRate",  "value": {"doubleVal": 4.0}},   # arbitrary — only schedule matters
                    *leg_common,
                ]},
                {"param": [
                    {"name": "Direction",     "value": {"selectionVal": {"value": "Receive"}}},
                    {"name": "FloatingIndex", "value": {"stringVal": "SOFRRATE"}},
                    *leg_common,
                ]},
            ],
        },
    }



# ---------------------------------------------------------------------------
# Pure bootstrap algorithm
# ---------------------------------------------------------------------------


def _interp_df(known: dict[date, float], target: date) -> float:
    """
    Return discount factor at *target* via log-linear interpolation / extrapolation
    from the set of already-computed discount factors in *known*.

    Log-linear interpolation preserves the log-linear structure of discount curves
    and is equivalent to piecewise-constant forward rates.
    """
    if target in known:
        return known[target]

    sorted_dates = sorted(known)
    before = [d for d in sorted_dates if d <= target]
    after  = [d for d in sorted_dates if d > target]

    if not before:
        return known[after[0]]

    if not after:
        # Flat-forward extrapolation from the last two known points
        if len(before) >= 2:
            d1, d2 = before[-2], before[-1]
            p1, p2 = known[d1], known[d2]
            span   = (d2 - d1).days
            gap    = (target - d1).days
            if span > 0 and p1 > 0 and p2 > 0:
                return p1 * math.exp(math.log(p2 / p1) * gap / span)
        return known[before[-1]]

    d1, d2 = before[-1], after[0]
    p1, p2 = known[d1], known[d2]
    span   = (d2 - d1).days
    gap    = (target - d1).days
    if span > 0 and p1 > 0 and p2 > 0:
        return p1 * math.exp(math.log(p2 / p1) * gap / span)
    return p1


def bootstrap_zero_curve(
    par_rates_pct: dict[str, float],
    schedules:     dict[str, TenorSchedule],
    valuation_date: date,
) -> BootstrapResult:
    """
    Bootstrap zero rates from user-provided par rates and MARS-sourced schedules.

    SOFR OIS swaps settle T+2 from the trade (valuation) date.  The schedules
    contain accrual periods starting at settle_date, not valuation_date.  To
    produce discount factors and zero rates measured from valuation_date (matching
    Bloomberg S490), we bridge the T+2 gap with a pre-spot discount factor
    computed from the overnight SOFRRATE.

    Bloomberg's SOFR OIS convention has a 2-business-day payment delay on both
    legs (Pay Delay: 2 BD), so cashflows occur at payment_date = accrual_end + 2BD.
    All discount factors are anchored at payment_date, matching S490 pillar placement.

    Algorithm (with T+2 settlement, trade date = 0, settle date = T₀):
      P(0, T₀) = P_settle = 1 / (1 + r_ON × gap_days/360)
      P(0, T₁) = P_settle / (1 + c₁ × τ₁)          [pillars at accrual_end]
      P(0, Tₙ) = (P_settle − cₙ × Σᵢ<ₙ P(0,Tᵢ)×τᵢ) / (1 + cₙ × τₙ)

    The 1D overnight rate is NOT bootstrapped as a swap.  It is added as a
    post-processing step via step-forward interpolation from the built curve
    (between settle and the 1W pillar), matching Bloomberg's S490 methodology
    where the 1D node inherits the constant forward of the first swap segment.

    Zero rates follow Bloomberg's S490 convention:
      continuous compounding, ACT/365, measured from valuation_date
      z = −ln(P(0,T)) × 365 / (T − valuation_date).days × 100  [in %]
    """
    # Exclude 1D from swap bootstrap — it is handled as a post-processing step.
    active_tenors = [t for t in par_rates_pct if t in schedules and t != "1D"]
    active_tenors.sort(key=lambda t: schedules[t].periods[-1].accrual_end)

    # Derive the settlement date from the actual first accrual start in the schedules.
    settle_date = min(
        s.periods[0].accrual_start for s in schedules.values() if s.periods
    )
    settle_gap  = (settle_date - valuation_date).days

    # Bridge the T+2 gap using the overnight SOFR rate (simple interest, ACT/360).
    overnight_rate = par_rates_pct.get("1D", 0.0) / 100.0
    if settle_gap > 0 and overnight_rate > 0:
        p_settle = 1.0 / (1.0 + overnight_rate * settle_gap / 360.0)
    else:
        p_settle = 1.0

    known_dfs: dict[date, float] = {valuation_date: 1.0, settle_date: p_settle}
    points: list[BootstrapPoint] = []

    for tenor in active_tenors:
        schedule  = schedules[tenor]
        par_rate  = par_rates_pct[tenor] / 100.0
        periods   = schedule.periods

        if len(periods) == 0:
            log.warning("Empty schedule for tenor %s — skipped", tenor)
            continue

        # Single-period (sub-annual) swap:
        #   P(0, T) = P_settle / (1 + c × τ)
        if len(periods) == 1:
            tau = periods[0].year_fraction
            P_n = p_settle / (1.0 + par_rate * tau)
        else:
            # Multi-period: annuity over all but the last coupon, then solve
            #   P(0, Tₙ) = (P_settle − c × Σ P(0,Tᵢ)τᵢ) / (1 + c × τₙ)
            annuity = sum(
                _interp_df(known_dfs, p.accrual_end) * p.year_fraction
                for p in periods[:-1]
            )
            tau_n = periods[-1].year_fraction
            P_n   = (p_settle - par_rate * annuity) / (1.0 + par_rate * tau_n)

        last_accrual = periods[-1].accrual_end
        known_dfs[last_accrual] = P_n

        # Zero rate: ACT/365 continuously compounded from valuation_date.
        days_from_val = (last_accrual - valuation_date).days
        if days_from_val <= 0 or P_n <= 0:
            log.warning("Invalid bootstrap result for tenor %s: P=%s days=%s", tenor, P_n, days_from_val)
            continue

        zero_rate_pct = -math.log(P_n) * 365.0 / days_from_val * 100.0

        points.append(BootstrapPoint(
            tenor=tenor,
            maturity_date=last_accrual,
            days_to_maturity=days_from_val,
            par_rate_pct=par_rates_pct[tenor],
            discount_factor=P_n,
            zero_rate_pct=zero_rate_pct,
        ))

    # 1D post-processing: step-forward interpolation from the built curve.
    # The 1D maturity (accrual_end of the 1D schedule) falls inside the first
    # swap segment [settle, 1W_accrual_end].  Under step-forward, the CC forward
    # is constant across this segment, so the 1D zero rate inherits the 1W
    # implied forward — matching Bloomberg's S490 methodology.
    if "1D" in schedules and "1D" in par_rates_pct and len(known_dfs) > 2:
        sched_1d   = schedules["1D"]
        maturity_1d = sched_1d.periods[-1].accrual_end
        days_1d     = (maturity_1d - valuation_date).days
        if days_1d > 0:
            p_1d = _interp_df(known_dfs, maturity_1d)
            if p_1d > 0:
                z_1d = -math.log(p_1d) * 365.0 / days_1d * 100.0
                points.insert(0, BootstrapPoint(
                    tenor="1D",
                    maturity_date=maturity_1d,
                    days_to_maturity=days_1d,
                    par_rate_pct=par_rates_pct["1D"],
                    discount_factor=p_1d,
                    zero_rate_pct=z_1d,
                ))

    return BootstrapResult(valuation_date=valuation_date, points=points)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class BootstrapService:
    """
    Orchestrates SOFR curve bootstrapping.

    Live mode:
      - Structures a temporary IR.OIS.SOFR deal per tenor via MARS async API
        to obtain the exact fixed-leg AccrualSchedule (payment dates + year fractions).
      - All structuring calls run concurrently via asyncio.gather.
      - Calls bootstrap_zero_curve() with user par rates + MARS-sourced schedules.

    Demo mode:
      - Loads pre-saved schedules from demo_data/sofr_schedules.json (no API calls).
      - Bootstrap uses the same algorithm as live mode.
    """

    def __init__(self, client: MarsClient | None = None) -> None:
        self._client = client

    # ------------------------------------------------------------------ live

    async def fetch_schedules_async(
        self,
        tenors:         list[str],
        effective_date: date,
    ) -> dict[str, TenorSchedule]:
        """
        Concurrently structure one SOFR OIS deal per tenor and return a
        mapping of tenor → TenorSchedule extracted from the fixed-leg
        AccrualSchedule in the MARS structuring response.
        """
        if self._client is None:
            raise RuntimeError("No MarsClient available — use demo mode")

        session_id = self._client.session_id  # ensure session started (sync, before async)

        async def _fetch_one(tenor: str) -> tuple[str, TenorSchedule]:
            body = _build_structure_body(tenor, effective_date, session_id)
            try:
                resp = await self._client.send_async(  # type: ignore[union-attr]
                    "POST", "/marswebapi/v1/deals/temporary", body
                )
            except MarsApiError as exc:
                raise StructuringError(f"Failed to structure {tenor} OIS: {exc}") from exc

            try:
                leg0_params: list[dict] = (
                    resp["results"][0]["structureResponse"]["dealStructure"]["leg"][0]["param"]
                )
            except (KeyError, IndexError) as exc:
                raise StructuringError(
                    f"Unexpected structure response for {tenor}: {resp}"
                ) from exc

            for param in leg0_params:
                if param["name"] == "AccrualSchedule":
                    schedule = _parse_accrual_schedule(
                        tenor, effective_date, param["value"]["tableVal"]
                    )
                    return tenor, schedule

            raise StructuringError(f"AccrualSchedule not found in MARS response for {tenor}")

        tasks   = [_fetch_one(t) for t in tenors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        schedules: dict[str, TenorSchedule] = {}
        for item in results:
            if isinstance(item, Exception):
                log.error("Schedule fetch failed: %s", item)
                raise item
            tenor, schedule = item
            schedules[tenor] = schedule

        return schedules

    # ------------------------------------------------------------------ demo

    def build_demo_schedules(
        self,
        tenors:         list[str],
        valuation_date: date,
    ) -> dict[str, TenorSchedule]:
        """Load pre-saved SOFR OIS schedules from demo_data/sofr_schedules.json."""
        import json
        from pathlib import Path

        path = Path(__file__).parent.parent / "demo_data" / "sofr_schedules.json"
        raw  = json.loads(path.read_text())["schedules"]

        result: dict[str, TenorSchedule] = {}
        for tenor in tenors:
            rows = raw.get(tenor, [])
            if not rows:
                continue
            periods = tuple(
                PeriodInfo(
                    accrual_start=date.fromisoformat(r["accrual_start"]),
                    accrual_end=date.fromisoformat(r["accrual_end"]),
                    payment_date=date.fromisoformat(r["payment_date"]),
                    day_count=r["day_count"],
                    year_fraction=r["year_fraction"],
                )
                for r in rows
            )
            result[tenor] = TenorSchedule(
                tenor=tenor,
                effective_date=periods[0].accrual_start,
                maturity_date=periods[-1].accrual_end,
                periods=periods,
            )
        return result

    # ------------------------------------------------------------------ bootstrap

    def bootstrap(
        self,
        par_rates_pct:  dict[str, float],
        schedules:      dict[str, TenorSchedule],
        valuation_date: date,
    ) -> BootstrapResult:
        """Run the bootstrap algorithm. Pure Python — no API calls."""
        try:
            return bootstrap_zero_curve(par_rates_pct, schedules, valuation_date)
        except Exception as exc:
            log.exception("Bootstrap failed")
            return BootstrapResult(valuation_date=valuation_date, error=str(exc))

    # ------------------------------------------------------------------ par rates

    def get_sofr_par_rates(self, as_of_date: date | None = None) -> dict[str, float]:
        """Fetch SOFR OIS par rates from Bloomberg via BLPAPI.

        When *as_of_date* is today or None, a live ``bdp`` request is used.
        When *as_of_date* is a past date, a historical ``bdh`` request is used
        so that the par rates match the requested valuation date.

        Algorithm:
          1. bds("YCSW0490 Index", "INDX_MEMBERS") → 32 USOSFR BGN Curncy tickers
          2. Prepend SOFRRATE Index as the 1D anchor
          3. bdp(tickers, ["NAME"]) → parse tenor labels (always current — stable)
          4. bdp or bdh(tickers, ["PX_LAST"]) → rates in % p.a. for the correct date
          5. Parse tenor from NAME via regex (e.g. "SOFR 18M" → "18M")

        Falls back to SOFR_DEFAULT_PAR_RATES on any error or in demo mode.
        """
        if settings.demo_mode:
            return dict(SOFR_DEFAULT_PAR_RATES)
        try:
            from bloomberg.blpapi_client import BlpapiClient
            today     = date.today()
            hist_date = as_of_date if (as_of_date is not None and as_of_date < today) else None

            with BlpapiClient() as client:
                members = client.bds(_SOFR_CURVE_INDEX, "INDX_MEMBERS")
                chain_tickers = [
                    row["Member Ticker and Exchange Code"]
                    for row in members
                    if "Member Ticker and Exchange Code" in row
                ]
                all_tickers = [_SOFR_OVERNIGHT] + chain_tickers

                # Names are static — always fetch current for tenor label parsing.
                name_raw = client.bdp(all_tickers, ["NAME"])

                # Prices — live or historical depending on valuation date.
                if hist_date is not None:
                    log.debug("Fetching historical SOFR par rates for %s", hist_date)
                    price_raw = client.bdh(all_tickers, ["PX_LAST"], hist_date)
                else:
                    price_raw = client.bdp(all_tickers, ["PX_LAST"])

            # Merge name + price into the same {ticker: {field: value}} shape.
            raw: dict[str, dict] = {
                t: {**name_raw.get(t, {}), **price_raw.get(t, {})}
                for t in all_tickers
            }

            result: dict[str, float] = {}
            # 1D anchor
            overnight_px = raw.get(_SOFR_OVERNIGHT, {}).get("PX_LAST")
            if overnight_px is not None:
                result["1D"] = float(overnight_px)
            # OIS swaps — parse tenor from NAME field
            for ticker in chain_tickers:
                data = raw.get(ticker, {})
                px   = data.get("PX_LAST")
                name = str(data.get("NAME", ""))
                if px is None:
                    continue
                m = _TENOR_RE.search(name)
                if m:
                    result[m.group(1).upper()] = float(px)
                else:
                    log.warning("Could not parse tenor from NAME %r for %s", name, ticker)

            if not result:
                return dict(SOFR_DEFAULT_PAR_RATES)
            return result
        except Exception:
            log.warning(
                "Failed to fetch SOFR par rates for %s; using snapshot defaults",
                as_of_date, exc_info=True,
            )
            return dict(SOFR_DEFAULT_PAR_RATES)

    # ------------------------------------------------------------------ factory

    @classmethod
    def from_settings(cls) -> BootstrapService:
        """Factory: returns a live-backed or demo-backed service based on settings."""
        if settings.demo_mode:
            return cls(client=None)
        return cls(client=MarsClient(settings))
