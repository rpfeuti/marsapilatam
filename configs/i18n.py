"""
Internationalisation (i18n) helpers for the MARS API LatAm Streamlit app.

Supported languages: English (EN), Portuguese (PT), Spanish (ES).
All code comments and docstrings remain in English; only UI-facing strings
are translated here.

Usage in a Streamlit page:
    from configs.i18n import t
    st.title(t("app.title"))

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
        "EN": "🪐🔴🌍 Bloomberg MARS API — LatAm 🌍🔴🪐",
        "PT": "🪐🔴🌍 Bloomberg MARS API — LatAm 🌍🔴🪐",
        "ES": "🪐🔴🌍 Bloomberg MARS API — LatAm 🌍🔴🪐",
    },
    "app.subtitle": {
        "EN": "**MARS** (Multi-Asset Risk System) API demo for Latin America markets. "
              "Built on Python 3.11 with `httpx`, `pydantic-settings`, and `streamlit`, "
              'and of course, with a "happy" interaction with Claude and Cursor :)',
        "PT": "Demo da API **MARS** (Multi-Asset Risk System) para mercados da América Latina. "
              "Desenvolvido em Python 3.11 com `httpx`, `pydantic-settings` e `streamlit`, "
              'e claro, com uma interação "feliz" com Claude e Cursor :)',
        "ES": "Demo de la API **MARS** (Multi-Asset Risk System) para mercados de América Latina. "
              "Desarrollado en Python 3.11 con `httpx`, `pydantic-settings` y `streamlit`, "
              'y por supuesto, con una interacción "feliz" con Claude y Cursor :)',
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
        "EN": "Price FX vanilla, barriers, and structures with full greeks (OVML back-end)",
        "PT": "Precificar vanilla, barreiras e estruturas FX com gregas completas (back-end OVML)",
        "ES": "Valorar vanilla, barreras y estructuras FX con griegas completas (back-end OVML)",
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
    "app.demo_stress": {
        "EN": "Run stress test scenarios on portfolios and single deals",
        "PT": "Executar cenários de teste de estresse em portfólios e deals individuais",
        "ES": "Ejecutar escenarios de prueba de estrés en portafolios y operaciones individuales",
    },
    "app.demo_krr": {
        "EN": "Key Rate Risk — DV01 decomposition by tenor bucket",
        "PT": "Risco por Vértice — decomposição do DV01 por bucket de prazo",
        "ES": "Riesgo por Vértice — descomposición del DV01 por bucket de plazo",
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
    # deal info page
    # ------------------------------------------------------------------
    "dealinfo.page_title": {
        "EN": "Deal Info",
        "PT": "Info de Deals",
        "ES": "Info de Deals",
    },
    "dealinfo.title": {
        "EN": "📃 Deal Information",
        "PT": "📃 Informações de Deals",
        "ES": "📃 Información de Deals",
    },
    "dealinfo.caption": {
        "EN": "Browse deal types, schemas, and terms & conditions via the Bloomberg MARS API.",
        "PT": "Explore tipos de deals, schemas e termos e condições via a API Bloomberg MARS.",
        "ES": "Explore tipos de operaciones, esquemas y términos y condiciones via la API Bloomberg MARS.",
    },
    "dealinfo.deal_type_label": {
        "EN": "Deal type",
        "PT": "Tipo de deal",
        "ES": "Tipo de operación",
    },
    "dealinfo.btn_load": {
        "EN": "Load schema",
        "PT": "Carregar schema",
        "ES": "Cargar esquema",
    },
    "dealinfo.deal_params_header": {
        "EN": "Deal-Level Parameters",
        "PT": "Parâmetros do Deal",
        "ES": "Parámetros del Deal",
    },
    "dealinfo.leg_header": {
        "EN": "Leg {n} Parameters",
        "PT": "Parâmetros da Perna {n}",
        "ES": "Parámetros de la Pata {n}",
    },
    "dealinfo.no_params": {
        "EN": "No parameters found.",
        "PT": "Nenhum parâmetro encontrado.",
        "ES": "No se encontraron parámetros.",
    },
    "dealinfo.col_name": {
        "EN": "Name",
        "PT": "Nome",
        "ES": "Nombre",
    },
    "dealinfo.col_type": {
        "EN": "Type",
        "PT": "Tipo",
        "ES": "Tipo",
    },
    "dealinfo.col_mode": {
        "EN": "Mode",
        "PT": "Modo",
        "ES": "Modo",
    },
    "dealinfo.col_solvable": {
        "EN": "Solvable",
        "PT": "Solucionável",
        "ES": "Resoluble",
    },
    "dealinfo.col_category": {
        "EN": "Category",
        "PT": "Categoria",
        "ES": "Categoría",
    },
    "dealinfo.col_description": {
        "EN": "Description",
        "PT": "Descrição",
        "ES": "Descripción",
    },
    "dealinfo.col_allowed": {
        "EN": "Allowed Values",
        "PT": "Valores Permitidos",
        "ES": "Valores Permitidos",
    },
    "dealinfo.summary": {
        "EN": "{total} parameters · {legs} legs · {solvable} solvable fields",
        "PT": "{total} parâmetros · {legs} pernas · {solvable} campos solucionáveis",
        "ES": "{total} parámetros · {legs} patas · {solvable} campos resolubles",
    },
    "dealinfo.spinner": {
        "EN": "Loading schema…",
        "PT": "Carregando schema…",
        "ES": "Cargando esquema…",
    },
    "dealinfo.spinner_types": {
        "EN": "Loading deal types…",
        "PT": "Carregando tipos de deal…",
        "ES": "Cargando tipos de operación…",
    },
    "dealinfo.info_idle": {
        "EN": "Select a deal type above and click **Load schema** to inspect its parameters.",
        "PT": "Selecione um tipo de deal acima e clique em **Carregar schema** para inspecionar os parâmetros.",
        "ES": "Seleccione un tipo de operación arriba y haga clic en **Cargar esquema** para inspeccionar los parámetros.",
    },
    "dealinfo.types_available": {
        "EN": "{n} deal types available",
        "PT": "{n} tipos de deal disponíveis",
        "ES": "{n} tipos de operación disponibles",
    },
    "common.yes": {
        "EN": "Yes",
        "PT": "Sim",
        "ES": "Sí",
    },
    "nav.deal_info": {
        "EN": "Deal Information",
        "PT": "Informações de Deals",
        "ES": "Información de Deals",
    },
    "nav.fx_options": {
        "EN": "FX Options",
        "PT": "Opções de Câmbio",
        "ES": "Opciones FX",
    },
    "nav.portfolio": {
        "EN": "Portfolio",
        "PT": "Portfólio",
        "ES": "Portafolio",
    },
    "nav.swaps_async": {
        "EN": "Swaps Async",
        "PT": "Swaps Assíncronos",
        "ES": "Swaps Asíncronos",
    },
    "nav.stress_testing": {
        "EN": "Stress Testing",
        "PT": "Teste de Estresse",
        "ES": "Prueba de Estrés",
    },
    "nav.krr": {
        "EN": "Key Rate Risk",
        "PT": "Risco por Vértice",
        "ES": "Riesgo por Vértice",
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

    # ------------------------------------------------------------------
    # derivatives page — FX Derivatives
    # ------------------------------------------------------------------
    "deriv.page_title": {
        "EN": "FX Derivatives",
        "PT": "Derivativos FX",
        "ES": "Derivados FX",
    },
    "deriv.title": {
        "EN": "📊 FX Derivatives",
        "PT": "📊 Derivativos FX",
        "ES": "📊 Derivados FX",
    },
    "deriv.caption": {
        "EN": "Structure and price FX options via the Bloomberg MARS API (OVML back-end).",
        "PT": "Estruture e precifique opções de câmbio via a Bloomberg MARS API (back-end OVML).",
        "ES": "Estructure y valore opciones FX vía Bloomberg MARS API (back-end OVML).",
    },
    "deriv.tab_vanilla": {
        "EN": "FX Vanilla",
        "PT": "FX Vanilla",
        "ES": "FX Vanilla",
    },
    "deriv.tab_rr": {
        "EN": "Risk Reversal",
        "PT": "Risk Reversal",
        "ES": "Risk Reversal",
    },
    "deriv.tab_barrier": {
        "EN": "FX Barriers",
        "PT": "Barreiras FX",
        "ES": "Barreras FX",
    },
    "deriv.template_label": {
        "EN": "Currency pair",
        "PT": "Par de moedas",
        "ES": "Par de divisas",
    },
    "deriv.template_help": {
        "EN": "Select a currency pair to pre-fill the form. "
              "You can override any value before pricing.",
        "PT": "Selecione um par de moedas para preencher o formulário. "
              "Altere qualquer valor antes de precificar.",
        "ES": "Seleccione un par de divisas para rellenar el formulario. "
              "Puede cambiar cualquier valor antes de valorar.",
    },
    "deriv.direction_label": {
        "EN": "Direction",
        "PT": "Direção",
        "ES": "Dirección",
    },
    "deriv.call_put_label": {
        "EN": "Call / Put",
        "PT": "Call / Put",
        "ES": "Call / Put",
    },
    "deriv.notional_label": {
        "EN": "Notional",
        "PT": "Nocional",
        "ES": "Nocional",
    },
    "deriv.notional_ccy_label": {
        "EN": "Notional ccy",
        "PT": "Moeda nocional",
        "ES": "Moneda nocional",
    },
    "deriv.underlying_label": {
        "EN": "Underlying",
        "PT": "Subjacente",
        "ES": "Subyacente",
    },
    "deriv.strike_label": {
        "EN": "Strike",
        "PT": "Strike",
        "ES": "Strike",
    },
    "deriv.expiry_label": {
        "EN": "Expiry date",
        "PT": "Data de vencimento",
        "ES": "Fecha de vencimiento",
    },
    "deriv.exercise_type_label": {
        "EN": "Exercise type",
        "PT": "Tipo de exercício",
        "ES": "Tipo de ejercicio",
    },
    "deriv.barrier_type_label": {
        "EN": "Barrier type",
        "PT": "Tipo de barreira",
        "ES": "Tipo de barrera",
    },
    "deriv.barrier_dir_label": {
        "EN": "Barrier direction",
        "PT": "Direção da barreira",
        "ES": "Dirección de barrera",
    },
    "deriv.barrier_level_label": {
        "EN": "Barrier level",
        "PT": "Nível da barreira",
        "ES": "Nivel de barrera",
    },
    "deriv.barrier_product_label": {
        "EN": "Barrier product",
        "PT": "Produto de barreira",
        "ES": "Producto de barrera",
    },
    "deriv.leg1_header": {
        "EN": "Leg 1",
        "PT": "Perna 1",
        "ES": "Pata 1",
    },
    "deriv.leg2_header": {
        "EN": "Leg 2",
        "PT": "Perna 2",
        "ES": "Pata 2",
    },
    "deriv.deal_terms_header": {
        "EN": "Deal Terms",
        "PT": "Termos do Deal",
        "ES": "Términos del Deal",
    },
    "deriv.valuation_header": {
        "EN": "Valuation Settings",
        "PT": "Configurações de Valoração",
        "ES": "Configuración de Valoración",
    },
    "deriv.valuation_date_label": {
        "EN": "Valuation date",
        "PT": "Data de valoração",
        "ES": "Fecha de valoración",
    },
    "deriv.curve_date_label": {
        "EN": "Curve date",
        "PT": "Data da curva",
        "ES": "Fecha de curva",
    },
    "deriv.button_price": {
        "EN": "Price",
        "PT": "Precificar",
        "ES": "Valorar",
    },
    "deriv.spinner_session": {
        "EN": "Starting deal session…",
        "PT": "Iniciando sessão de deals…",
        "ES": "Iniciando sesión de deals…",
    },
    "deriv.spinner_pricing": {
        "EN": "Pricing derivative…",
        "PT": "Precificando derivativo…",
        "ES": "Valorando derivado…",
    },
    "deriv.info_idle": {
        "EN": "Configure the derivative above and click **Price** to run the calculation.",
        "PT": "Configure o derivativo acima e clique em **Precificar** para calcular.",
        "ES": "Configure el derivado arriba y haga clic en **Valorar** para calcular.",
    },
    "deriv.error_pricing": {
        "EN": "Pricing error: {error}",
        "PT": "Erro de precificação: {error}",
        "ES": "Error de valoración: {error}",
    },
    "deriv.error_structuring": {
        "EN": "Structuring error: {error}",
        "PT": "Erro de estruturação: {error}",
        "ES": "Error de estructuración: {error}",
    },
    "deriv.warning_no_result": {
        "EN": "No pricing result returned. Check your inputs.",
        "PT": "Nenhum resultado retornado. Verifique os parâmetros.",
        "ES": "No se obtuvo resultado. Verifique los parámetros.",
    },
    "deriv.result_premium": {
        "EN": "Premium (%)",
        "PT": "Prêmio (%)",
        "ES": "Prima (%)",
    },
    "deriv.result_delta": {
        "EN": "Delta",
        "PT": "Delta",
        "ES": "Delta",
    },
    "deriv.result_gamma": {
        "EN": "Gamma",
        "PT": "Gamma",
        "ES": "Gamma",
    },
    "deriv.result_vega": {
        "EN": "Vega",
        "PT": "Vega",
        "ES": "Vega",
    },
    "deriv.result_theta": {
        "EN": "Theta",
        "PT": "Theta",
        "ES": "Theta",
    },
    "deriv.result_rho": {
        "EN": "Rho",
        "PT": "Rho",
        "ES": "Rho",
    },
    "deriv.result_implied_vol": {
        "EN": "Impl. Vol (%)",
        "PT": "Vol Impl. (%)",
        "ES": "Vol Impl. (%)",
    },
    "deriv.result_spot": {
        "EN": "Spot",
        "PT": "Spot",
        "ES": "Spot",
    },
    "deriv.result_forward": {
        "EN": "Forward",
        "PT": "Forward",
        "ES": "Forward",
    },
    "deriv.result_npv": {
        "EN": "NPV",
        "PT": "VPL",
        "ES": "VPN",
    },

    # ------------------------------------------------------------------
    # common — save deal
    # ------------------------------------------------------------------
    "common.button_save_deal": {
        "EN": "Save Deal on Bloomberg",
        "PT": "Salvar Deal na Bloomberg",
        "ES": "Guardar Deal en Bloomberg",
    },
    "common.spinner_saving": {
        "EN": "Saving deal…",
        "PT": "Salvando deal…",
        "ES": "Guardando deal…",
    },
    "common.save_success": {
        "EN": "Deal saved — ID: **{deal_id}**",
        "PT": "Deal salvo — ID: **{deal_id}**",
        "ES": "Deal guardado — ID: **{deal_id}**",
    },
    "common.save_error": {
        "EN": "Failed to save deal: {error}",
        "PT": "Falha ao salvar deal: {error}",
        "ES": "Error al guardar deal: {error}",
    },

    # ------------------------------------------------------------------
    # Portfolio page
    # ------------------------------------------------------------------
    "portfolio.page_title": {
        "EN": "Portfolio",
        "PT": "Portfólio",
        "ES": "Portafolio",
    },
    "portfolio.title": {
        "EN": "🏦 Portfolio Pricing",
        "PT": "🏦 Precificação de Portfólio",
        "ES": "🏦 Valoración de Portafolio",
    },
    "portfolio.caption": {
        "EN": "Price existing Bloomberg portfolios and view "
              "risk metrics via the MARS API.",
        "PT": "Precifique portfólios Bloomberg existentes e "
              "visualize métricas de risco via a API MARS.",
        "ES": "Valore portafolios Bloomberg existentes y "
              "visualice métricas de riesgo vía la API MARS.",
    },
    "portfolio.price_btn": {
        "EN": "Price Portfolio",
        "PT": "Precificar Portfólio",
        "ES": "Valorar Portafolio",
    },
    "portfolio.pricing_spinner": {
        "EN": "Pricing portfolio…",
        "PT": "Precificando portfólio…",
        "ES": "Valorando portafolio…",
    },
    "portfolio.summary_header": {
        "EN": "Portfolio Summary",
        "PT": "Resumo do Portfólio",
        "ES": "Resumen del Portafolio",
    },
    "portfolio.total_mtm": {
        "EN": "Total MtM (USD)",
        "PT": "MtM Total (USD)",
        "ES": "MtM Total (USD)",
    },
    "portfolio.total_dv01": {
        "EN": "Total DV01",
        "PT": "DV01 Total",
        "ES": "DV01 Total",
    },
    "portfolio.total_pv01": {
        "EN": "Total PV01",
        "PT": "PV01 Total",
        "ES": "PV01 Total",
    },
    "portfolio.total_vega": {
        "EN": "Total Vega",
        "PT": "Vega Total",
        "ES": "Vega Total",
    },
    "portfolio.total_delta": {
        "EN": "Total Delta",
        "PT": "Delta Total",
        "ES": "Delta Total",
    },
    "portfolio.deal_count": {
        "EN": "Deal Count",
        "PT": "Qtd. de Deals",
        "ES": "Cant. de Deals",
    },
    "portfolio.select_label": {
        "EN": "Select Portfolio",
        "PT": "Selecionar Portfólio",
        "ES": "Seleccionar Portafolio",
    },
    "portfolio.deals_header": {
        "EN": "Portfolio Deals",
        "PT": "Deals do Portfólio",
        "ES": "Deals del Portafolio",
    },
    "portfolio.select_columns": {
        "EN": "Visible columns",
        "PT": "Colunas visíveis",
        "ES": "Columnas visibles",
    },

    # -----------------------------------------------------------------------
    # Stress Testing
    # -----------------------------------------------------------------------

    "stress.page_title": {
        "EN": "Stress Testing",
        "PT": "Teste de Estresse",
        "ES": "Prueba de Estrés",
    },
    "stress.title": {
        "EN": "Stress Testing",
        "PT": "Teste de Estresse",
        "ES": "Prueba de Estrés",
    },
    "stress.caption": {
        "EN": "Run interest rate shocks on a single deal or portfolio, run one or multiple scenarios like the sample below",
        "PT": "Execute choques de taxa de juros em um deal individual ou carteira, execute um ou múltiplos cenários como o exemplo abaixo",
        "ES": "Ejecute choques de tasa de interés en un deal individual o cartera, ejecute uno o múltiples escenarios como el ejemplo a continuación",
    },
    "stress.deal_label": {
        "EN": "Bloomberg Deal ID",
        "PT": "ID do Deal Bloomberg",
        "ES": "ID del Deal Bloomberg",
    },
    "stress.scenarios_header": {
        "EN": "IRRBB Scenarios Sample",
        "PT": "Amostra de Cenários IRRBB",
        "ES": "Muestra de Escenarios IRRBB",
    },
    "stress.grid_caption": {
        "EN": "Edit basis-point shifts per tenor and scenario. Sort by any scenario column. Use ↺ Reset to restore tenor order.",
        "PT": "Edite os choques em pontos-base por vértice e cenário. Ordene por qualquer coluna. Use ↺ Reset para restaurar a ordem dos vértices.",
        "ES": "Edite los choques en puntos básicos por tenor y escenario. Ordene por cualquier columna. Use ↺ Reset para restaurar el orden de tenores.",
    },
    "stress.run_btn": {
        "EN": "Run Stress Test",
        "PT": "Executar Teste de Estresse",
        "ES": "Ejecutar Prueba de Estrés",
    },
    "stress.running_spinner": {
        "EN": "Creating scenarios and pricing...",
        "PT": "Criando cenários e precificando...",
        "ES": "Creando escenarios y valorando...",
    },
    "stress.base_case": {
        "EN": "Deal Base Case",
        "PT": "Caso Base do Deal",
        "ES": "Caso Base del Deal",
    },
    "stress.results_header": {
        "EN": "Deal Stress Test Results",
        "PT": "Resultados do Teste de Estresse do Deal",
        "ES": "Resultados de la Prueba de Estrés del Deal",
    },
    "stress.col_scenario": {
        "EN": "Scenario",
        "PT": "Cenário",
        "ES": "Escenario",
    },
    "stress.col_shift": {
        "EN": "Shift (bp)",
        "PT": "Choque (bp)",
        "ES": "Choque (bp)",
    },
    "stress.col_mtm": {
        "EN": "MtM (Port. Ccy)",
        "PT": "MtM (Moeda Carteira)",
        "ES": "MtM (Mon. Cartera)",
    },
    "stress.col_delta_mtm": {
        "EN": "Delta MtM",
        "PT": "Delta MtM",
        "ES": "Delta MtM",
    },
    "stress.col_dv01": {
        "EN": "DV01 (Port. Ccy)",
        "PT": "DV01 (Moeda Carteira)",
        "ES": "DV01 (Mon. Cartera)",
    },
    "stress.col_pv01": {
        "EN": "PV01",
        "PT": "PV01",
        "ES": "PV01",
    },
    "stress.chart_title": {
        "EN": "MtM Change by Scenario",
        "PT": "Variação do MtM por Cenário",
        "ES": "Cambio del MtM por Escenario",
    },
    "stress.error": {
        "EN": "Stress test failed: {error}",
        "PT": "Teste de estresse falhou: {error}",
        "ES": "Prueba de estrés falló: {error}",
    },
    "stress.no_results": {
        "EN": "No scenario results returned",
        "PT": "Nenhum resultado de cenário retornado",
        "ES": "No se devolvieron resultados de escenarios",
    },
    "stress.base_mtm": {
        "EN": "MtM (Port. Ccy)",
        "PT": "MtM (Moeda Carteira)",
        "ES": "MtM (Mon. Cartera)",
    },
    "stress.base_dv01": {
        "EN": "DV01 (Port. Ccy)",
        "PT": "DV01 (Moeda Carteira)",
        "ES": "DV01 (Mon. Cartera)",
    },
    "stress.base_pv01": {
        "EN": "Base PV01",
        "PT": "PV01 Base",
        "ES": "PV01 Base",
    },
    "stress.base_price": {
        "EN": "Price",
        "PT": "Preço",
        "ES": "Precio",
    },
    "stress.tab_deal": {
        "EN": "Single Deal",
        "PT": "Deal Individual",
        "ES": "Operación Individual",
    },
    "stress.tab_portfolio": {
        "EN": "Portfolio",
        "PT": "Carteira",
        "ES": "Cartera",
    },
    "stress.portfolio_label": {
        "EN": "Portfolio Name",
        "PT": "Nome da Carteira",
        "ES": "Nombre de la Cartera",
    },
    "stress.portfolio_run_btn": {
        "EN": "Run Portfolio Stress Test",
        "PT": "Executar Teste de Estresse da Carteira",
        "ES": "Ejecutar Prueba de Estrés de la Cartera",
    },
    "stress.portfolio_spinner": {
        "EN": "Creating scenarios and pricing portfolio...",
        "PT": "Criando cenários e precificando a carteira...",
        "ES": "Creando escenarios y valorando la cartera...",
    },
    "stress.portfolio_base_case": {
        "EN": "Portfolio Base Case (Aggregated)",
        "PT": "Caso Base da Carteira (Agregado)",
        "ES": "Caso Base de la Cartera (Agregado)",
    },
    "stress.portfolio_results_header": {
        "EN": "Portfolio Stress Results",
        "PT": "Resultados do Teste de Estresse da Carteira",
        "ES": "Resultados de la Prueba de Estrés de la Cartera",
    },
    "stress.portfolio_chart_title": {
        "EN": "Portfolio MtM Change by Scenario",
        "PT": "Variação do MtM da Carteira por Cenário",
        "ES": "Cambio del MtM de la Cartera por Escenario",
    },

    # ------------------------------------------------------------------
    # KRR page
    # ------------------------------------------------------------------
    "krr.page_title": {
        "EN": "Key Rate Risk",
        "PT": "Risco por Vértice",
        "ES": "Riesgo por Vértice",
    },
    "krr.title": {
        "EN": "📐 Key Rate Risk (KRR)",
        "PT": "📐 Risco por Vértice (KRR)",
        "ES": "📐 Riesgo por Vértice (KRR)",
    },
    "krr.caption": {
        "EN": "DV01 decomposition by tenor bucket, per curve, for a single deal or an entire portfolio.",
        "PT": "Decomposição do DV01 por vértice de prazo, por curva, para um deal ou toda uma carteira.",
        "ES": "Descomposición del DV01 por vértice de plazo, por curva, para un deal o toda una cartera.",
    },
    "krr.krr_def_label": {
        "EN": "KRR Greek Definition ID",
        "PT": "ID da Definição KRR (Greek Definition ID)",
        "ES": "ID de Definición KRR (Greek Definition ID)",
    },
    "krr.krr_def_help": {
        "EN": "Bloomberg MARS: Settings → User Settings → Key Rate Risk → Greek Definition ID",
        "PT": "Bloomberg MARS: Settings → User Settings → Key Rate Risk → Greek Definition ID",
        "ES": "Bloomberg MARS: Settings → User Settings → Key Rate Risk → Greek Definition ID",
    },
    "krr.deal_label": {
        "EN": "Deal ID (Bloomberg Deal ID)",
        "PT": "ID do Deal (Bloomberg Deal ID)",
        "ES": "ID del Deal (Bloomberg Deal ID)",
    },
    "krr.portfolio_label": {
        "EN": "Portfolio Name",
        "PT": "Nome da Carteira",
        "ES": "Nombre de la Cartera",
    },
    "krr.run_deal_btn": {
        "EN": "Run Deal KRR",
        "PT": "Calcular KRR do Deal",
        "ES": "Calcular KRR del Deal",
    },
    "krr.run_portfolio_btn": {
        "EN": "Run Portfolio KRR",
        "PT": "Calcular KRR da Carteira",
        "ES": "Calcular KRR de la Cartera",
    },
    "krr.deal_spinner": {
        "EN": "Calculating KRR for deal...",
        "PT": "Calculando KRR do deal...",
        "ES": "Calculando KRR del deal...",
    },
    "krr.portfolio_spinner": {
        "EN": "Calculating KRR for portfolio...",
        "PT": "Calculando KRR da carteira...",
        "ES": "Calculando KRR de la cartera...",
    },
    "krr.deal_results_header": {
        "EN": "Deal KRR Results",
        "PT": "Resultados KRR do Deal",
        "ES": "Resultados KRR del Deal",
    },
    "krr.portfolio_results_header": {
        "EN": "Portfolio KRR Results (Aggregated)",
        "PT": "Resultados KRR da Carteira (Agregado)",
        "ES": "Resultados KRR de la Cartera (Agregado)",
    },
    "krr.chart_title": {
        "EN": "DV01 by Tenor — {curve_label}",
        "PT": "DV01 por Vértice — {curve_label}",
        "ES": "DV01 por Vértice — {curve_label}",
    },
    "krr.col_tenor": {
        "EN": "Tenor",
        "PT": "Vértice",
        "ES": "Vértice",
    },
    "krr.col_dv01": {
        "EN": "DV01",
        "PT": "DV01",
        "ES": "DV01",
    },
    "krr.total_dv01": {
        "EN": "Total DV01",
        "PT": "DV01 Total",
        "ES": "DV01 Total",
    },
    "krr.deal_count": {
        "EN": "Deals",
        "PT": "Deals",
        "ES": "Deals",
    },
    "krr.no_results": {
        "EN": "No KRR results to display.",
        "PT": "Nenhum resultado KRR para exibir.",
        "ES": "No hay resultados KRR para mostrar.",
    },
    "krr.error": {
        "EN": "KRR error: {error}",
        "PT": "Erro KRR: {error}",
        "ES": "Error KRR: {error}",
    },
    "krr.deal_header": {
        "EN": "Deal: {label}",
        "PT": "Deal: {label}",
        "ES": "Deal: {label}",
    },
    "krr.curve_header": {
        "EN": "Curve: {label}",
        "PT": "Curva: {label}",
        "ES": "Curva: {label}",
    },
    # -------------------------------------------------------------------------
    # Async Swaps — SOFR curve bootstrap
    # -------------------------------------------------------------------------
    "async_swaps.page_title": {
        "EN": "Async Swaps",
        "PT": "Swaps Assíncronos",
        "ES": "Swaps Asíncronos",
    },
    "async_swaps.title": {
        "EN": "SOFR Curve Bootstrap",
        "PT": "Bootstrap da Curva SOFR",
        "ES": "Bootstrap de la Curva SOFR",
    },
    "async_swaps.caption": {
        "EN": "Build a zero curve from your own par rates. MARS structures SOFR OIS swaps "
              "concurrently to extract exact payment schedules; Python bootstraps the zero rates.",
        "PT": "Construa uma curva zero a partir das suas próprias taxas par. O MARS estrutura "
              "swaps SOFR OIS de forma concorrente para extrair os cronogramas exatos; "
              "o Python faz o bootstrap das taxas zero.",
        "ES": "Construya una curva cero a partir de sus propias tasas par. MARS estructura "
              "swaps SOFR OIS de forma concurrente para extraer los cronogramas exactos; "
              "Python hace el bootstrap de las tasas cero.",
    },
    "async_swaps.section_inputs": {
        "EN": "Par Rate Inputs",
        "PT": "Taxas Par de Entrada",
        "ES": "Tasas Par de Entrada",
    },
    "async_swaps.label_valuation_date": {
        "EN": "Valuation / Effective Date",
        "PT": "Data de Avaliação / Início",
        "ES": "Fecha de Valoración / Inicio",
    },
    "async_swaps.label_tenor": {
        "EN": "Tenor",
        "PT": "Prazo",
        "ES": "Plazo",
    },
    "async_swaps.label_par_rate": {
        "EN": "Par Rate (%)",
        "PT": "Taxa Par (%)",
        "ES": "Tasa Par (%)",
    },
    "async_swaps.label_include": {
        "EN": "Include",
        "PT": "Incluir",
        "ES": "Incluir",
    },
    "async_swaps.button_bootstrap": {
        "EN": "Bootstrap Curve",
        "PT": "Fazer Bootstrap",
        "ES": "Construir Curva",
    },
    "async_swaps.spinner_schedules": {
        "EN": "Structuring {n} SOFR OIS swaps in parallel via MARS API…",
        "PT": "Estruturando {n} swaps SOFR OIS em paralelo via MARS API…",
        "ES": "Estructurando {n} swaps SOFR OIS en paralelo via MARS API…",
    },
    "async_swaps.spinner_bootstrap": {
        "EN": "Bootstrapping zero curve…",
        "PT": "Calculando curva zero…",
        "ES": "Calculando curva cero…",
    },
    "async_swaps.spinner_s490": {
        "EN": "Fetching S490 from Bloomberg…",
        "PT": "Buscando S490 na Bloomberg…",
        "ES": "Obteniendo S490 de Bloomberg…",
    },
    "async_swaps.tab_zero_rates": {
        "EN": "Zero Rates",
        "PT": "Taxas Zero",
        "ES": "Tasas Cero",
    },
    "async_swaps.tab_discount_factors": {
        "EN": "Discount Factors",
        "PT": "Fatores de Desconto",
        "ES": "Factores de Descuento",
    },
    "async_swaps.tab_detail": {
        "EN": "Detail Table",
        "PT": "Tabela Detalhada",
        "ES": "Tabla Detallada",
    },
    "async_swaps.chart_zero_title": {
        "EN": "SOFR Zero Rates — Bootstrapped vs S490",
        "PT": "Taxas Zero SOFR — Bootstrap vs S490",
        "ES": "Tasas Cero SOFR — Bootstrap vs S490",
    },
    "async_swaps.chart_df_title": {
        "EN": "SOFR Discount Factors — Bootstrapped vs S490",
        "PT": "Fatores de Desconto SOFR — Bootstrap vs S490",
        "ES": "Factores de Descuento SOFR — Bootstrap vs S490",
    },
    "async_swaps.chart_x_label": {
        "EN": "Maturity (years)",
        "PT": "Vencimento (anos)",
        "ES": "Vencimiento (años)",
    },
    "async_swaps.chart_y_zero": {
        "EN": "Zero Rate (%)",
        "PT": "Taxa Zero (%)",
        "ES": "Tasa Cero (%)",
    },
    "async_swaps.chart_y_df": {
        "EN": "Discount Factor",
        "PT": "Fator de Desconto",
        "ES": "Factor de Descuento",
    },
    "async_swaps.legend_bootstrap": {
        "EN": "Bootstrapped (yours)",
        "PT": "Bootstrap (seu)",
        "ES": "Bootstrap (tuyo)",
    },
    "async_swaps.legend_par": {
        "EN": "Par rates (input)",
        "PT": "Taxas par (entrada)",
        "ES": "Tasas par (entrada)",
    },
    "async_swaps.legend_s490": {
        "EN": "S490 — Bloomberg",
        "PT": "S490 — Bloomberg",
        "ES": "S490 — Bloomberg",
    },
    "async_swaps.col_tenor": {
        "EN": "Tenor",
        "PT": "Prazo",
        "ES": "Plazo",
    },
    "async_swaps.col_maturity": {
        "EN": "Maturity Date",
        "PT": "Data de Vencimento",
        "ES": "Fecha de Vencimiento",
    },
    "async_swaps.col_days": {
        "EN": "Days",
        "PT": "Dias",
        "ES": "Días",
    },
    "async_swaps.col_par_rate": {
        "EN": "Par Rate (%)",
        "PT": "Taxa Par (%)",
        "ES": "Tasa Par (%)",
    },
    "async_swaps.col_df_ours": {
        "EN": "P(0,T) Bootstrap",
        "PT": "P(0,T) Bootstrap",
        "ES": "P(0,T) Bootstrap",
    },
    "async_swaps.col_df_s490": {
        "EN": "P(0,T) S490",
        "PT": "P(0,T) S490",
        "ES": "P(0,T) S490",
    },
    "async_swaps.col_z_ours": {
        "EN": "Zero Rate Bootstrap (%)",
        "PT": "Taxa Zero Bootstrap (%)",
        "ES": "Tasa Cero Bootstrap (%)",
    },
    "async_swaps.col_z_s490": {
        "EN": "Zero Rate S490 (%)",
        "PT": "Taxa Zero S490 (%)",
        "ES": "Tasa Cero S490 (%)",
    },
    "async_swaps.col_diff_z": {
        "EN": "Diff (bps)",
        "PT": "Dif. (bps)",
        "ES": "Dif. (bps)",
    },
    "async_swaps.info_idle": {
        "EN": "Enter par rates and click **Bootstrap Curve** to build your zero curve.",
        "PT": "Insira as taxas par e clique em **Fazer Bootstrap** para construir sua curva zero.",
        "ES": "Ingrese las tasas par y haga clic en **Construir Curva** para construir su curva cero.",
    },
    "async_swaps.warning_s490_unavailable": {
        "EN": "S490 comparison unavailable in demo mode.",
        "PT": "Comparação com S490 indisponível no modo demo.",
        "ES": "Comparación con S490 no disponible en modo demo.",
    },
    "async_swaps.error_structuring": {
        "EN": "Structuring error: {error}",
        "PT": "Erro de estruturação: {error}",
        "ES": "Error de estructuración: {error}",
    },
    "async_swaps.error_s490": {
        "EN": "Could not fetch S490: {error}",
        "PT": "Não foi possível buscar S490: {error}",
        "ES": "No se pudo obtener S490: {error}",
    },
    "async_swaps.note_methodology": {
        "EN": "**Methodology** — For each tenor, MARS structures a temporary `IR.OIS.SOFR` swap "
              "and returns the fixed-leg `AccrualSchedule` (payment dates + ACT/360 year fractions). "
              "No Bloomberg curve is used in the bootstrap itself. Zero rates use continuous "
              "compounding ACT/365, the same convention as S490.",
        "PT": "**Metodologia** — Para cada prazo, o MARS estrutura um swap `IR.OIS.SOFR` temporário "
              "e retorna o `AccrualSchedule` da perna fixa (datas de pagamento + frações de ano ACT/360). "
              "Nenhuma curva Bloomberg é usada no bootstrap. As taxas zero usam capitalização contínua "
              "ACT/365, a mesma convenção do S490.",
        "ES": "**Metodología** — Para cada plazo, MARS estructura un swap `IR.OIS.SOFR` temporal "
              "y devuelve el `AccrualSchedule` de la pata fija (fechas de pago + fracciones ACT/360). "
              "No se usa ninguna curva Bloomberg en el bootstrap. Las tasas cero usan capitalización "
              "continua ACT/365, la misma convención que S490.",
    },
    "async_swaps.docs_title": {
        "EN": "Documentation",
        "PT": "Documentação",
        "ES": "Documentación",
    },
    "async_swaps.docs_walkthrough_header": {
        "EN": "Step-by-Step Walkthrough",
        "PT": "Passo a Passo",
        "ES": "Paso a Paso",
    },
    "async_swaps.docs_glossary_header": {
        "EN": "Variable Glossary",
        "PT": "Glossário de Variáveis",
        "ES": "Glosario de Variables",
    },
    "async_swaps.docs_settlement_header": {
        "EN": "T+2 Settlement Bridge",
        "PT": "Ponte de Liquidação T+2",
        "ES": "Puente de Liquidación T+2",
    },
    "async_swaps.docs_math_header": {
        "EN": "Bootstrap Mathematics — Deriving P(0,T) from NPV = 0",
        "PT": "Matemática do Bootstrap — Derivando P(0,T) de NPV = 0",
        "ES": "Matemáticas del Bootstrap — Derivando P(0,T) de NPV = 0",
    },
    "async_swaps.docs_interpolation_header": {
        "EN": "Log-linear Interpolation = Step-Forward (Cont)",
        "PT": "Interpolação Log-linear = Step-Forward (Cont)",
        "ES": "Interpolación Log-lineal = Step-Forward (Cont)",
    },
    "async_swaps.docs_oneday_header": {
        "EN": "1D Special Case — Not Bootstrapped as a Swap",
        "PT": "Caso Especial 1D — Não Bootstrapped como Swap",
        "ES": "Caso Especial 1D — No Bootstrappeado como Swap",
    },
    "async_swaps.docs_zerorates_header": {
        "EN": "Zero Rate Conversion",
        "PT": "Conversão de Taxa Zero",
        "ES": "Conversión de Tasa Cero",
    },
    "async_swaps.docs_tickers_header": {
        "EN": "Par Rate Sources (BLPAPI)",
        "PT": "Fontes de Taxas Par (BLPAPI)",
        "ES": "Fuentes de Tasas Par (BLPAPI)",
    },
    "async_swaps.docs_calendar_header": {
        "EN": "Calendar Engine",
        "PT": "Motor de Calendário",
        "ES": "Motor de Calendario",
    },
    "async_swaps.docs_calendar_body": {
        "EN": (
            "In **live mode**, each tenor's fixed-leg accrual schedule is obtained by structuring "
            "a temporary `IR.OIS.SOFR` deal via the Bloomberg MARS API. All 33 tenor calls run "
            "concurrently via `asyncio.gather` — MARS is used purely as a **calendar engine** "
            "(no pricing, no Bloomberg curve). "
            "In **demo mode**, schedules are loaded from a pre-saved snapshot "
            "(`demo_data/bootstrap/sofr_schedules.json`) — no API calls required."
        ),
        "PT": (
            "No **modo ao vivo**, o cronograma de acumulação da perna fixa de cada prazo é obtido "
            "estruturando um deal temporário `IR.OIS.SOFR` via MARS API da Bloomberg. Todas as 33 "
            "chamadas de prazo são executadas simultaneamente via `asyncio.gather` — o MARS é usado "
            "puramente como um **motor de calendário** (sem precificação, sem curva Bloomberg). "
            "No **modo demo**, os cronogramas são carregados de um snapshot pré-salvo "
            "(`demo_data/bootstrap/sofr_schedules.json`) — sem chamadas de API."
        ),
        "ES": (
            "En **modo en vivo**, el cronograma de acumulación de la pata fija de cada plazo se "
            "obtiene estructurando un deal temporal `IR.OIS.SOFR` a través de la MARS API de Bloomberg. "
            "Las 33 llamadas de plazo se ejecutan concurrentemente mediante `asyncio.gather` — MARS se "
            "usa puramente como un **motor de calendario** (sin valoración, sin curva Bloomberg). "
            "En **modo demo**, los cronogramas se cargan desde un snapshot pre-guardado "
            "(`demo_data/bootstrap/sofr_schedules.json`) — sin llamadas a la API."
        ),
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
