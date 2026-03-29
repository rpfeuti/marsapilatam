# MARS API LatAm — Bloomberg MARS Derivatives & Curves Explorer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://marsapilatam.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source Python/Streamlit application built on top of the **Bloomberg MARS (Multi-Asset Risk System) API**. It lets you explore, visualize, and price interest rate curves, IR swaps, cross-currency swaps, FX derivatives, and portfolios across LatAm and global markets — directly from the Bloomberg enterprise API, with no Excel required.

> **Try the live demo** → [marsapilatam.streamlit.app](https://marsapilatam.streamlit.app)
> No Bloomberg subscription needed for the demo. Connect your own credentials to unlock 248+ curves and live pricing.

---

## Contents

- [Features](#features)
- [Demo Mode](#demo-mode)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Layer Architecture](#layer-architecture)
- [Pages](#pages)
- [Services](#services)
- [Bloomberg Clients](#bloomberg-clients)
- [Configs](#configs)
- [Demo Data](#demo-data)
- [Scripts](#scripts)
- [Deployment — Streamlit Cloud](#deployment--streamlit-cloud)
- [Bloomberg MARS API](#bloomberg-mars-api)
- [Dependencies](#dependencies)
- [License](#license)

---

## Features

| Feature | Details |
|---|---|
| **248 rate curves** | All Bloomberg XMarket curves: OIS, IBOR, Cross-Currency Basis, Treasury, Sovereign, Sector/Issuer, CSA, UFR |
| **Curve types** | Raw (par rates), Zero Coupon, Discount Factor with custom date grids |
| **IR Swap pricing** | OIS and XCCY/NDS structuring, pricing, and par-rate solving |
| **FX Derivatives** | Vanilla, Risk Reversal, Knock-In, Knock-Out barrier options |
| **Portfolio pricing** | Multi-deal MTM portfolio with DV01 and PV01 roll-up |
| **Key Rate Risk (KRR)** | Bucket DV01 ladders for single securities and portfolios |
| **Stress testing** | Parallel shift and SHOC scenario analysis via MARS |
| **SOFR Bootstrap** | Independent SOFR zero curve from par rates + MARS schedules |
| **Deal Information** | Browse all MARS deal types and their full schema parameters |
| **Async pricing** | Concurrent swap pricing across multiple tenors and currencies |
| **Multilingual UI** | English, Portuguese (BR), Spanish |
| **Demo mode** | Fully offline — all features work with pre-saved 2026-03-27 snapshots |

---

## Demo Mode

When no Bloomberg credentials are configured the app automatically enters **demo mode**. All features are available using pre-saved real market data snapshotted on **2026-03-27**.

### Demo curves (7)

| Curve ID | Profile | Country | Description |
|---|---|---|---|
| S329 | COP.OIS | Colombia | Colombia IBR OIS |
| S490 | USD.SOFR | United States | USD SOFR OIS |
| S89 | BRL.BM&F | Brazil | Brazil Pre × DI (B3) |
| S583 | MXN.OIS.TIIE | Mexico | Mexico TIIE OIS |
| S193 | CLP.6m | Chile | Chile CLP 6-month |
| S514 | EUR.OIS.ESTR | Europe | EUR €STR OIS |
| S374 | PEN.OIS | Peru | Peru PEN OIS |

### Demo swap snapshots (12)

| Key | Type | Description |
|---|---|---|
| COP | OIS | Colombia IBR/OIS — COP 5Y |
| USD | OIS | USD SOFR OIS — 5Y |
| BRL | OIS | Brazil CDI Pre×DI — 5Y |
| MXN | OIS | Mexico TIIE OIS — 5Y |
| CLP | OIS | Chile OIS — 5Y |
| EUR | OIS | EUR €STR OIS — 5Y |
| USDCOP | XCCY/NDS | USD/COP Non-Deliverable Swap — 5Y |
| USDBRL | XCCY/NDS | USD/BRL NDS — 5Y |
| USDMXN | XCCY/NDS | USD/MXN NDS — 5Y |
| USDCLP | XCCY/NDS | USD/CLP NDS — 5Y |
| USDPEN | XCCY/NDS | USD/PEN NDS — 5Y |
| USDEUR | XCCY/NDS | USD/EUR NDS — 5Y |

### Demo FX derivative snapshots (24)

Four product types × six currency pairs: EUR/USD, USD/COP, USD/MXN, USD/PEN, USD/BRL, USD/CLP.
Products: Vanilla (FX.VA), Risk Reversal (FX.RR), Knock-In (FX.KI), Knock-Out (FX.KO).

### Demo FX spot rates (2026-03-27)

| Currency | Rate (per USD) |
|---|---|
| COP | 3 665.70 |
| BRL | 5.2388 |
| MXN | 18.1188 |
| PEN | 3.4860 |
| CLP | 922.94 |
| EUR | 0.8689 (i.e. EURUSD ≈ 1.1508) |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/rpfeuti/marsapilatam.git
cd marsapilatam
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3a. Run in demo mode (no credentials needed)

```bash
streamlit run app.py
```

The app starts immediately with the pre-loaded 2026-03-27 market data.

### 3b. Run with live Bloomberg data

Create a `.env` file at the project root with your Bloomberg MARS credentials:

```env
BBG_CLIENT_ID=your_client_id
BBG_CLIENT_SECRET=your_hex_secret
BBG_UUID=your_bloomberg_uuid
```

Optionally override defaults:

```env
BBG_HOST=https://api.bloomberg.com   # default; only change for non-prod
BLPAPI_HOST=localhost                 # Bloomberg Desktop API host
BLPAPI_PORT=8194                      # Bloomberg Desktop API port
```

Then run:

```bash
streamlit run app.py
```

> **Bloomberg BLPAPI** (Desktop API) is only required for the SOFR Bootstrap page (live par rates) and FX rate fetching. All other pages use only the MARS REST API. The `blpapi` package is **not** in `requirements.txt` and is never imported on Streamlit Cloud — the app degrades gracefully to demo mode when it is absent.

---

## Project Structure

```
marsapilatam/
│
├── app.py                           # Streamlit entry point, navigation, sidebar
│
├── pages/
│   ├── home.py                      # Landing page with feature table
│   ├── curves.py                    # Rate curves explorer (Raw / Zero / Discount)
│   ├── deal_info.py                 # Deal type browser + schema explorer
│   ├── swaps.py                     # OIS and XCCY swap pricer
│   ├── fx_derivatives.py            # FX Vanilla / RR / KI / KO pricer
│   ├── portfolio.py                 # Portfolio MTM pricing
│   ├── stress_testing.py            # Parallel shift & SHOC scenario analysis
│   ├── krr.py                       # Key Rate Risk (bucket DV01)
│   └── async_swaps.py               # Concurrent multi-tenor SOFR bootstrap
│
├── bloomberg/
│   ├── webapi/
│   │   ├── mars_client.py           # MARS REST client: JWT auth, sessions, async
│   │   └── bbg_jwt.py               # HS256 JWT factory (client_id + client_secret)
│   ├── blpapi_client.py             # Bloomberg Desktop API thin wrapper (bdp/bds/bdh)
│   ├── api_models.py                # Pydantic models for all MARS request/response envelopes
│   ├── exceptions.py                # Exception hierarchy (MarsApiError, BlpapiError, …)
│   └── pricing_result.py            # Parses securitiesPricing / solve response into dicts
│
├── services/
│   ├── curves_service.py            # XMarket curve download (Repository pattern)
│   ├── swaps_service.py             # IR/XCCY swap structure + price + solve
│   ├── fx_derivatives_service.py    # FX option structure + price
│   ├── fx_service.py                # USD cross-rate fetcher (BLPAPI or demo fallback)
│   ├── portfolio_service.py         # Portfolio pricing + PnL aggregation
│   ├── risk_service.py              # Key Rate Risk (KRR) — security & portfolio
│   ├── bootstrap_service.py         # SOFR zero curve bootstrap (MARS + pure Python)
│   └── deal_info_service.py         # Deal type list + schema browser
│
├── configs/
│   ├── settings.py                  # Credentials (pydantic-settings), DEMO_DATE
│   ├── curves_config.py             # CurveType, CurveSpec, DEMO_CURVES, CSA_CURVE_IDS
│   ├── curves_catalog.py            # 248 XMarket curve entries (CURVES_BY_ID / CURVES_BY_LABEL)
│   ├── swaps_config.py              # SwapSpec, OIS_SWAP_SPECS, XCCY_SWAP_SPECS, demo manifests
│   ├── derivatives_config.py        # FxDerivativeSpec, FX_*_SPECS for 4 product types
│   ├── portfolio_config.py          # PORTFOLIO_DEALS, MARS_API_FIELDS catalog
│   ├── krr_config.py                # KRR tenor buckets, pricing fields
│   └── i18n.py                      # UI translations (EN / PT / ES), lang_selector()
│
├── demo_data/
│   ├── curves/                      # 7 × curve snapshots (raw + zero + discount)
│   ├── swaps/                       # 12 × swap pricing snapshots
│   ├── fx_derivatives/              # 24 × FX option snapshots + fx_rates.json
│   ├── bootstrap/                   # SOFR OIS accrual schedules
│   └── deal_info/
│       ├── deal_types.json          # All supported MARS deal type codes
│       └── schemas/                 # Per-deal-type dealSchema responses (14 files)
│
├── scripts/
│   ├── refresh_demo_data.py         # Master refresh script (all demo_data at once)
│   ├── download_curves_demo_data.py
│   ├── download_swap_demo_data.py
│   ├── download_fx_deriv_demo_data.py
│   ├── download_fx_rates_demo_data.py
│   └── download_deal_info_demo_data.py
│
├── docs/
│   ├── mars_api_examples.md         # Annotated MARS API request/response examples
│   └── marsapi_swagger.json         # Bloomberg MARS OpenAPI specification
│
├── .streamlit/
│   ├── config.toml                  # Server settings, dark theme
│   └── secrets.toml.example         # Template for Streamlit Cloud secrets
│
├── requirements.txt
└── .env                             # (gitignored) live credentials
```

---

## Configuration

### `configs/settings.py`

Credentials are loaded via `pydantic-settings` from environment variables or a `.env` file. All fields have safe defaults so the app starts in demo mode when credentials are absent.

| Field | Env Var | Default | Description |
|---|---|---|---|
| `bbg_client_id` | `BBG_CLIENT_ID` | `""` | Bloomberg Enterprise Console OAuth client ID |
| `bbg_client_secret` | `BBG_CLIENT_SECRET` | `""` | Hex-encoded client secret |
| `bbg_uuid` | `BBG_UUID` | `0` | Bloomberg user UUID |
| `bbg_host` | `BBG_HOST` | `https://api.bloomberg.com` | MARS REST API base URL |
| `blpapi_host` | `BLPAPI_HOST` | `localhost` | Bloomberg Desktop API host |
| `blpapi_port` | `BLPAPI_PORT` | `8194` | Bloomberg Desktop API port |

`settings.demo_mode` is `True` when any of `bbg_client_id`, `bbg_client_secret`, or `bbg_uuid` is missing.

`DEMO_DATE = date(2026, 3, 27)` is the reference date for all demo snapshots. All date inputs in pages default to this value and are disabled in demo mode to prevent users from requesting back-dates against stale data.

---

## Layer Architecture

```
Browser (Streamlit pages)
        │
        ▼
   Service layer  ──────────────────────────────────────────┐
   (services/)                                               │
        │                                                    │
        ├─ XMarketCurveService   → MarsClient  (MARS REST)  │
        ├─ SwapPricingService    → MarsClient  (MARS REST)  │
        ├─ DerivativePricingService → MarsClient             │
        ├─ PortfolioPricingService  → MarsClient             │
        ├─ KrrService           → MarsClient                 │
        ├─ BootstrapService     → MarsClient (schedules)     │
        │                       → BlpapiClient (par rates)   │
        ├─ FxRateService        → BlpapiClient (PX_LAST)    │
        └─ DealInfoService      → MarsClient                │
                                                             │
   Bloomberg clients  (bloomberg/)                           │
        ├─ MarsClient           HTTPS + JWT → api.bloomberg.com
        └─ BlpapiClient         native SDK → localhost:8194  │
                                                             │
   Demo repositories  (demo_data/)  ◄────────── (fallback) ─┘
```

Every service uses the **Repository pattern**: a `Protocol` interface with two concrete implementations — one live (MARS or BLPAPI) and one demo (reads from `demo_data/`). Pages only depend on the service interface; they never touch credentials or the filesystem.

---

## Pages

### `pages/home.py` — Landing Page
Renders a Streamlit table listing all pages with descriptions. Uses i18n keys for all strings.

### `pages/curves.py` — Interest Rate Curves
Downloads and visualises XMarket curves via `XMarketCurveService`.

- **Curve selector**: all 248 XMarket curves in live mode; 7 demo curves in demo mode
- **Curve types**: Raw Curve (par rates at instrument maturities), Zero Coupon (bootstrapped zero rates), Discount Factor (present-value factors)
- **Side**: Mid / Bid / Ask (disabled in demo mode)
- **Interpolation method**: Piecewise Linear (Simple), Smooth Forward (Cont), Step Forward (Cont), Piecewise Linear (Cont)
- **Date grid interval**: Daily, Weekly, Monthly (for Zero and Discount curves)
- **As-of date**: locked to `DEMO_DATE` in demo mode
- Plotly chart with correct tenor-axis spacing for Raw curves; date-axis for interpolated curves
- Formatted data table below the chart

### `pages/deal_info.py` — Deal Information
Browse all Bloomberg MARS deal types and inspect the complete field schema for any deal.

- Lists all available `dealType` codes with descriptions
- Renders the full `dealSchema` response for any selected deal — all parameters, their types (`doubleVal`, `stringVal`, `selectionVal`, `dateVal`, `tableVal`), allowed selection values, and which fields are solvable targets
- Useful for building new pricing workflows without guessing field names

### `pages/swaps.py` — IR & XCCY Swap Pricer
Full swap structuring and pricing using `SwapPricingService`.

**OIS tab** — Single-currency OIS swaps:
- Supported: COP OIS, USD SOFR, BRL CDI, MXN OIS, CLP OIS, EUR €STR
- Inputs: direction, notional, effective/maturity dates, fixed rate (optional), pay frequency, day count, solve target
- Curve overrides: forward and discount curve per leg (selectable from CURVES_BY_LABEL)
- Outputs: par rate (if solved), MktVal, DV01, PV01, MktPx, AccruedInterest

**XCCY/NDS tab** — Cross-currency non-deliverable swaps:
- Supported: USD/COP, USD/BRL, USD/MXN, USD/CLP, USD/PEN, USD/EUR
- Leg 1 in USD (SOFR); Leg 2 in local currency (OIS index)
- FX spot rate auto-populated from `FxRateService`
- Same pricing fields as OIS plus separate leg curve overrides

### `pages/fx_derivatives.py` — FX Derivatives Pricer
Prices FX options via `DerivativePricingService`.

**Vanilla (FX.VA)**: Call/Put, direction Buy/Sell, notional, strike, expiry, exercise type (European/American). Greeks: Delta, Gamma, Vega, Theta, Rho, Vanna, Volga, Phi.

**Risk Reversal (FX.RR)**: 2-leg structure with separate Call/Put strikes and directions.

**Knock-In (FX.KI)**: Down & In / Up & In barriers with American or European monitoring.

**Knock-Out (FX.KO)**: Down & Out / Up & Out barriers.

All four tabs support the same 6 currency pairs: EUR/USD, USD/COP, USD/MXN, USD/PEN, USD/BRL, USD/CLP.

Valuation and curve dates are locked to `DEMO_DATE` in demo mode.

### `pages/portfolio.py` — Portfolio Pricing
Prices a predefined multi-deal portfolio via `PortfolioPricingService`.

- Calls the MARS `portfolioPricing` endpoint
- Aggregates per-deal `MktVal`, `DV01`, `PV01` into a summary table
- Demo mode loads `demo_data/swaps/` and `demo_data/fx_derivatives/` snapshots and merges them into the same table format

### `pages/stress_testing.py` — Scenario Analysis
Tests interest rate scenarios (parallel shifts and SHOC) against a deal or portfolio.

- Builds a `scenarioRequest` with `shiftWhat`, `shiftMode`, and `shiftValue` expressions
- Displays PnL by scenario bucket

### `pages/krr.py` — Key Rate Risk
Computes bucket DV01 ladders for single securities or portfolios via `KrrService`.

- Single security: `POST /marswebapi/v1/securitiesKrr`
- Portfolio: `POST /enterprise/mars/portfolioKrr`
- Displays a tenor-bucketed DV01 bar chart and data table

### `pages/async_swaps.py` — SOFR Bootstrap (Async)
Bootstraps the SOFR zero curve from par rates using MARS as a calendar engine.

- Reads SOFR OIS par rates from BLPAPI (`YCSW0490 Index` constituents + `SOFRRATE Index`) — or uses `SOFR_DEFAULT_PAR_RATES` in demo mode
- Concurrently structures one temporary `IR.OIS.SOFR` deal per tenor via `BootstrapService.fetch_schedules_async()` to extract the `AccrualSchedule`
- Runs pure Python bootstrap: iteratively solves `P(0,T)` from par rates and accrual year fractions
- Displays: par rate input grid (editable), bootstrapped discount factors, zero rates (continuous, ACT/365), and a comparison against Bloomberg S490 SOFR curve

---

## Services

### `services/curves_service.py`
**`XMarketCurveService`** — downloads Bloomberg XMarket interest rate curves.

```
CurveQuery (frozen dataclass)
    curve_id:        str         # e.g. "S329"
    curve_type:      CurveType   # RAW | ZERO | DISCOUNT
    as_of:           date
    side:            Side        # "Mid" | "Bid" | "Ask"
    requested_dates: tuple[date, ...]  # for ZERO / DISCOUNT interpolation
    interpolation:   str         # MARS interpolation method key
```

- `XMarketRepository.fetch()` — calls `POST /marswebapi/v1/dataDownload`
- `DemoRepository.fetch()` — loads `demo_data/curves/{filename}.json`, reads the `demo_key` array (`"raw"`, `"zero"`, or `"discount"`)
- `XMarketCurveService.from_settings()` — factory that selects repository based on `settings.demo_mode`

### `services/swaps_service.py`
**`SwapPricingService`** — structures, prices, and solves IR/XCCY swaps.

```
SwapQuery (frozen dataclass)
    key:              str         # "COP", "USDCOP", etc.
    swap_type:        "OIS"|"XCCY"
    direction:        "Receive"|"Pay"
    effective_date:   date
    maturity_date:    date
    valuation_date:   date
    curve_date:       date
    notional:         float
    forward_curve:    str         # Bloomberg curve ID, e.g. "S329"
    discount_curve:   str
    float_index:      str         # Bloomberg ticker, e.g. "COOVIBR"
    pay_frequency:    str
    day_count:        str
    fixed_rate:       float|None  # None → solve for par rate
    solve_for:        str         # "Coupon" | "Spread"
    leg1_forward_curve:  str      # XCCY: USD leg projection curve
    leg1_discount_curve: str      # XCCY: USD leg discount curve
    leg2_notional:    float       # 0 = use leg1 notional
```

Live flow: `POST /marswebapi/v1/deals/temporary` → `POST /marswebapi/v1/securitiesPricing` → `POST /marswebapi/v1/securitiesPricing` (solve request). Discount curve overrides are injected via `interestRateCurveOverrides` in the pricing body.

`_DEMO_SOLVABLE` provides fallback solve-target lists when the dealSchema API is unavailable. `fetch_solvable_fields(deal_type)` fetches live targets from `GET /marswebapi/v1/dealSchema`.

### `services/fx_derivatives_service.py`
**`DerivativePricingService`** — prices FX options (no solve).

```
DerivativeQuery (frozen dataclass)
    key:              str          # "USDCOP", "EURUSD", etc.
    product_type:     str          # "FX_VANILLA"|"FX_RR"|"FX_KI"|"FX_KO"
    direction:        str          # "Buy"|"Sell"
    call_put:         str          # "Call"|"Put"
    notional:         float
    strike:           float
    expiry_date:      date
    valuation_date:   date
    curve_date:       date
    exercise_type:    str          # "European"|"American"
    # Risk Reversal
    leg2_call_put:    str
    leg2_strike:      float
    leg2_direction:   str
    # Barrier
    barrier_direction: str         # "Down & In", "Up & Out", etc.
    barrier_level:    float
    barrier_type:     str          # "American"|"European"
```

Pricing fields captured: `MktVal`, `MktPx`, `Premium`, `Delta`, `Gamma`, `Vega`, `Theta`, `Rho`, `Vol`, `DV01`, `Vanna`, `Volga`, `Phi`.

### `services/fx_service.py`
**`FxRateService`** — provides USD cross-rate spot prices.

- Live: `BlpapiClient.bdp(tickers, ["PX_LAST"])` — single batched call, cached 1 hour
- EUR is inverted: `EURUSD Curncy` → `PX_LAST` is USD/EUR, so `rate = 1 / PX_LAST`
- Demo / BLPAPI unavailable: falls back to `demo_data/fx_derivatives/fx_rates.json`, then hardcoded `_HARDCODED_RATES`
- `BlpapiClient` is imported lazily inside `from_settings()` so the module loads cleanly without the `blpapi` SDK installed

### `services/bootstrap_service.py`
**`BootstrapService`** — bootstraps the SOFR zero curve from par rates.

Uses MARS purely as a **calendar engine**: it structures temporary `IR.OIS.SOFR` deals asynchronously and reads the `AccrualSchedule` from the `dealStructure.leg[0].param[]` of each response. No MARS pricing call is made; Bloomberg's S490 curve is never read.

```
PeriodInfo  accrual_start, accrual_end, payment_date, day_count, year_fraction
TenorSchedule  tenor, effective_date, maturity_date, periods: tuple[PeriodInfo]
BootstrapPoint  tenor, maturity_date, days, par_rate, discount_factor, zero_rate
BootstrapResult  points: list[BootstrapPoint], valuation_date, error
```

**Algorithm** (pure Python):
1. For the short end (1D–1Y, single-period OIS): `P(0,T) = 1 / (1 + r × τ)`
2. For the long end (multi-period OIS): iterative bootstrap subtracting already-known discount factors
3. Zero rate: `z = −ln(P(0,T)) × 365 / days` (continuous, ACT/365 — matching Bloomberg S490)

**`SOFR_DEFAULT_PAR_RATES`** (2026-03-27 snapshot, all 33 tenors from 1D to 50Y) is used in demo mode and as a fallback when BLPAPI is unavailable.

**`get_sofr_par_rates(as_of_date)`** fetches live rates:
- `bds("YCSW0490 Index", "INDX_MEMBERS")` → 32 USOSFR BGN Curncy tickers
- Prepends `SOFRRATE Index` as the 1D overnight anchor
- Uses `bdh()` for historical dates, `bdp()` for today

**`fetch_schedules_async(tenors, effective_date)`** concurrently structures one SOFR OIS deal per tenor using `asyncio.gather`.

**`sofr_schedules.json`** (`demo_data/bootstrap/sofr_schedules.json`) snapshot covers all 33 tenors with effective date 2026-03-27 (used in demo mode to skip MARS calls entirely).

### `services/portfolio_service.py`
**`PortfolioPricingService`** — MTM-prices a multi-deal portfolio.

- Live: fetches portfolio IDs via `GET /enterprise/common/portfolio-ids`, then calls `POST /marswebapi/v1/portfolioPricing`
- Demo: walks `configs/portfolio_config.PORTFOLIO_DEALS` and merges `metrics` from the relevant `demo_data/` snapshots
- Aggregates numeric fields (`MktVal`, `DV01`, `PV01`) across deals using `NUMERIC_AGGREGATE_FIELDS`

### `services/risk_service.py`
**`KrrService`** — computes Key Rate Risk (bucket DV01 ladders).

- Security-level: `POST /marswebapi/v1/securitiesKrr`
- Portfolio-level: `POST /enterprise/mars/portfolioKrr`
- Demo: synthetic DV01 ladders from `DEMO_KRR_TENORS_*` constants in `configs/krr_config.py`

### `services/deal_info_service.py`
**`DealInfoService`** — lists deal types and fetches deal schemas.

- `list_deal_types()` → `GET /marswebapi/v1/dealType`; demo loads `demo_data/deal_info/deal_types.json`
- `get_schema(tail)` → `GET /marswebapi/v1/dealSchema`; demo loads `demo_data/deal_info/schemas/{tail}.json`
- Filters `_LEGACY_DEAL_TYPES` from the list to avoid exposing deprecated codes

---

## Bloomberg Clients

### `bloomberg/webapi/mars_client.py` — `MarsClient`
Low-level HTTPS client for the Bloomberg MARS REST API.

- **Auth**: generates a fresh HS256 JWT per request via `JwtFactory` (client_id + client_secret + uuid)
- **Sessions**: automatically starts and maintains three session types:
  - Deal session (`session_id`) — used for swap/FX deal structuring
  - XMarket session (`xmarket_session_id`) — required for curve downloads; created with `market_date`
  - Market data session — for pricing overrides
- **Sync dispatch**: `send(method, path, body)` using `httpx`
- **Async dispatch**: `send_async(method, path, body)` — used by `BootstrapService` for concurrent structuring
- **Polling**: pricing endpoints return immediately with a job ID; `MarsClient` polls `_results_endpoint()` with `tenacity` retry until results are available
- **Error handling**: raises `IpNotWhitelistedError` on 403, `SessionError` on session failures, `MarsApiError` for all other API errors

### `bloomberg/blpapi_client.py` — `BlpapiClient`
Thin synchronous wrapper around the Bloomberg Desktop API (`blpapi` C++ SDK).

- **`bdp(tickers, fields)`** — Bloomberg Data Point (current/reference data); returns `{ticker: {field: value}}`
- **`bds(ticker, field)`** — Bloomberg Data Set (bulk data); returns `list[dict]`
- **`bdh(tickers, fields, date)`** — Bloomberg Data History (historical data for a specific date); returns `{ticker: {field: value}}`
- Manages one long-lived session per instance; `stop()` or context manager for cleanup
- `import blpapi` is wrapped in `try/except ImportError` — the module loads safely on Streamlit Cloud where the SDK is not installed; instantiation raises `BlpapiError` if called without the package

### `bloomberg/exceptions.py`

```python
MarsApiError          # Base for all MARS REST API errors
  IpNotWhitelistedError   # 403 — caller IP not whitelisted by Bloomberg
  SessionError            # Session start or validation failure
  PricingError            # Pricing or solve request returned an error result
  CurveError              # Curve data download failure
  StructuringError        # Deal structuring request failure

BlpapiError           # Bloomberg Desktop API (BLPAPI) session or request failure
```

---

## Configs

### `configs/curves_config.py`

| Symbol | Type | Description |
|---|---|---|
| `CurveType` | `StrEnum` | `RAW` / `ZERO` / `DISCOUNT` |
| `CurveSpec` | dataclass | Per-type API keys, demo_key, scale, format |
| `CURVE_SPECS` | dict | `CurveType → CurveSpec` |
| `DEMO_CURVES` | list | 7 demo curve manifests (id, profile, label, filename) |
| `INTERPOLATION_METHODS` | dict | UI label → MARS method string |
| `CSA_CURVE_IDS` | dict | 43 currency codes → Bloomberg CSA OIS curve IDs |
| `FLOAT_INDICES` | list | 6 OIS float index tickers |
| `BOND_TO_SWPM_PAY_FREQUENCY` | dict | Coupon frequency → MARS pay-frequency label |

### `configs/swaps_config.py`

| Symbol | Type | Description |
|---|---|---|
| `SwapSpec` | dataclass | Full OIS/XCCY template: deal type, curves, notional, frequency, day count |
| `OIS_SWAP_SPECS` | dict | 6 OIS templates (COP, USD, BRL, MXN, CLP, EUR) |
| `XCCY_SWAP_SPECS` | dict | 6 XCCY templates (USDCOP, USDBRL, USDMXN, USDCLP, USDPEN, USDEUR) |
| `OIS_DEMO_SNAPSHOTS` | list | 6 OIS demo file manifests |
| `XCCY_DEMO_SNAPSHOTS` | list | 6 XCCY demo file manifests |
| `SWAP_DIRECTIONS` | list | `["Receive", "Pay"]` |
| `SWAP_PAY_FREQUENCIES` | list | 8 options from At Maturity to Daily |
| `SWAP_DAY_COUNTS` | list | 6 conventions (ACT/360, ACT/365, …, DU/252) |

### `configs/derivatives_config.py`

| Symbol | Description |
|---|---|
| `FxDerivativeSpec` | Per-pair template: deal type, ticker, currencies, notional, default tenor |
| `FX_VANILLA_SPECS` | 6 vanilla option specs |
| `FX_RR_SPECS` | 6 risk reversal specs |
| `FX_KI_SPECS` | 6 knock-in specs |
| `FX_KO_SPECS` | 6 knock-out specs |
| `FX_DIRECTIONS` | `["Buy", "Sell"]` |
| `FX_CALL_PUT` | `["Call", "Put"]` |
| `FX_EXERCISE_TYPES` | `["European", "American"]` |
| `FX_BARRIER_DIRS_KI` | `["Down & In", "Up & In"]` |
| `FX_BARRIER_DIRS_KO` | `["Down & Out", "Up & Out"]` |
| `FX_BARRIER_TYPES` | `["American", "European"]` |

### `configs/portfolio_config.py`
Defines `PORTFOLIO_DEALS` — a list of `PortfolioDealDef` entries (one per deal in the demo portfolio) with asset class, key, product type, and display label. Also contains `MARS_API_FIELDS` — a comprehensive catalog of MARS pricing response fields with their descriptions, used by the portfolio and KRR pages for column labelling.

### `configs/i18n.py`
`TRANSLATIONS` dict with keys in dot-notation (e.g. `"curves.page_title"`, `"swaps.solve_for_label"`) and values per language code (`"EN"`, `"PT"`, `"ES"`).

- `t(key, **kwargs)` — returns the translated string for the current session language; supports `str.format_map` for interpolated values
- `lang_selector()` — Streamlit sidebar widget that writes `st.session_state["lang"]`

---

## Demo Data

All files are JSON snapshots of real Bloomberg MARS API responses captured on **2026-03-27**. They are committed to the repository so the app runs fully offline on Streamlit Cloud.

| Path | Count | Content |
|---|---|---|
| `demo_data/curves/*.json` | 7 | `{curve_id, profile, label, curve_date, raw: [...], zero: [...], discount: [...]}` |
| `demo_data/swaps/*.json` | 12 | `{key, swap_type, label, tenor, valuation_date, par_rate, metrics: {...}}` |
| `demo_data/fx_derivatives/FX_*_*.json` | 24 | `{key, product_type, label, valuation_date, metrics: {...}}` |
| `demo_data/fx_derivatives/fx_rates.json` | 1 | `{USD:1.0, COP:3665.7, BRL:5.24, ...}` |
| `demo_data/bootstrap/sofr_schedules.json` | 1 | `{as_of, schedules: {tenor: [{accrual_start, accrual_end, payment_date, day_count, year_fraction}]}}` |
| `demo_data/deal_info/deal_types.json` | 1 | `[[code, description], ...]` |
| `demo_data/deal_info/schemas/*.json` | 14 | Full `dealSchema` response per deal type |

### Regenerating demo data

Run the master refresh script from a machine with live Bloomberg MARS credentials:

```bash
python scripts/refresh_demo_data.py               # uses DEMO_DATE (2026-03-27)
python scripts/refresh_demo_data.py 2026-06-30    # custom date
```

This script downloads all curves, swaps, FX derivatives, FX rates (via BLPAPI if available), and SOFR schedules, then saves them to `demo_data/`. Commit the updated files to update the deployed app.

---

## Scripts

| Script | Description |
|---|---|
| `scripts/refresh_demo_data.py` | **Master script** — refreshes all `demo_data/` in one run |
| `scripts/download_curves_demo_data.py` | Curves only |
| `scripts/download_swap_demo_data.py` | Swap snapshots only |
| `scripts/download_fx_deriv_demo_data.py` | FX derivative snapshots only |
| `scripts/download_fx_rates_demo_data.py` | FX spot rates only |
| `scripts/download_deal_info_demo_data.py` | Deal types + schema files |

All scripts read credentials from `.env` and exit with an error if `settings.demo_mode` is `True`.

---

## Deployment — Streamlit Cloud

1. Push the repository to GitHub (all `demo_data/` files must be committed)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo
3. Set **Main file path** to `app.py`
4. Under **Advanced settings → Secrets**, leave all Bloomberg fields empty — the app will run in demo mode automatically:

```toml
# No secrets required for demo mode.
# To enable live pricing, add:
# BBG_CLIENT_ID     = "..."
# BBG_CLIENT_SECRET = "..."
# BBG_UUID          = 12345678
```

The `blpapi` package is not in `requirements.txt` and is never imported at module level, so deployment succeeds without the Bloomberg Terminal SDK.

### Deploying to AWS / Azure / GCP

Since the MARS API is a pure HTTPS REST service, this app (or any Python client built on `MarsClient`) runs on any cloud provider. The pattern is the same across platforms:

**1. Pass credentials as environment variables**

```bash
BBG_CLIENT_ID=your_client_id
BBG_CLIENT_SECRET=your_client_secret
BBG_UUID=12345678
BBG_HOST=https://api.bloomberg.com
```

**2. Whitelist your server's outbound IP with Bloomberg**

Contact your Bloomberg representative or [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) to add your cloud instance IP to the MARS API allowlist. For dynamic IPs, use a NAT Gateway (AWS), a static outbound IP on Azure/GCP, or a fixed egress proxy.

**3. Platform-specific notes**

| Platform | Recommended service | Notes |
|---|---|---|
| **AWS** | ECS Fargate / Lambda / EC2 | Store credentials in Secrets Manager; use NAT Gateway for a fixed outbound IP |
| **Azure** | Container Apps / AKS / App Service | Store in Key Vault; use NAT Gateway or Azure Firewall for fixed egress |
| **GCP** | Cloud Run / GKE / Compute Engine | Store in Secret Manager; use Cloud NAT for fixed outbound IP |
| **Docker (any)** | `docker run -e BBG_CLIENT_ID=... -e BBG_CLIENT_SECRET=... -e BBG_UUID=...` | Works anywhere with outbound HTTPS |

```dockerfile
# Minimal Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless=true"]
```

---

## Dependencies

```
httpx>=0.27            # Async/sync HTTP client for MARS REST API
pydantic>=2.7          # Request/response models, settings validation
pydantic-settings>=2.3 # .env loading for credentials
PyJWT>=2.8             # HS256 JWT generation for MARS authentication
tenacity>=8.2          # Retry logic for polling MARS pricing job results
pandas>=2.2            # DataFrame manipulation throughout services
numpy>=1.26            # Bootstrap math (log, array ops)
python-dateutil>=2.9   # Date arithmetic for tenor calculations
streamlit>=1.36        # UI framework
plotly>=5.20           # Interactive charts
```

**Not in requirements** (optional, local use only):
- `blpapi` — Bloomberg Desktop API SDK; only needed for live SOFR par rates and FX spot prices. Install from the Bloomberg-distributed wheel if you have a Terminal.

---

## Bloomberg MARS API

This project uses the [Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/) — a professional-grade pricing, risk, and market data system available to Bloomberg Terminal subscribers.

### Why MARS API is ideal for Cloud deployments

Unlike Bloomberg's Desktop API (BLPAPI), which requires a local Bloomberg Terminal and is limited to on-premises machines, **the MARS REST API is a pure HTTPS service** — making it a natural fit for any cloud environment:

| | Bloomberg Desktop API (BLPAPI) | Bloomberg MARS REST API |
|---|---|---|
| **Transport** | TCP socket to localhost:8194 | HTTPS to `api.bloomberg.com` |
| **Terminal required** | ✅ Yes — must run on the Terminal machine | ❌ No — works from any server |
| **Cloud compatible** | ❌ No | ✅ Yes — AWS, Azure, GCP, any container |
| **Authentication** | Session-based (logged-in Terminal user) | HS256 JWT (client ID + secret) |
| **IP whitelisting** | Not required | Required (contact Bloomberg support) |
| **Scaling** | Single machine | Horizontally scalable (stateless REST) |

This means you can price swaps, pull curves, and run risk from:

- **AWS Lambda / ECS / EC2** — containerised Python microservices
- **Azure Functions / AKS** — event-driven or batch pricing pipelines
- **Google Cloud Run / GKE** — auto-scaled API backends
- **Streamlit Cloud / Heroku / Railway** — lightweight dashboards like this one
- **Jupyter on SageMaker / Vertex AI** — quantitative research notebooks

The only prerequisite is that your outbound IP is whitelisted by Bloomberg. Once whitelisted, credentials (`BBG_CLIENT_ID`, `BBG_CLIENT_SECRET`, `BBG_UUID`) are passed as environment variables — no Terminal, no local SDK, no VPN required.

Key endpoints used:

| Endpoint | Method | Usage |
|---|---|---|
| `/marswebapi/v1/dataDownload` | POST | XMarket curve download (raw / zero / discount) |
| `/marswebapi/v1/deals/temporary` | POST | Deal structuring (swap, FX option, SOFR schedule) |
| `/marswebapi/v1/securitiesPricing` | POST | Price and solve deals |
| `/marswebapi/v1/securitiesKrr` | POST | Key Rate Risk per security |
| `/marswebapi/v1/portfolioPricing` | POST | Portfolio MTM |
| `/enterprise/mars/portfolioKrr` | POST | Portfolio KRR |
| `/marswebapi/v1/dealType` | GET | List all deal type codes |
| `/marswebapi/v1/dealSchema` | GET | Full parameter schema for a deal type |
| `/marswebapi/v1/dataSessions` | POST | Start XMarket data session |

**Want to try the live API?** Contact [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) to request access.

---

## Contributing

Pull requests are welcome. For major changes please open an issue first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Follow the existing layer conventions (Repository pattern, `from_settings()` factory, i18n for all UI strings)
4. Test in both demo mode and live mode if possible
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE) for details.

Copyright 2026, Bloomberg Finance L.P.
