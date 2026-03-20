# MARS API LatAm — Bloomberg MARS Rate Curves Explorer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://marsapilatam.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source Python application built on top of the **Bloomberg MARS (Multi-Asset Risk System) API** that lets you explore, visualize, and price interest rate curves across LatAm and global markets.

> **Try the live demo** → [marsapilatam.streamlit.app](https://marsapilatam.streamlit.app)
> No Bloomberg subscription needed for the demo. Connect your own credentials to unlock all 246+ curves and live pricing.

---

## Features

- **246 rate curves** across 50+ currencies from Bloomberg XMarket
- Interactive Plotly charts with correct tenor spacing
- Raw Curve, Zero Coupon, and Discount Factor views
- Swap structuring & pricing engine (Bloomberg SWPM back-end)
- Full LatAm coverage: COP, BRL, MXN, CLP, PEN, ARS

## Demo Mode

When no Bloomberg credentials are configured the app automatically enters **demo mode**, serving pre-loaded real market data (2026-03-18) for 7 representative curves:

| Curve | Country | ID |
|---|---|---|
| COP OIS | Colombia | S329 |
| USD SOFR | United States | S490 |
| BRL Pre x DI | Brazil | S89 |
| MXN OIS TIIE | Mexico | S583 |
| CLP 6m | Chile | S193 |
| EUR OIS ESTR | Europe | S514 |
| PEN OIS | Peru | S374 |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/marsapilatam.git
cd marsapilatam
```

### 2. Install dependencies

```bash
pip install -e .[dev]
```

### 3a. Run in demo mode (no credentials)

```bash
streamlit run app.py
```

The app will start immediately using the pre-loaded curve data.

### 3b. Run with live Bloomberg data

Copy `.env.example` to `.env` and fill in your Bloomberg MARS API credentials:

```bash
cp .env.example .env
```

```env
BBG_CLIENT_ID=your_client_id
BBG_CLIENT_SECRET=your_hex_secret
BBG_UUID=your_bloomberg_uuid
```

Then run:

```bash
streamlit run app.py
```

## Project Structure

```
marsapilatam/
├── app.py                   # Streamlit home page
├── pages/
│   └── 1_📈_Curves.py       # Rate curves explorer
├── bloomberg/
│   ├── webapi/              # MARS API client (JWT auth, sessions, polling)
│   └── pricing_result.py    # Response parser
├── services/
│   ├── curves_service.py    # XMarket curve downloads
│   └── security_service.py  # Deal structuring & pricing
├── instruments/             # Typed Pydantic models (Swap, FxOption, EquityOption)
├── configs/
│   ├── settings.py          # Credentials + constants
│   └── curves_catalog.py    # 248 Bloomberg XMarket curves
├── demo_data/               # Pre-saved JSON curve data for demo mode
└── docs/                    # API documentation & Swagger spec
```

## Bloomberg MARS API

This project uses the [Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/) — a professional-grade pricing and risk system available to Bloomberg Terminal subscribers.

**Want to try it?** Contact [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) to request a trial.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request

## License

MIT — see [LICENSE](LICENSE) for details.
