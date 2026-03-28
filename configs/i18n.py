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
        "EN": "Deal Information",
        "PT": "Informações de Deals",
        "ES": "Información de Deals",
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
