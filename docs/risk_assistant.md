# Risk Assistant — Documentação do Chatbot xAI

## Visão Geral

O Risk Assistant é um chatbot integrado ao app MARS API LatAm que usa a **API xAI (Grok)**
com **function calling** para acionar os serviços Bloomberg MARS já existentes.
O usuário conversa em linguagem natural; o Grok decide qual tool chamar e o app
executa o cálculo via Bloomberg MARS.

---

## Arquitetura

```
Usuário (chat UI)
    │
    ▼
pages/risk_assistant.py          ← UI Streamlit (st.chat_message / st.chat_input)
    │
    ▼
services/chat_service.py         ← Orquestrador: cliente xAI + loop de tools
services/chat_tools.py           ← Definições de tools, prompt e dispatch (`execute_tool`)
    │
    ├─► BondReferenceService     ← lookup_bond (BLPAPI)
    ├─► SwapPricingService        ← price_swap / price_asset_swap
    ├─► StressService             ← run_stress_test
    ├─► KrrService                ← run_krr
    └─► PortfolioPricingService   ← price_portfolio
              │
              ▼
        Bloomberg MARS API
```

---

## Configuração

### Variáveis de Ambiente (`.env`)

```
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxx
XAI_MODEL=grok-3                     # opcional, padrão: grok-3
```

### `configs/settings.py` (campos adicionados na Etapa 1)

```python
xai_api_key: str = Field(default="", description="xAI API key")
xai_model:   str = Field(default="grok-3", description="xAI model name")
```

### Cliente xAI

A API xAI é **compatível com o SDK `openai`**:

```python
from openai import OpenAI
client = OpenAI(
    api_key=settings.xai_api_key,
    base_url="https://api.x.ai/v1",
)
```

---

## Ferramentas (Tools)

### Ordem de Implementação

| # | Tool | Status | Serviço |
|---|------|--------|---------|
| 1 | Fundação (sem tools) | ✅ concluída | — |
| 2a | `lookup_bond` | ✅ concluída | `BondReferenceService` BLPAPI |
| 2b | `price_asset_swap` | ✅ concluída | `SwapPricingService` IR.NDSFX |
| 2c | `price_bond_swap` | ✅ concluída | `SwapPricingService` IR.NDSFX + IR.NDS |
| 3 | `price_swap` | ⬜ pendente | `SwapPricingService` OIS/XCCY |
| 4 | `run_stress_test` | ⬜ pendente | `StressService` |
| 5 | `run_krr` | ⬜ pendente | `KrrService` |
| 6 | `price_portfolio` | ⬜ pendente | `PortfolioPricingService` |
| 7 | Polimento | ⬜ pendente | — |

---

### Tool: `lookup_bond`

**Propósito:** Obter **YTM mid** (`ytm_pct`, campo Bloomberg `YLD_YTM_MID`), cupom de referência, vencimento, moeda, frequência de pagamento e convenção de day count
via Bloomberg Desktop API (`ReferenceDataRequest`), para alimentar `price_asset_swap`.

**Uso no asset swap:** `fixed_rate = ytm_pct / 100` (decimal) — **não** usar o cupom como taxa fixa USD.

**Parâmetros:** `identifier` — ticker Bloomberg (ex: `AN9676742 Corp`), ISIN ou CUSIP.

**Implementação:** `services/bond_reference_service.py` — `BondReferenceService.from_settings().lookup(identifier)`.

Em modo demo (`settings.demo_mode`), apenas o snapshot `AN9676742 CORP` está disponível.

---

### Tool: `price_asset_swap`

**Propósito:** Precificar um **asset swap** no MARS como **IR.NDSFX** (perna USD **fixa** vs perna local **fixa**): com a **YTM** do bond na perna USD (`fixed_rate` = `ytm_pct/100` em decimal, de `lookup_bond`), o solve encontra a **taxa fixa na perna local** (leg 2) que zera o NPV.

