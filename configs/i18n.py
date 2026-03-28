"""
Internationalisation (i18n) helpers for the MARS API LatAm Streamlit app.

Supported languages: English (EN), Portuguese (PT), Spanish (ES).
All code comments and docstrings remain in English; only UI-facing strings
are translated here.

Usage in a Streamlit page:
    from configs.i18n import t
    st.title(t("app.title"))
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------

LANGUAGES: dict[str, str] = {
    "EN": "🇺🇸 English",
    "PT": "🇧🇷 Português",
    "ES": "🇪🇸 Español",
}

_DEFAULT_LANG = "EN"

# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------------
    # navigation labels
    # ------------------------------------------------------------------
    "nav.home": {
        "EN": "Home",
        "PT": "Início",
        "ES": "Inicio",
    },

    # ------------------------------------------------------------------
    # app.py — home page
    # ------------------------------------------------------------------
    "app.title": {
        "EN": "Bloomberg MARS API — LatAm",
        "PT": "Bloomberg MARS API — LatAm",
        "ES": "Bloomberg MARS API — LatAm",
    },
    "app.subtitle": {
        "EN": "**MARS** (Multi-Asset Risk System) API demo for Latin America markets. "
              "Built on Python 3.11 with `httpx`, `pydantic-settings`, and `streamlit`.",
        "PT": "Demo da API **MARS** (Multi-Asset Risk System) para mercados da América Latina. "
              "Desenvolvido em Python 3.11 com `httpx`, `pydantic-settings` e `streamlit`.",
        "ES": "Demo de la API **MARS** (Multi-Asset Risk System) para mercados de América Latina. "
              "Desarrollado en Python 3.11 con `httpx`, `pydantic-settings` y `streamlit`.",
    },
    "app.nav_prompt": {
        "EN": "**👈 Select a page from the sidebar** to explore the demos.",
        "PT": "**👈 Selecione uma página no menu lateral** para explorar as demos.",
        "ES": "**👈 Seleccione una página en el menú lateral** para explorar las demos.",
    },
    "app.demos_header": {
        "EN": "### Available demos",
        "PT": "### Demos disponíveis",
        "ES": "### Demos disponibles",
    },
    "app.table_page": {
        "EN": "Page",
        "PT": "Página",
        "ES": "Página",
    },
    "app.table_desc": {
        "EN": "Description",
        "PT": "Descrição",
        "ES": "Descripción",
    },
    "app.demo_curves": {
        "EN": "Download and visualize interest rate curves via XMarket",
        "PT": "Baixar e visualizar curvas de juros via XMarket",
        "ES": "Descargar y visualizar curvas de tasas de interés vía XMarket",
    },
    "app.demo_swaps": {
        "EN": "Structure, price, and solve IR swaps (SWPM back-end)",
        "PT": "Estruturar, precificar e solver swaps de juros (back-end SWPM)",
        "ES": "Estructurar, valorar y resolver swaps de tasas de interés (back-end SWPM)",
    },
    "app.demo_fx": {
        "EN": "Price FX vanilla options with full greeks (OVML back-end)",
        "PT": "Precificar opções de câmbio vanilla com gregas completas (back-end OVML)",
        "ES": "Valorar opciones FX vainilla con griegas completas (back-end OVML)",
    },
    "app.demo_portfolio": {
        "EN": "Price an entire Bloomberg portfolio",
        "PT": "Precificar um portfólio Bloomberg completo",
        "ES": "Valorar un portafolio Bloomberg completo",
    },
    "app.demo_dealinfo": {
        "EN": "Browse deal types, schemas, and terms & conditions",
        "PT": "Explorar tipos de deals, schemas e termos e condições",
        "ES": "Explorar tipos de operaciones, esquemas y términos y condiciones",
    },
    "app.demo_async": {
        "EN": "Build a par rate curve with concurrent async requests",
        "PT": "Construir uma curva de taxa par com requisições assíncronas paralelas",
        "ES": "Construir una curva de tasa par con solicitudes asíncronas concurrentes",
    },
    "app.resources_header": {
        "EN": "### Resources",
        "PT": "### Recursos",
        "ES": "### Recursos",
    },
    "app.coming_soon": {
        "EN": "*(Coming soon...)*",
        "PT": "*(Em breve...)*",
        "ES": "*(Próximamente...)*",
    },

    # ------------------------------------------------------------------
    # common — shared across pages
    # ------------------------------------------------------------------
    "common.status_demo": {
        "EN": "Demo Mode — mock data",
        "PT": "Modo Demo — dados simulados",
        "ES": "Modo Demo — datos simulados",
    },
    "common.status_live": {
        "EN": "Connected — Bloomberg API",
        "PT": "Conectado — Bloomberg API",
        "ES": "Conectado — Bloomberg API",
    },
    "common.lang_label": {
        "EN": "Language",
        "PT": "Idioma",
        "ES": "Idioma",
    },
    "common.demo_banner": {
        "EN": "**Demo Mode** — displaying pre-loaded market data (2026-03-18). "
              "Connect a Bloomberg MARS API account to access live data for any curve and date.",
        "PT": "**Modo Demo** — exibindo dados de mercado pré-carregados (2026-03-18). "
              "Conecte uma conta Bloomberg MARS API para acessar dados ao vivo de qualquer curva e data.",
        "ES": "**Modo Demo** — mostrando datos de mercado precargados (2026-03-18). "
              "Conecte una cuenta de Bloomberg MARS API para acceder a datos en vivo de cualquier curva y fecha.",
    },
    "common.demo_cta_sidebar": {
        "EN": "**Want live data?**\n\nThis tool is powered by the "
              "[Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/). "
              "Contact [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) to request a trial.",
        "PT": "**Quer dados ao vivo?**\n\nEsta ferramenta é alimentada pela "
              "[Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/). "
              "Entre em contato com [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) para solicitar uma versão de avaliação.",
        "ES": "**¿Quiere datos en vivo?**\n\nEsta herramienta utiliza la "
              "[Bloomberg MARS API](https://www.bloomberg.com/professional/product/multi-asset-risk-system/). "
              "Contacte a [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) para solicitar una prueba.",
    },
    "common.demo_cta_bottom": {
        "EN": "This is a live Bloomberg MARS API integration. "
              "With a MARS API subscription you get access to 246+ curves across all asset classes, "
              "live dates, and the full structuring & pricing engine. "
              "Contact [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) or "
              "[learn more about Bloomberg MARS]"
              "(https://www.bloomberg.com/professional/product/multi-asset-risk-system/)",
        "PT": "Esta é uma integração real com a Bloomberg MARS API. "
              "Com uma assinatura da MARS API você tem acesso a mais de 246 curvas em todas as "
              "classes de ativos, datas ao vivo e o motor completo de estruturação e precificação. "
              "Entre em contato com [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) ou "
              "[saiba mais sobre o Bloomberg MARS]"
              "(https://www.bloomberg.com/professional/product/multi-asset-risk-system/)",
        "ES": "Esta es una integración real con la Bloomberg MARS API. "
              "Con una suscripción a la MARS API obtiene acceso a más de 246 curvas en todas las "
              "clases de activos, fechas en vivo y el motor completo de estructuración y valoración. "
              "Contacte a [Ricardo Pfeuti](mailto:rpfeuti4@bloomberg.net) o "
              "[más información sobre Bloomberg MARS]"
              "(https://www.bloomberg.com/professional/product/multi-asset-risk-system/)",
    },

    # ------------------------------------------------------------------
    # curves page
    # ------------------------------------------------------------------
    "curves.page_title": {
        "EN": "Curves",
        "PT": "Curvas",
        "ES": "Curvas",
    },
    "curves.title": {
        "EN": "📈 Interest Rate Curves",
        "PT": "📈 Curvas de Juros",
        "ES": "📈 Curvas de Tasas de Interés",
    },
    "curves.caption": {
        "EN": "Download and visualize Bloomberg XMarket rate curves via the MARS API.",
        "PT": "Baixe e visualize curvas de juros Bloomberg XMarket via a API MARS.",
        "ES": "Descargue y visualice curvas de tasas Bloomberg XMarket vía la API MARS.",
    },
    "curves.sidebar_header": {
        "EN": "Curve parameters",
        "PT": "Parâmetros da curva",
        "ES": "Parámetros de la curva",
    },
    "curves.curve_label": {
        "EN": "Curve",
        "PT": "Curva",
        "ES": "Curva",
    },
    "curves.curve_help": {
        "EN": "Select a Bloomberg XMarket curve from the catalog.",
        "PT": "Selecione uma curva Bloomberg XMarket do catálogo.",
        "ES": "Seleccione una curva Bloomberg XMarket del catálogo.",
    },
    "curves.curve_help_demo": {
        "EN": "Demo mode: 7 LatAm + global curves available.",
        "PT": "Modo demo: 7 curvas LatAm + globais disponíveis.",
        "ES": "Modo demo: 7 curvas LatAm + globales disponibles.",
    },
    "curves.curve_id_caption": {
        "EN": "Curve ID: **{curve_id}**",
        "PT": "ID da curva: **{curve_id}**",
        "ES": "ID de curva: **{curve_id}**",
    },
    "curves.market_date_label": {
        "EN": "Market date (XMarket session)",
        "PT": "Data de mercado (sessão XMarket)",
        "ES": "Fecha de mercado (sesión XMarket)",
    },
    "curves.curve_date_label": {
        "EN": "Curve date",
        "PT": "Data da curva",
        "ES": "Fecha de la curva",
    },
    "curves.curve_type_label": {
        "EN": "Curve type",
        "PT": "Tipo de curva",
        "ES": "Tipo de curva",
    },
    "curves.side_label": {
        "EN": "Side",
        "PT": "Lado",
        "ES": "Lado",
    },
    "curves.interpolation_label": {
        "EN": "Interpolation method",
        "PT": "Método de interpolação",
        "ES": "Método de interpolación",
    },
    "curves.interval_label": {
        "EN": "Interval",
        "PT": "Intervalo",
        "ES": "Intervalo",
    },
    "curves.interval_help": {
        "EN": "Only used for Zero Coupon and Discount Factor curves.",
        "PT": "Usado apenas para curvas de Zero Cupom e Fator de Desconto.",
        "ES": "Solo se usa para curvas de Cupón Cero y Factor de Descuento.",
    },
    "curves.button_load": {
        "EN": "Load curve",
        "PT": "Carregar curva",
        "ES": "Cargar curva",
    },
    "curves.info_idle": {
        "EN": "Select a curve in the sidebar and click **Load curve**.",
        "PT": "Selecione uma curva no menu lateral e clique em **Carregar curva**.",
        "ES": "Seleccione una curva en el menú lateral y haga clic en **Cargar curva**.",
    },
    "curves.error_date_range": {
        "EN": "Curve date is too far in the future for the selected market date.",
        "PT": "A data da curva está muito no futuro para a data de mercado selecionada.",
        "ES": "La fecha de la curva está demasiado lejos en el futuro para la fecha de mercado seleccionada.",
    },
    "curves.error_curve": {
        "EN": "Curve error: {error}",
        "PT": "Erro de curva: {error}",
        "ES": "Error de curva: {error}",
    },
    "curves.error_api": {
        "EN": "Bloomberg API error: {error}",
        "PT": "Erro na API Bloomberg: {error}",
        "ES": "Error en la API Bloomberg: {error}",
    },
    "curves.warning_empty": {
        "EN": "No data returned for this curve.",
        "PT": "Nenhum dado retornado para esta curva.",
        "ES": "No se retornaron datos para esta curva.",
    },
    "curves.chart_title": {
        "EN": "{curve_type} — {profile}  |  {curve_id}{demo_tag}",
        "PT": "{curve_type} — {profile}  |  {curve_id}{demo_tag}",
        "ES": "{curve_type} — {profile}  |  {curve_id}{demo_tag}",
    },
    "curves.xaxis_tenor": {
        "EN": "Tenor",
        "PT": "Prazo",
        "ES": "Plazo",
    },
    "curves.xaxis_date": {
        "EN": "Date",
        "PT": "Data",
        "ES": "Fecha",
    },
    "curves.demo_date_tag": {
        "EN": "  |  Demo — 2026-03-18",
        "PT": "  |  Demo — 2026-03-18",
        "ES": "  |  Demo — 2026-03-18",
    },
    "curves.table_header": {
        "EN": "Curve data  —  {n} points",
        "PT": "Dados da curva  —  {n} pontos",
        "ES": "Datos de la curva  —  {n} puntos",
    },
    "curves.spinner_session": {
        "EN": "Starting XMarket session…",
        "PT": "Iniciando sessão XMarket…",
        "ES": "Iniciando sesión XMarket…",
    },
    "curves.spinner_download": {
        "EN": "Loading curve…",
        "PT": "Carregando curva…",
        "ES": "Cargando curva…",
    },

    # ------------------------------------------------------------------
    # swaps page
    # ------------------------------------------------------------------
    "swaps.page_title": {
        "EN": "Swaps",
        "PT": "Swaps",
        "ES": "Swaps",
    },
    "swaps.title": {
        "EN": "💱 Swaps — OIS & XCCY",
        "PT": "💱 Swaps — OIS e XCCY",
        "ES": "💱 Swaps — OIS y XCCY",
    },
    "swaps.caption": {
        "EN": "Structure and price interest rate swaps via the Bloomberg MARS API.",
        "PT": "Estruture e precifique swaps de juros via a Bloomberg MARS API.",
        "ES": "Estructure y valore swaps de tasas de interés vía Bloomberg MARS API.",
    },
    "swaps.tab_ois": {
        "EN": "OIS Swaps",
        "PT": "Swaps OIS",
        "ES": "Swaps OIS",
    },
    "swaps.tab_xccy": {
        "EN": "XCCY Swaps",
        "PT": "Swaps XCCY",
        "ES": "Swaps XCCY",
    },
    "swaps.template_label": {
        "EN": "Deal template",
        "PT": "Template do deal",
        "ES": "Plantilla del deal",
    },
    "swaps.template_help": {
        "EN": "Select a template to pre-fill all fields. You can override any value before pricing.",
        "PT": "Selecione um template para preencher todos os campos. Você pode alterar qualquer valor antes de precificar.",
        "ES": "Seleccione una plantilla para rellenar todos los campos. Puede cambiar cualquier valor antes de valorar.",
    },
    "swaps.leg1_header": {
        "EN": "Leg 1 — Fixed",
        "PT": "Perna 1 — Fixa",
        "ES": "Pata 1 — Fija",
    },
    "swaps.leg2_header": {
        "EN": "Leg 2 — Float",
        "PT": "Perna 2 — Flutuante",
        "ES": "Pata 2 — Variable",
    },
    "swaps.valuation_header": {
        "EN": "Valuation Settings",
        "PT": "Configurações de Valoração",
        "ES": "Configuración de Valoración",
    },
    "swaps.direction_label": {
        "EN": "Direction",
        "PT": "Direção",
        "ES": "Dirección",
    },
    "swaps.notional_label": {
        "EN": "Notional",
        "PT": "Nocional",
        "ES": "Nocional",
    },
    "swaps.currency_label": {
        "EN": "Currency",
        "PT": "Moeda",
        "ES": "Moneda",
    },
    "swaps.effective_label": {
        "EN": "Effective date",
        "PT": "Data de início",
        "ES": "Fecha de inicio",
    },
    "swaps.tenor_label": {
        "EN": "Tenor",
        "PT": "Prazo",
        "ES": "Plazo",
    },
    "swaps.maturity_label": {
        "EN": "Maturity date",
        "PT": "Data de vencimento",
        "ES": "Fecha de vencimiento",
    },
    "swaps.fixed_rate_label": {
        "EN": "Fixed rate (% — leave blank to solve)",
        "PT": "Taxa fixa (% — deixe em branco para resolver)",
        "ES": "Tasa fija (% — deje en blanco para resolver)",
    },
    "swaps.float_index_label": {
        "EN": "Float index",
        "PT": "Índice flutuante",
        "ES": "Índice variable",
    },
    "swaps.spread_label": {
        "EN": "Spread (bp)",
        "PT": "Spread (bp)",
        "ES": "Spread (bp)",
    },
    "swaps.pay_freq_label": {
        "EN": "Pay frequency",
        "PT": "Frequência de pagamento",
        "ES": "Frecuencia de pago",
    },
    "swaps.day_count_label": {
        "EN": "Day count",
        "PT": "Base de cálculo",
        "ES": "Base de cálculo",
    },
    "swaps.curve_date_label": {
        "EN": "Curve date",
        "PT": "Data da curva",
        "ES": "Fecha de curva",
    },
    "swaps.valuation_date_label": {
        "EN": "Valuation date",
        "PT": "Data de valoração",
        "ES": "Fecha de valoración",
    },
    "swaps.csa_ccy_label": {
        "EN": "CSA collateral currency",
        "PT": "Moeda de colateral CSA",
        "ES": "Moneda de colateral CSA",
    },
    "swaps.coll_curve_label": {
        "EN": "Collateral curve",
        "PT": "Curva de colateral",
        "ES": "Curva de colateral",
    },
    "swaps.discount_curve_label": {
        "EN": "Discount curve",
        "PT": "Curva de desconto",
        "ES": "Curva de descuento",
    },
    "swaps.forward_curve_label": {
        "EN": "Proj. curve",
        "PT": "Curva proj.",
        "ES": "Curva proj.",
    },
    "swaps.solve_for_label": {
        "EN": "Solve for",
        "PT": "Resolver para",
        "ES": "Resolver para",
    },
    "swaps.button_price": {
        "EN": "Price swap",
        "PT": "Precificar swap",
        "ES": "Valorar swap",
    },
    "swaps.spinner_session": {
        "EN": "Starting deal session…",
        "PT": "Iniciando sessão de deals…",
        "ES": "Iniciando sesión de deals…",
    },
    "swaps.spinner_pricing": {
        "EN": "Pricing swap…",
        "PT": "Precificando swap…",
        "ES": "Valorando swap…",
    },
    "swaps.result_par_cpn": {
        "EN": "Par Cpn (%)",
        "PT": "Taxa Par (%)",
        "ES": "Cpn Par (%)",
    },
    "swaps.result_npv": {
        "EN": "NPV",
        "PT": "VPL",
        "ES": "VPN",
    },
    "swaps.result_dv01": {
        "EN": "DV01",
        "PT": "DV01",
        "ES": "DV01",
    },
    "swaps.result_pv01": {
        "EN": "PV01",
        "PT": "PV01",
        "ES": "PV01",
    },
    "swaps.result_bp_value": {
        "EN": "BP Value",
        "PT": "Valor BP",
        "ES": "Valor BP",
    },
    "swaps.result_accrued": {
        "EN": "Accrued",
        "PT": "Acruado",
        "ES": "Devengado",
    },
    "swaps.result_premium": {
        "EN": "Premium (%)",
        "PT": "Prêmio (%)",
        "ES": "Prima (%)",
    },
    "swaps.info_idle": {
        "EN": "Configure the swap above and click **Price swap** to run the calculation.",
        "PT": "Configure o swap acima e clique em **Precificar swap** para calcular.",
        "ES": "Configure el swap arriba y haga clic en **Valorar swap** para calcular.",
    },
    "swaps.error_pricing": {
        "EN": "Pricing error: {error}",
        "PT": "Erro de precificação: {error}",
        "ES": "Error de valoración: {error}",
    },
    "swaps.error_structuring": {
        "EN": "Structuring error: {error}",
        "PT": "Erro de estruturação: {error}",
        "ES": "Error de estructuración: {error}",
    },
    "swaps.warning_no_result": {
        "EN": "No pricing result returned. Check your inputs.",
        "PT": "Nenhum resultado retornado. Verifique os parâmetros.",
        "ES": "No se obtuvo resultado. Verifique los parámetros.",
    },
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_lang() -> str:
    """Return the current language code from Streamlit session state."""
    return st.session_state.get("lang", _DEFAULT_LANG)


def t(key: str, **kwargs: object) -> str:
    """
    Look up a translation key for the current session language.

    Falls back to English if the key or language is missing.
    Supports format placeholders: t("curves.error_curve", error=str(e))
    """
    lang = get_lang()
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get(_DEFAULT_LANG) or key
    return text.format(**kwargs) if kwargs else text


def lang_selector(sidebar: bool = True) -> str:
    """
    Render a language selectbox and persist the choice in session state.

    Returns the selected language code ("EN", "PT", or "ES").
    """
    container = st.sidebar if sidebar else st
    lang = container.selectbox(
        t("common.lang_label"),
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        key="lang",
        index=list(LANGUAGES.keys()).index(get_lang()),
    )
    return lang  # type: ignore[return-value]
