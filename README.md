# MARS API — Bloomberg LatAm

Python 3.12 service layer for the Bloomberg MARS (Multi-Asset Risk System) API.

## Prerequisites

- Python 3.12+
- Bloomberg EAPI credentials (client ID, client secret, UUID) from the Enterprise Console
- Your IP must be whitelisted by Bloomberg

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 2. Install the package in editable mode
pip install -e .

# 3. Copy the credentials template and fill in your values
copy .env.example .env          # Windows
cp .env.example .env            # macOS / Linux
```

Edit `.env` with your Bloomberg credentials:
```
BBG_CLIENT_ID=...
BBG_CLIENT_SECRET=...
BBG_UUID=...
```

## Project layout

```
bloomberg/          # API client layer (JWT auth, httpx, tenacity polling)
configs/            # pydantic-settings config loaded from .env
instruments/        # Pydantic v2 instrument models (Swap, FxOption, EquityOption)
services/           # Business logic services (security, curves, portfolio, risk)
examples/           # Runnable CLI scripts
```

## Quick start

```python
from configs.settings import settings
from bloomberg.webapi import MarsClient
from services.security_service import SecurityService

svc = SecurityService()
df = svc.price({
    "securitiesPricingRequest": {
        "pricingParameter": {
            "valuationDate": "2024-04-18+00:00",
            "requestedField": ["MktPx", "MktVal", "Notional"],
        },
        "security": [{"identifier": {"bloombergDealId": "IBM 2.85 05/15/2040 Corp"}}],
    }
})
print(df)
```

## Authentication

The API uses HS256 JWT tokens signed with your `client_secret`. Each request gets a
fresh token (5-minute expiry) injected as a `jwt` HTTP header. Sessions are managed
automatically by `MarsClient` and closed on destruction.

## Services

| Service | Methods |
|---|---|
| `SecurityService` | `structure`, `price`, `solve`, `save`, `get_deal_schema`, `get_deal_type`, `get_terms_and_conditions` |
| `CurvesService` | `download_curve` (Raw / Zero Coupon / Discount Factor) |
| `PortfolioService` | `create`, `price` |
| `RiskService` | `key_rate_risk` |

## Error handling

All services raise `MarsApiError` (or a subclass) on failure — no silent error tuples.

```python
from bloomberg.exceptions import MarsApiError, PricingError

try:
    df = svc.price(body)
except PricingError as e:
    print(f"Pricing failed: {e}")
except MarsApiError as e:
    print(f"API error: {e}")
```