- **Contrato:** `swap_type="NDSFX"`, specs em `configs.swaps_config.XCCY_NDSFX_SPECS`, deal type MARS `IR.NDSFX`.
- **Perna USD alinhada ao bond:** `fixed_rate` = YTM decimal; `pay_frequency` e `day_count` como devolvidos pelo `lookup_bond` (mapeamento BLPAPI → MARS em [`configs/mars_bbg_mappings.py`](configs/mars_bbg_mappings.py)); **`bond_maturity`** = `lookup_bond.maturity` (YYYY-MM-DD) para o vencimento do swap — preferir a calcular só `tenor_years`.
- **Nocionais:** perna USD = `notional_usd` (padrão **100**); perna local = USD nocional × FX spot.
- **Solve:** `solve_for="Coupon"`, `solve_for_leg=2`. Resposta inclui **`solve_raw`** (double MARS) e `local_fixed_par_rate_pct` (heurística documentada em `ndsfx_fixed_rate_to_display_pct`).
- **Sem** `MktVal`, `DV01`, `PV01` neste fluxo. **Não** sugerir mudar `direction` para “ajustar” a taxa par local.

**lookup_bond** devolve `ytm_pct`, `maturity`, `pay_frequency`, `day_count` (MARS), e opcionalmente `cpn_freq_raw`, `day_cnt_des_raw`.

**Pares disponíveis:**

| Par | Deal Type | Uso |
|-----|-----------|-----|
| `USDCOP` | IR.NDSFX | USD fixo vs COP fixo |
| `USDBRL` | IR.NDSFX | USD fixo vs BRL fixo |
| `USDMXN` | IR.NDSFX | USD fixo vs MXN fixo |
| `USDCLP` | IR.NDSFX | USD fixo vs CLP fixo |
| `USDPEN` | IR.NDSFX | USD fixo vs PEN fixo (convenção de pernas conforme spec) |
| `USDEUR` | IR.NDSFX | USD fixo vs EUR fixo |

**Schema JSON (resumo):**

```json
{
  "name": "price_asset_swap",
  "description": "IR.NDSFX: YTM na perna USD; resolve taxa fixa local (leg 2). fixed_rate obrigatório (ytm_pct/100).",
  "parameters": {
    "type": "object",
    "properties": {
      "pair":         { "type": "string", "enum": ["USDCOP","USDBRL","USDMXN","USDCLP","USDPEN","USDEUR"] },
      "notional_usd": { "type": "number", "description": "Opcional; padrão 100 USD. Local = USD × FX." },
      "bond_maturity": { "type": "string", "description": "YYYY-MM-DD = lookup_bond.maturity (preferido)" },
      "tenor_years":  { "type": "number", "description": "Alternativa se bond_maturity omitido" },
      "direction":    { "type": "string", "enum": ["Receive","Pay"] },
      "fixed_rate":   { "type": "number", "description": "YTM em decimal (ytm_pct/100), obrigatório" },
      "pay_frequency": { "type": "string" },
      "day_count":     { "type": "string" },
      "valuation_date": { "type": "string" }
    },
    "required": ["pair", "direction", "fixed_rate"]
  }
}
```

**Implementação (referência):** `services/chat_tools._price_asset_swap` — `XCCY_NDSFX_SPECS`, `FxRateService.default_leg2_notional`, `SwapQuery` com `maturity_date` a partir de `bond_maturity` ou `tenor_years`; `SwapResult.solve_raw` exposto no JSON.

### Tool: `save_asset_swap_deal`

**Propósito:** Guardar no MARS o mesmo **IR.NDSFX** que `price_asset_swap` e devolver o **Bloomberg deal ID** (`bloomberg_deal_id`) para abrir no SWPM/Terminal.

- **Parâmetros:** iguais a `price_asset_swap` (incl. `bond_maturity` preferido).
- **Fluxo:** `price()` para obter o solve; depois `SwapPricingService.save_deal` com `SwapQuery.ndsfx_leg2_fixed_rate` = `solve_raw` (perna 2 fixa CLP gravada com o valor MARS, não placeholder 0,01).
- **Modo demo:** não disponível (`save_requires_live` no JSON de erro).

**Implementação:** `services/chat_tools._save_asset_swap_deal` → `SwapPricingService.save_deal`.

---

### Tool: `price_bond_swap`

