import streamlit as st

st.set_page_config(
    page_title="MARS API LatAm",
    page_icon="📊",
    layout="wide",
)

st.title("Bloomberg MARS API — LatAm")

st.markdown(
    """
    **MARS** (Multi-Asset Risk System) API demo for Latin America markets.
    Built on Python 3.11 with `httpx`, `pydantic-settings`, and `streamlit`.

    **👈 Select a page from the sidebar** to explore the demos.

    ---

    ### Available demos

    | Page | Description |
    |---|---|
    | 📈 Curves | Download and visualize interest rate curves via XMarket |
    | 💱 Swaps | Structure, price, and solve IR swaps (SWPM back-end) |
    | 💵 FX Options | Price FX vanilla options with full greeks (OVML back-end) |
    | 🏦 Portfolio | Price an entire Bloomberg portfolio |
    | 📃 Deal Information | Browse deal types, schemas, and terms & conditions |
    | 🚀 Swaps Async | Build a par rate curve with concurrent async requests |

    ---

    ### Resources
    - Bloomberg Terminal: `RISK<GO>`, `EAPI<GO>`, `SWPM<GO>`, `OVML<GO>`
    - [Bloomberg MARS API documentation](https://developer.bloomberg.com/pages/apis/marsapi/reference)
    """
)