**Propósito:** Para um **bond USD** (ticker/ISIN) e um **par XCCY** (ex. `USDCLP`), executar **lookup interno** e devolver **duas** precificações MARS no mesmo JSON:

| Chave JSON | Deal MARS | Métrica |
|------------|-----------|---------|
| `IR_NDSFX` | `IR.NDSFX` | Taxa **fixa** local (leg 2) par com YTM na perna USD fixa — mesmo racional que `price_asset_swap`. |
| `IR_NDS` | `IR.NDS` | **Spread** par na perna **flutuante** local (ex. índice `CLICP` em `USDCLP`) com USD fixo @ YTM. |

- **Template:** `local_equiv_fixed_and_float` (único valor suportado neste pacote; futuros templates podem acrescentar enum sem mudar o nome da tool).
- **Parâmetros:** `identifier`, `pair`, `template` (obrigatórios); `direction` (default `Receive`), `notional_usd`, `valuation_date`, **`save_to_mars`** (bool).
- **`save_to_mars=true` (MARS live):** grava **dois** deals — NDSFX com `ndsfx_leg2_fixed_rate` = solve, NDS com `spread` = solve do spread. Em **demo**, `save` inclui `save_requires_live`.
- **Demo:** snapshots `*_NDSFX_5Y.json` e `*_NDS_SPREAD.json` em `demo_data/swaps/` por par.
- **Nota de validação:** Em primeiro deploy **live**, confirmar no Terminal/SWPM o solve **`Spread`** na leg 2 de `IR.NDS` com USD fixo (e, se necessário, `GET /marswebapi/v1/dealSchema` com `tail=IR.NDS` para o parâmetro Spread).

**Implementação:** [`services/chat_tools.py`](services/chat_tools.py) — `_price_bond_swap`, `_run_nds_float_spread_for_bond`, `SwapLiveRepository.price` com `solve_for=Spread` quando `swap_type=XCCY` e `fixed_rate` preenchido ([`services/swaps_service.py`](services/swaps_service.py)).

---

### Tool: `price_swap`

**Propósito:** Precificar qualquer swap OIS ou XCCY (MtM, DV01, PV01, taxa par).

**Instrumentos OIS:** `COP` (IBR), `USD` (SOFR), `BRL` (CDI), `MXN`, `CLP`, `EUR`

**Schema JSON:**

```json
{
  "name": "price_swap",
  "description": "Precifica um swap OIS ou XCCY. Retorna MktVal, DV01, PV01 e taxa par.",
  "parameters": {
    "type": "object",
    "properties": {
      "swap_key":   { "type": "string", "description": "Ex: COP, USD, BRL, USDCOP, USDBRL" },
      "swap_type":  { "type": "string", "enum": ["OIS","XCCY"] },
      "direction":  { "type": "string", "enum": ["Receive","Pay"] },
      "tenor_years":{ "type": "number" },
      "notional":   { "type": "number" },
      "fixed_rate": { "type": "number", "description": "Se omitido, resolve taxa par." },
      "valuation_date": { "type": "string" }
    },
    "required": ["swap_key", "swap_type", "direction", "tenor_years", "notional"]
  }
}
```

---

### Tool: `run_stress_test`

**Propósito:** Rodar cenários de stress IRRBB num deal Bloomberg salvo.
Cria SHOC scenarios no MARS, precifica, deleta os scenarios.

**Schema JSON:**

```json
{
  "name": "run_stress_test",
  "description": "Roda cenários de stress de taxa de juros num deal Bloomberg. Retorna MktVal base e por cenário.",
  "parameters": {
    "type": "object",
    "properties": {
      "deal_id":       { "type": "string", "description": "Bloomberg Deal ID (ex: SLLVJ42Q Corp)" },
      "rate_shift_bp": { "type": "number", "description": "Shift paralelo em bp (ex: +200 ou -200)" },
      "currency":      { "type": "string", "description": "Moeda da curva a shiftar (ex: USD, COP, BRL)" },
      "valuation_date":{ "type": "string" }
    },
    "required": ["deal_id", "rate_shift_bp", "currency"]
  }
}
```

**Nota de implementação:** O `StressService` já suporta shifts por tenor via `IRRBB_MATRIX`.
Para shifts paralelos simples pedidos pelo usuário, aplicar o mesmo shift em todos os tenors.

---

### Tool: `run_krr`

**Propósito:** Calcular Key Rate Risk (DV01 por bucket de tenor) de um deal ou portfólio.

**Schema JSON:**

```json
{
  "name": "run_krr",
  "description": "Calcula a sensibilidade DV01 por tenor (Key Rate Risk) de um deal ou portfólio Bloomberg.",
  "parameters": {
    "type": "object",
    "properties": {
      "target_type": { "type": "string", "enum": ["deal","portfolio"] },
      "id_or_name":  { "type": "string", "description": "Deal ID ou nome do portfólio" },
      "valuation_date": { "type": "string" }
    },
    "required": ["target_type", "id_or_name"]
  }
}
```

---

### Tool: `price_portfolio`

**Propósito:** Precificar um portfólio Bloomberg completo (MtM total, DV01, por deal).

**Schema JSON:**

```json
{
  "name": "price_portfolio",
  "description": "Precifica um portfólio Bloomberg. Retorna MtM total, DV01 e métricas por deal.",
  "parameters": {
    "type": "object",
    "properties": {
      "portfolio_name": { "type": "string", "description": "Nome do portfólio Bloomberg (ex: MARS_VIBE_CODING)" },
      "valuation_date": { "type": "string" }
    },
    "required": ["portfolio_name"]
  }
}
```

---

## System Prompt

```
Você é um assistente especialista em riscos de mercado para LatAm, com foco em
derivativos de taxa de juros e câmbio (swaps OIS, NDS/XCCY, asset swaps).

Você tem acesso a ferramentas Bloomberg MARS para precificação de swaps,
análise de sensibilidade (DV01/KRR), stress testing IRRBB e portfólios.

Ao responder:
- Formate números com separadores de milhar e 2 casas decimais
- Explique brevemente o resultado (o que significa o DV01, MtM positivo/negativo)
- Se o usuário não informar datas, use a data de hoje
- Se o modo demo estiver ativo, avise que os dados são ilustrativos
- Responda preferencialmente em português
```

---

## Estrutura de Arquivos

```
services/
  chat_service.py          ← cliente xAI + loop
  chat_tools.py            ← tools + execute_tool
  bond_reference_service.py ← BLPAPI: lookup de bonds
pages/
  risk_assistant.py        ← NOVO: UI de chat Streamlit
configs/
  settings.py              ← MODIFICADO: + xai_api_key, xai_model
docs/
  risk_assistant.md        ← ESTE ARQUIVO
.cursor/rules/
  risk-assistant.mdc       ← CRIAR na Etapa 1 (Agent mode)
requirements.txt           ← MODIFICADO: + openai>=1.0
```

---

## Padrão de Loop de Chat

```python
# pages/risk_assistant.py — loop principal
if prompt := st.chat_input("Pergunte sobre riscos..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        response = chat_service.chat(st.session_state.messages)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

```python
# services/chat_service.py — loop de tool calling
def chat(self, messages: list[dict]) -> str:
    while True:
        resp = self._client.chat.completions.create(
            model=self._model, messages=messages, tools=_TOOLS
        )
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                result = self.execute_tool(tc.function.name, json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        else:
            return msg.content
```

---

## Demo Mode

Quando `settings.demo_mode = True`:
- `SwapPricingService`, `StressService`, `KrrService`, `PortfolioPricingService` retornam dados pré-gravados
- `BondReferenceService` usa snapshots fixos (ex.: `AN9676742 Corp`) em vez do terminal
- O chat funciona **sem Bloomberg ativo**
- Avisar o usuário no system prompt que os dados são ilustrativos

---

## Histórico de Mudanças

| Data | Etapa | Descrição |
|------|-------|-----------|
| 2026-04-03 | 1 | Fundação: ChatService, UI chat, xAI client, system prompt, política de escopo |
| 2026-04-03 | 2 | `price_asset_swap`: bond USD → moeda LatAm via XCCY NDS no MARS |
| 2026-04-03 | 2b | `lookup_bond` + BLPAPI; YTM (`YLD_YTM_MID`) para perna USD; chips AN9676742 Corp |
