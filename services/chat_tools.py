"""
Risk Assistant — xAI (Grok) chat service with Bloomberg tool calling.

Architecture:
    ChatService  — orchestrator: manages xAI client, tool registry, and the
                   function-calling loop. New tools are added incrementally
                   per the plan in docs/risk_assistant.md.

Tool implementation pattern:
    1. Add JSON schema to _TOOLS list.
    2. Implement _<tool_name>(**kwargs) -> str (returns JSON string).
    3. Add dispatch branch to execute_tool().

Copyright 2026, Bloomberg Finance L.P.
"""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import date, timedelta
from typing import Any

import httpx
from openai import APIConnectionError, APIError, APITimeoutError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from bloomberg.exceptions import (
    IpNotWhitelistedError,
    MarsApiError,
    PricingError,
    StructuringError,
)
from configs.settings import settings
from configs.swaps_config import XCCY_NDSFX_SPECS, XCCY_SWAP_SPECS
from services.bond_reference_service import BondReferenceService
from services.fx_service import FxRateService
from services.outbound_ip import outbound_ip_for_whitelist
from services.swaps_service import SwapPricingService, SwapQuery

log = logging.getLogger(__name__)

_XAI_BASE_URL = "https://api.x.ai/v1"

# Prevent infinite tool-calling loops if the model never returns plain text.
_MAX_CHAT_TOOL_ROUNDS = 16

# Per-request HTTP timeout (each Grok completion is a separate call; MARS runs between calls).
_XAI_HTTP_TIMEOUT = httpx.Timeout(connect=20.0, read=240.0, write=60.0, pool=20.0)

# Available pairs for IR.NDSFX asset swap (fixed vs fixed)
_XCCY_PAIRS = sorted(XCCY_NDSFX_SPECS.keys())

# Bond swap templates (product names — not MARS deal-type strings in the identifier).
_BOND_SWAP_TEMPLATE_LOCAL_EQUIV = "local_equiv_fixed_and_float"
_BOND_SWAP_TEMPLATES: list[str] = [_BOND_SWAP_TEMPLATE_LOCAL_EQUIV]

_SYSTEM_PROMPT = """Você é um assistente especialista em riscos de mercado para LatAm, \
com foco em derivativos de taxa de juros e câmbio (swaps OIS, NDS/XCCY, asset swaps).

Você tem acesso a ferramentas Bloomberg MARS para precificação de swaps, \
análise de sensibilidade (DV01/KRR), stress testing IRRBB e portfólios, \
e à consulta de características de bonds via Bloomberg Desktop API (lookup_bond).

Ao responder:
- Formate números com separadores de milhar e 2 casas decimais
- Explique brevemente o resultado (o que significa o DV01, MtM positivo/negativo)
- Se o usuário não informar datas, use a data de hoje ({today})
- Se o modo demo estiver ativo, avise que os dados são ilustrativos
- Responda preferencialmente em português
- Modo demo ativo: {demo_mode}

REGRA CRÍTICA — Escopo:
Você SOMENTE responde a perguntas que podem ser respondidas usando as ferramentas Bloomberg MARS \
disponíveis (precificação de swaps, asset swaps, dados de bonds Bloomberg, stress, KRR, portfólio). \
Se o usuário **pedir explicitamente**, também é possível guardar um asset swap IR.NDSFX no MARS e obter deal ID.
Se a pergunta estiver fora desse escopo (ex: cotações de ações, notícias, previsões macroeconômicas \
genéricas, explicações teóricas sem cálculo), responda exatamente:
"Não consigo responder isso com as ferramentas Bloomberg disponíveis. \
Por favor, faça uma pergunta sobre precificação de swaps, asset swaps, dados de bonds, stress testing, \
sensibilidade (DV01/KRR) ou portfólios."
Nunca invente dados nem use conhecimento geral quando uma ferramenta deveria ser chamada.

Quando o usuário citar um bond (ISIN, CUSIP ou ticker Bloomberg como AN9676742 Corp), \
chame primeiro lookup_bond; depois **price_asset_swap** com: fixed_rate = ytm_pct/100 (decimal), \
**bond_maturity** = maturity do lookup (YYYY-MM-DD), pay_frequency e day_count **exatamente** \
como devolvidos pelo lookup (já em convenções MARS). A perna USD do swap deve espelhar o bond \
(YTM na fixa, calendário de vencimento e convenções). O contrato é **IR.NDSFX** (fixo vs fixo): \
a API resolve a taxa fixa na perna local (leg 2) que zera o NPV. Nocional USD padrão **100**; \
perna local = nocional × FX spot. **Não** sugira mudar Receive/Pay para "corrigir" ou afinar a \
taxa par local — direção só define quem paga/recebe cada perna, não o valor de mercado da taxa. \
Não mencione DV01, PV01 ou MtM neste fluxo. O JSON pode incluir **solve_raw** (valor MARS antes \
da conversão para %).

**bond_maturity vs tenor_years — sem perguntar ao usuário:** Se lookup_bond devolver o campo \
**maturity** (string YYYY-MM-DD), copie-o **literalmente** para price_asset_swap.**bond_maturity** \
e **não** use tenor_years. **É proibido** pedir confirmação ao usuário entre bond_maturity e \
tenor_years quando maturity já existe no resultado do lookup — chame price_asset_swap na mesma \
sequência, sem parar para confirmar datas. Use **tenor_years** apenas se maturity vier ausente \
ou o lookup tiver erro. Para pedidos como "taxa equivalente em CLP", use **pair=USDCLP** e \
**direction=Receive** (recebe USD fixo, paga CLP fixo) salvo indicação contrária do usuário.

**Pacote bond + moeda local (duas métricas):** Para pedidos que pedem **taxa fixa equivalente** \
e **flutuante local + spread** (ex.: CLP), use a tool **price_bond_swap** com \
**template=`local_equiv_fixed_and_float`** e o **pair** adequado (CLP → USDCLP). O JSON devolve \
dois blocos (**IR_NDSFX** = fixa local par; **IR_NDS** = spread par na perna flutuante em CLP). \
Com **save_to_mars=true**, guarda **ambos** os deals no MARS (live). Para só a fixa-fixa num passo, \
pode usar **lookup_bond** + **price_asset_swap** ou **price_bond_swap** com template acima (o pacote \
inclui sempre as duas métricas).

**Guardar swap / deal ID:** **Não** chame **save_asset_swap_deal** em pedidos normais de precificação, \
asset swap ou análise — nesses casos use só **lookup_bond** e **price_asset_swap** (ou **price_bond_swap** sem save). \
Chame **save_asset_swap_deal** **somente** quando o usuário pedir **explicitamente** para **salvar**, \
**guardar**, **registrar** no MARS, obter **deal ID** / **ID Bloomberg**, ou abrir no **SWPM**/**Terminal** \
o deal **só no produto fixa-fixa (IR.NDSFX)**. Use os **mesmos** argumentos que **price_asset_swap**. \
Se o utilizador quiser **guardar os dois** contratos (fixa-fixa **e** flutuante+spread), use **price_bond_swap** \
com **save_to_mars=true** (dois IDs em **save.IR_NDSFX** e **save.IR_NDS**). \
**É proibido** negar que existe guardar deal quando o usuário pediu explicitamente — a ferramenta existe. \
Se **demo_mode** estiver ativo, a tool devolve erro; explique que o save só funciona com MARS ao vivo. \
Com MARS ao vivo, mostre o(s) **bloomberg_deal_id**.

Se uma ferramenta retornar JSON com error_code IP_NOT_WHITELISTED e outbound_ip_to_whitelist, \
mostre esse IP ao usuário e diga que ele deve ser incluído na allowlist Bloomberg MARS \
para esta rede de saída.
"""

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _fallback_reply_from_tool_content(tool_content: str) -> str:
    """
    When the model returns empty text after tool execution, show something useful
    instead of a blank assistant message.
    """
    raw = tool_content.strip()
    if not raw:
        return ""
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return f"```\n{raw}\n```"

    if not isinstance(data, dict):
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"

    lines: list[str] = []
    if "bloomberg_deal_id" in data:
        lines.append(
            f"**Bloomberg deal ID:** `{data['bloomberg_deal_id']}` — pode abrir no SWPM/Terminal."
        )
    if "error" in data:
        lines.append(f"**Erro:** {data['error']}")
    if "save_requires_live" in data and data.get("save_requires_live"):
        lines.append(
            "Guardar deal só funciona com MARS ao vivo (`demo_mode=False` no servidor)."
        )
    if "local_fixed_par_rate_pct" in data:
        lines.append(
            f"Taxa fixa local (par): **{data['local_fixed_par_rate_pct']}%** "
            f"({data.get('local_currency', '')})."
        )
    # Pacote price_bond_swap (IR_NDSFX + IR.NDS)
    ndsfx_b = data.get("IR_NDSFX")
    if isinstance(ndsfx_b, dict):
        if "local_fixed_par_rate_pct" in ndsfx_b:
            lines.append(
                f"**IR.NDSFX** — taxa fixa local (par): **{ndsfx_b['local_fixed_par_rate_pct']}%** "
                f"({ndsfx_b.get('local_currency', '')})."
            )
        if "error" in ndsfx_b:
            lines.append(f"**IR.NDSFX — erro:** {ndsfx_b['error']}")
    nds_b = data.get("IR_NDS")
    if isinstance(nds_b, dict):
        if "float_leg_spread_par_bp" in nds_b:
            lines.append(
                f"**IR.NDS** — spread par perna flutuante (**{nds_b.get('float_index', '')}**): "
                f"**{nds_b['float_leg_spread_par_bp']}** bp (heurística; validar no Terminal)."
            )
        if "error" in nds_b:
            lines.append(f"**IR.NDS — erro:** {nds_b['error']}")
    save_b = data.get("save")
    if isinstance(save_b, dict):
        for k in ("IR_NDSFX", "IR_NDS"):
            blk = save_b.get(k)
            if isinstance(blk, dict) and blk.get("bloomberg_deal_id"):
                lines.append(f"**Deal ID ({k}):** `{blk['bloomberg_deal_id']}`")
            if isinstance(blk, dict) and blk.get("error"):
                lines.append(f"**Save {k} — erro:** {blk['error']}")
        if save_b.get("save_requires_live"):
            lines.append(
                "Guardar deals só com MARS ao vivo (`demo_mode=False` no servidor)."
            )
    if not lines:
        return (
            "```json\n"
            f"{json.dumps(data, ensure_ascii=False, indent=2)}\n"
            "```"
        )
    return "\n\n".join(lines)


def _last_tool_content_for_fallback(working: list[Any]) -> str | None:
    for m in reversed(working):
        if not isinstance(m, dict):
            continue
        if m.get("role") != "tool":
            continue
        c = m.get("content")
        if c is not None and str(c).strip():
            return str(c)
    return None


def _json_mars_ip_whitelist_error(exc: Exception) -> str:
    detail = str(exc)
    ip     = outbound_ip_for_whitelist(detail)
    hint   = (
        "Peça à Bloomberg para incluir na allowlist MARS o IP indicado em "
        "outbound_ip_to_whitelist (extraído da resposta da API)."
    )
    if not ip:
        hint = (
            "A resposta completa da API está em detail — localize o IP negado na mensagem "
            "e solicite a allowlist desse IP à Bloomberg."
        )
    payload: dict[str, Any] = {
        "error": (
            "Bloomberg MARS recusou a conexão: o IP de saída desta rede "
            "não está na allowlist da API REST."
        ),
        "error_code": "IP_NOT_WHITELISTED",
        "outbound_ip_to_whitelist": ip,
        "detail": detail,
        "hint": hint,
    }
    return json.dumps(payload, ensure_ascii=False)


def _lookup_bond(identifier: str) -> str:
    """Return bond reference data as JSON (BLPAPI or demo)."""
    svc  = BondReferenceService.from_settings()
    data = svc.lookup(identifier)
    return json.dumps(data, default=str)


def _bond_inputs_for_asset_swap(identifier: str) -> dict[str, Any] | str:
    """Parse lookup into fields for asset-swap pricing, or return a JSON error string."""
    raw = _lookup_bond(identifier)
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return json.dumps({"error": "Resposta inválida do lookup de bond."}, ensure_ascii=False)

    if not isinstance(data, dict):
        return json.dumps({"error": "Dados de bond inválidos."}, ensure_ascii=False)

    if data.get("error"):
        err_out: dict[str, Any] = {
            "error": data["error"],
            "identifier": data.get("identifier", identifier),
        }
        for k in ("error_code", "outbound_ip_to_whitelist", "hint", "detail"):
            if k in data:
                err_out[k] = data[k]
        return json.dumps(err_out, ensure_ascii=False, default=str)

    maturity = data.get("maturity")
    if not maturity or not str(maturity).strip():
        return json.dumps(
            {
                "error": (
                    "O lookup não devolveu maturity (YYYY-MM-DD). "
                    "Experimente outro identificador ou use price_asset_swap com tenor_years."
                ),
                "identifier": data.get("identifier", identifier),
            },
            ensure_ascii=False,
        )

    ytm = data.get("ytm_pct")
    if ytm is None:
        return json.dumps(
            {
                "error": "lookup_bond sem ytm_pct; não é possível fixar a perna USD.",
                "identifier": data.get("identifier", identifier),
            },
            ensure_ascii=False,
        )

    try:
        fixed_rate = float(ytm) / 100.0
    except (TypeError, ValueError):
        return json.dumps(
            {"error": f"ytm_pct inválido: {ytm!r}", "identifier": data.get("identifier", identifier)},
            ensure_ascii=False,
        )

    mat_str = str(maturity).strip()[:10]
    return {
        "identifier": data.get("identifier", identifier),
        "name": data.get("name"),
        "maturity": mat_str,
        "fixed_rate": fixed_rate,
        "ytm_pct": float(ytm),
        "pay_frequency": data.get("pay_frequency"),
        "day_count": data.get("day_count"),
    }


def _price_asset_swap_for_bond(
    identifier: str,
    pair: str,
    direction: str = "Receive",
    notional_usd: float = 100.0,
    valuation_date: str | None = None,
) -> str:
    """Lookup bond then price IR.NDSFX in one step (no user confirmation of maturity)."""
    bio = _bond_inputs_for_asset_swap(identifier)
    if isinstance(bio, str):
        return bio

    inner = _price_asset_swap(
        pair=pair,
        direction=direction,
        fixed_rate=bio["fixed_rate"],
        bond_maturity=bio["maturity"],
        tenor_years=None,
        notional_usd=notional_usd,
        valuation_date=valuation_date,
        pay_frequency=bio.get("pay_frequency"),
        day_count=bio.get("day_count"),
    )

    try:
        inner_obj: Any = json.loads(inner)
    except json.JSONDecodeError:
        return inner

    if isinstance(inner_obj, dict) and "error" not in inner_obj:
        inner_obj["bond_identifier"] = bio.get("identifier", identifier)
        if bio.get("name") is not None:
            inner_obj["bond_name"] = bio["name"]
        inner_obj["ytm_pct_used"] = bio["ytm_pct"]
        inner_obj["bond_maturity_used"] = bio["maturity"]
        return json.dumps(inner_obj, default=str, ensure_ascii=False)

    return inner


def _resolve_asset_swap_schedule(
    bond_maturity: str | None,
    tenor_years: float | None,
    valuation_date: str | None,
) -> tuple[dict[str, Any] | None, tuple[date, date, date] | None]:
    """Return (error_dict, None) or (None, (valuation_date, effective, maturity))."""
    val_date  = date.fromisoformat(valuation_date) if valuation_date else date.today()
    effective = val_date + timedelta(days=2)

    if bond_maturity and str(bond_maturity).strip():
        try:
            maturity = date.fromisoformat(str(bond_maturity).strip()[:10])
        except ValueError:
            return ({"error": f"bond_maturity inválido (use YYYY-MM-DD): {bond_maturity!r}"}, None)
        return (None, (val_date, effective, maturity))

    if tenor_years is not None:
        years_int = int(tenor_years)
        months    = round((float(tenor_years) - years_int) * 12)
        mat_year  = effective.year + years_int + (effective.month + months - 1) // 12
        mat_month = (effective.month + months - 1) % 12 + 1
        maturity  = date(mat_year, mat_month, effective.day)
        return (None, (val_date, effective, maturity))

    return (
        {
            "error": (
                "Informe bond_maturity (lookup_bond.maturity, YYYY-MM-DD) ou tenor_years. "
                "Para perna USD alinhada ao bond, use bond_maturity."
            ),
        },
        None,
    )


def _swap_query_for_asset_swap(
    pair: str,
    direction: str,
    fixed_rate: float,
    val_date: date,
    effective: date,
    maturity: date,
    pay_frequency: str | None,
    day_count: str | None,
    notional_usd: float,
    *,
    ndsfx_leg2_fixed_rate: float | None = None,
) -> tuple[SwapQuery, Any, float | None]:
    """Build ``SwapQuery`` for IR.NDSFX asset swap; returns (query, spec, fx_spot)."""
    spec = XCCY_NDSFX_SPECS[pair]
    n_usd = float(notional_usd) if notional_usd and notional_usd > 0 else 100.0
    fx_svc       = FxRateService.from_settings()
    leg2_notional = float(fx_svc.default_leg2_notional(n_usd, spec.currency))
    fx_spot      = fx_svc.get_rate(spec.currency)

    query = SwapQuery(
        key=pair,
        swap_type="NDSFX",
        direction=direction,
        effective_date=effective,
        maturity_date=maturity,
        valuation_date=val_date,
        curve_date=val_date,
        notional=n_usd,
        forward_curve=spec.forward_curve,
        discount_curve=spec.discount_curve,
        float_index="",
        leg1_forward_curve=spec.leg1_forward_curve,
        leg1_discount_curve=spec.leg1_discount_curve,
        pay_frequency=pay_frequency or spec.pay_frequency,
        day_count=day_count or spec.day_count,
        fixed_rate=fixed_rate,
        solve_for="Coupon",
        solve_for_leg=2,
        leg2_notional=leg2_notional,
        ndsfx_leg2_fixed_rate=ndsfx_leg2_fixed_rate,
    )
    return query, spec, fx_spot


def _swap_query_for_nds_bond_spread(
    pair: str,
    direction: str,
    fixed_rate: float,
    val_date: date,
    effective: date,
    maturity: date,
    pay_frequency: str | None,
    day_count: str | None,
    notional_usd: float,
) -> tuple[SwapQuery, Any, float | None]:
    """IR.NDS: USD (base) fixed @ *fixed_rate* vs local float + spread; solve Spread on leg 2."""
    spec = XCCY_SWAP_SPECS[pair]
    n_usd = float(notional_usd) if notional_usd and notional_usd > 0 else 100.0
    fx_svc        = FxRateService.from_settings()
    leg2_notional = float(fx_svc.default_leg2_notional(n_usd, spec.currency))
    fx_spot       = fx_svc.get_rate(spec.currency)

    query = SwapQuery(
        key=pair,
        swap_type="XCCY",
        direction=direction,
        effective_date=effective,
        maturity_date=maturity,
        valuation_date=val_date,
        curve_date=val_date,
        notional=n_usd,
        forward_curve=spec.forward_curve,
        discount_curve=spec.discount_curve,
        float_index=spec.float_index,
        pay_frequency=pay_frequency or spec.pay_frequency,
        day_count=day_count,
        fixed_rate=fixed_rate,
        spread=0.0,
        solve_for="Spread",
        solve_for_leg=2,
        leg1_forward_curve=spec.leg1_forward_curve,
        leg1_discount_curve=spec.leg1_discount_curve,
        leg2_notional=leg2_notional,
    )
    return query, spec, fx_spot


def _nds_spread_solve_display_bp(raw: float) -> float:
    """Heuristic display for MARS spread solve on float leg (compare to Terminal)."""
    return round(float(raw), 6)


def _run_nds_float_spread_for_bond(
    bio: dict[str, Any],
    pair: str,
    direction: str,
    notional_usd: float,
    valuation_date: str | None,
) -> dict[str, Any]:
    """Price IR.NDS with bond YTM on USD fixed leg; solve par spread on local float leg."""
    sched_err, sched = _resolve_asset_swap_schedule(
        bio["maturity"], None, valuation_date,
    )
    if sched_err:
        return dict(sched_err)
    assert sched is not None
    val_date, effective, maturity = sched

    try:
        query, spec, fx_spot = _swap_query_for_nds_bond_spread(
            pair,
            direction,
            float(bio["fixed_rate"]),
            val_date,
            effective,
            maturity,
            bio.get("pay_frequency"),
            bio.get("day_count"),
            notional_usd,
        )
    except KeyError:
        return {"error": f"pair {pair!r} não encontrado em XCCY_SWAP_SPECS."}

    try:
        svc    = SwapPricingService.from_settings()
        result = svc.price(query)
    except IpNotWhitelistedError as exc:
        return json.loads(_json_mars_ip_whitelist_error(exc))
    except StructuringError as exc:
        return {"error": f"Estruturação MARS falhou: {exc}"}
    except PricingError as exc:
        return {"error": f"Precificação MARS falhou: {exc}"}
    except MarsApiError as exc:
        msg = str(exc)
        if "403" in msg or "401" in msg:
            low = msg.lower()
            if "whitelist" in low or "not allowed" in low or "forbidden" in low:
                return json.loads(_json_mars_ip_whitelist_error(exc))
        return {"error": str(exc)}

    if not result.ok:
        return {"error": result.error}
    if result.par_rate is None:
        return {"error": "Solve não devolveu spread par na perna flutuante local."}

    raw = result.solve_raw if result.solve_raw is not None else result.par_rate
    out: dict[str, Any] = {
        "deal_type": "IR.NDS",
        "local_currency": spec.currency,
        "float_index": spec.float_index,
        "float_leg_spread_par_bp": _nds_spread_solve_display_bp(float(raw)),
        "spread_solve_raw": raw,
        "spread_display_note": "Unidade MARS; validar no Terminal (bp).",
        "usd_leg_fixed_rate_decimal": bio["fixed_rate"],
        "leg1_notional_usd": query.notional,
        "leg2_notional_local": query.leg2_notional,
        "valuation_date": str(val_date),
        "effective_date": str(effective),
        "maturity_date": str(maturity),
    }
    if fx_spot is not None:
        out["fx_spot_units_local_per_1_usd"] = fx_spot
    return out


def ndsfx_fixed_rate_to_display_pct(raw: float) -> float:
    """Convert MARS ``solveResult.value.doubleVal`` for IR.NDSFX leg-2 FixedRate to display %.

    Bloomberg does not publish a single unit for all currencies; this matches common behaviour:
    ``|raw| < 1`` → decimal rate (0.0647 → 6.47%); ``|raw| > 100`` → hundredths (6474 → 64.74);
    else treat as percent points. Prefer comparing **solve_raw** with Terminal when in doubt.
    """
    a = abs(raw)
    if a < 1.0:
        return round(raw * 100.0, 6)
    if a > 100.0:
        return round(raw / 100.0, 6)
    return round(raw, 6)


def _price_asset_swap(
    pair: str,
    direction: str,
    fixed_rate: float | None = None,
    bond_maturity: str | None = None,
    tenor_years: float | None = None,
    notional_usd: float = 100.0,
    valuation_date: str | None = None,
    pay_frequency: str | None = None,
    day_count: str | None = None,
) -> str:
    """Asset swap via **IR.NDSFX** (fixed USD vs fixed local): solve local FixedRate (leg 2) for NPV=0.

    *fixed_rate* must be the bond **YTM in decimal** (``ytm_pct/100`` from lookup_bond).
    Prefer **bond_maturity** = ``lookup_bond.maturity`` so the swap ends on the bond date.
    *notional_usd* defaults to 100; leg-2 notional in local ccy = USD notional × FX spot.
    """
    if fixed_rate is None:
        return json.dumps(
            {
                "error": (
                    "fixed_rate é obrigatório: use ytm_pct/100 de lookup_bond (YTM em decimal), "
                    "não o cupom."
                ),
            },
            ensure_ascii=False,
        )

    sched_err, sched = _resolve_asset_swap_schedule(bond_maturity, tenor_years, valuation_date)
    if sched_err:
        return json.dumps(sched_err, ensure_ascii=False)
    assert sched is not None
    val_date, effective, maturity = sched

    query, spec, fx_spot = _swap_query_for_asset_swap(
        pair,
        direction,
        float(fixed_rate),
        val_date,
        effective,
        maturity,
        pay_frequency,
        day_count,
        notional_usd,
        ndsfx_leg2_fixed_rate=None,
    )

    try:
        svc    = SwapPricingService.from_settings()
        result = svc.price(query)
    except IpNotWhitelistedError as exc:
        return _json_mars_ip_whitelist_error(exc)
    except StructuringError as exc:
        return json.dumps(
            {"error": f"Estruturação MARS falhou: {exc}"},
            ensure_ascii=False,
        )
    except PricingError as exc:
        return json.dumps(
            {"error": f"Precificação MARS falhou: {exc}"},
            ensure_ascii=False,
        )
    except MarsApiError as exc:
        msg = str(exc)
        if "403" in msg or "401" in msg:
            low = msg.lower()
            if "whitelist" in low or "not allowed" in low or "forbidden" in low:
                return _json_mars_ip_whitelist_error(exc)
        raise

    if not result.ok:
        return json.dumps({"error": result.error}, ensure_ascii=False)

    if result.par_rate is None:
        return json.dumps(
            {"error": "Solve não retornou taxa fixa local (par_rate)."},
            ensure_ascii=False,
        )

    local_pct = ndsfx_fixed_rate_to_display_pct(result.par_rate)
    n_usd       = query.notional
    leg2_notional = query.leg2_notional
    out: dict[str, Any] = {
        "pair": pair,
        "deal_type": "IR.NDSFX",
        "local_currency": spec.currency,
        "local_fixed_par_rate_pct": local_pct,
        "local_fixed_par_rate_pct_scaling": "heuristic",
        "usd_leg_fixed_rate_decimal": fixed_rate,
        "leg1_notional_usd": n_usd,
        "leg2_notional_local": leg2_notional,
        "valuation_date": str(val_date),
        "effective_date": str(effective),
        "maturity_date": str(maturity),
    }
    if result.solve_raw is not None:
        out["solve_raw"] = result.solve_raw
    if fx_spot is not None:
        out["fx_spot_units_local_per_1_usd"] = fx_spot

    return json.dumps(out, default=str, ensure_ascii=False)


def _save_asset_swap_deal(
    pair: str,
    direction: str,
    fixed_rate: float | None = None,
    bond_maturity: str | None = None,
    tenor_years: float | None = None,
    notional_usd: float = 100.0,
    valuation_date: str | None = None,
    pay_frequency: str | None = None,
    day_count: str | None = None,
) -> str:
    """Price IR.NDSFX asset swap, then save permanently with leg-2 FixedRate = MARS solve value."""
    if settings.demo_mode:
        return json.dumps(
            {
                "error": "Guardar deal no MARS só está disponível com Bloomberg ao vivo (demo_mode=False).",
                "save_requires_live": True,
            },
            ensure_ascii=False,
        )

    if fixed_rate is None:
        return json.dumps(
            {
                "error": (
                    "fixed_rate é obrigatório: use ytm_pct/100 de lookup_bond (YTM em decimal), "
                    "não o cupom."
                ),
            },
            ensure_ascii=False,
        )

    sched_err, sched = _resolve_asset_swap_schedule(bond_maturity, tenor_years, valuation_date)
    if sched_err:
        return json.dumps(sched_err, ensure_ascii=False)
    assert sched is not None
    val_date, effective, maturity = sched

    query, spec, fx_spot = _swap_query_for_asset_swap(
        pair,
        direction,
        float(fixed_rate),
        val_date,
        effective,
        maturity,
        pay_frequency,
        day_count,
        notional_usd,
        ndsfx_leg2_fixed_rate=None,
    )

    try:
        svc = SwapPricingService.from_settings()
        result = svc.price(query)
    except IpNotWhitelistedError as exc:
        return _json_mars_ip_whitelist_error(exc)
    except StructuringError as exc:
        return json.dumps(
            {"error": f"Estruturação MARS falhou: {exc}"},
            ensure_ascii=False,
        )
    except PricingError as exc:
        return json.dumps(
            {"error": f"Precificação MARS falhou: {exc}"},
            ensure_ascii=False,
        )
    except MarsApiError as exc:
        msg = str(exc)
        if "403" in msg or "401" in msg:
            low = msg.lower()
            if "whitelist" in low or "not allowed" in low or "forbidden" in low:
                return _json_mars_ip_whitelist_error(exc)
        raise

    if not result.ok:
        return json.dumps({"error": result.error}, ensure_ascii=False)

    raw_leg2 = result.solve_raw if result.solve_raw is not None else result.par_rate
    if raw_leg2 is None:
        return json.dumps(
            {"error": "Solve não retornou taxa fixa local; não é possível guardar o deal."},
            ensure_ascii=False,
        )

    query_saved = replace(query, ndsfx_leg2_fixed_rate=float(raw_leg2))

    try:
        deal_id = svc.save_deal(query_saved)
    except IpNotWhitelistedError as exc:
        return _json_mars_ip_whitelist_error(exc)
    except StructuringError as exc:
        return json.dumps({"error": str(exc), "error_code": "STRUCTURING"}, ensure_ascii=False)
    except MarsApiError as exc:
        msg = str(exc)
        if "403" in msg or "401" in msg:
            low = msg.lower()
            if "whitelist" in low or "not allowed" in low or "forbidden" in low:
                return _json_mars_ip_whitelist_error(exc)
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    out: dict[str, Any] = {
        "bloomberg_deal_id": deal_id,
        "note": (
            "Deal IR.NDSFX guardado com FixedRate na perna local (leg 2) igual ao valor "
            "retornado pelo solve do MARS (solve_raw), coerente com price_asset_swap."
        ),
        "pair": pair,
        "deal_type": "IR.NDSFX",
        "local_currency": spec.currency,
        "solve_raw_applied_to_leg2": raw_leg2,
        "leg1_notional_usd": query_saved.notional,
        "leg2_notional_local": query_saved.leg2_notional,
        "maturity_date": str(maturity),
        "effective_date": str(effective),
        "valuation_date": str(val_date),
    }
    if fx_spot is not None:
        out["fx_spot_units_local_per_1_usd"] = fx_spot

    return json.dumps(out, default=str, ensure_ascii=False)


def _price_bond_swap(
    identifier: str,
    pair: str,
    template: str,
    direction: str = "Receive",
    notional_usd: float = 100.0,
    valuation_date: str | None = None,
    save_to_mars: bool = False,
) -> str:
    """Lookup bond, price IR.NDSFX (local fixed par) + IR.NDS (float local spread par); optional dual save."""
    if template != _BOND_SWAP_TEMPLATE_LOCAL_EQUIV:
        return json.dumps(
            {
                "error": (
                    f"template não suportado: {template!r}. "
                    f"Opções: {_BOND_SWAP_TEMPLATES!r}."
                ),
            },
            ensure_ascii=False,
        )
    if pair not in XCCY_NDSFX_SPECS or pair not in XCCY_SWAP_SPECS:
        return json.dumps(
            {"error": f"pair {pair!r} não tem specs NDSFX+NDS (XCCY)."},
            ensure_ascii=False,
        )

    bio = _bond_inputs_for_asset_swap(identifier)
    if isinstance(bio, str):
        return bio

    ndsfx_json = _price_asset_swap(
        pair=pair,
        direction=direction,
        fixed_rate=bio["fixed_rate"],
        bond_maturity=bio["maturity"],
        tenor_years=None,
        notional_usd=notional_usd,
        valuation_date=valuation_date,
        pay_frequency=bio.get("pay_frequency"),
        day_count=bio.get("day_count"),
    )
    try:
        ndsfx_obj: Any = json.loads(ndsfx_json)
    except json.JSONDecodeError:
        ndsfx_obj = {"error": "Resposta NDSFX inválida.", "raw": ndsfx_json}

    nds_obj = _run_nds_float_spread_for_bond(
        bio, pair, direction, notional_usd, valuation_date,
    )

    out: dict[str, Any] = {
        "template": template,
        "pair": pair,
        "bond_identifier": bio["identifier"],
        "bond_name": bio.get("name"),
        "ytm_pct_used": bio["ytm_pct"],
        "bond_maturity_used": bio["maturity"],
        "IR_NDSFX": ndsfx_obj,
        "IR_NDS": nds_obj,
    }

    if save_to_mars:
        save_out: dict[str, Any] = {}
        if settings.demo_mode:
            save_out["save_requires_live"] = True
            save_out["note"] = "Guardar deals só com MARS ao vivo (demo_mode=False)."
        else:
            ndsfx_ok = isinstance(ndsfx_obj, dict) and "error" not in ndsfx_obj
            if ndsfx_ok:
                try:
                    sx = json.loads(
                        _save_asset_swap_deal(
                            pair=pair,
                            direction=direction,
                            fixed_rate=bio["fixed_rate"],
                            bond_maturity=bio["maturity"],
                            tenor_years=None,
                            notional_usd=notional_usd,
                            valuation_date=valuation_date,
                            pay_frequency=bio.get("pay_frequency"),
                            day_count=bio.get("day_count"),
                        )
                    )
                    save_out["IR_NDSFX"] = {
                        "bloomberg_deal_id": sx.get("bloomberg_deal_id"),
                        "error": sx.get("error"),
                    }
                except Exception as exc:
                    save_out["IR_NDSFX"] = {"error": str(exc)}
            else:
                save_out["IR_NDSFX"] = {"error": "Precificação NDSFX com erro; save omitido."}

            nds_ok = isinstance(nds_obj, dict) and "error" not in nds_obj
            if nds_ok:
                try:
                    sched_err, sched = _resolve_asset_swap_schedule(
                        bio["maturity"], None, valuation_date,
                    )
                    if sched_err or sched is None:
                        save_out["IR_NDS"] = {"error": "Calendário inválido para save NDS."}
                    else:
                        val_date, effective, maturity = sched
                        nds_q, _, _ = _swap_query_for_nds_bond_spread(
                            pair,
                            direction,
                            float(bio["fixed_rate"]),
                            val_date,
                            effective,
                            maturity,
                            bio.get("pay_frequency"),
                            bio.get("day_count"),
                            notional_usd,
                        )
                        svc = SwapPricingService.from_settings()
                        res2 = svc.price(nds_q)
                        raw_sp = res2.solve_raw if res2.solve_raw is not None else res2.par_rate
                        if raw_sp is not None and res2.ok:
                            nds_saved = replace(nds_q, spread=float(raw_sp))
                            deal_id = svc.save_deal(nds_saved)
                            save_out["IR_NDS"] = {"bloomberg_deal_id": deal_id}
                        else:
                            save_out["IR_NDS"] = {"error": "Sem spread resolvido para gravar NDS."}
                except StructuringError as exc:
                    save_out["IR_NDS"] = {"error": str(exc)}
                except MarsApiError as exc:
                    save_out["IR_NDS"] = {"error": str(exc)}
                except Exception as exc:
                    save_out["IR_NDS"] = {"error": str(exc)}
            else:
                err = nds_obj.get("error") if isinstance(nds_obj, dict) else "NDS indisponível"
                save_out["IR_NDS"] = {"error": err}

        out["save"] = save_out

    return json.dumps(out, default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

_ASSET_SWAP_TOOL_PROPERTIES: dict[str, Any] = {
    "pair": {
        "type": "string",
        "enum": _XCCY_PAIRS,
        "description": "Par: USDCOP, USDBRL, USDMXN, USDCLP, USDPEN, USDEUR.",
    },
    "notional_usd": {
        "type": "number",
        "description": (
            "Nocional na perna USD. Padrão 100. A perna local = este valor × "
            "FX spot (unidades de moeda local por 1 USD)."
        ),
    },
    "bond_maturity": {
        "type": "string",
        "description": (
            "Obrigatório quando lookup_bond devolveu maturity: copiar o valor exato YYYY-MM-DD "
            "do campo maturity do JSON de lookup_bond. Não pedir confirmação ao usuário."
        ),
    },
    "tenor_years": {
        "type": "number",
        "description": (
            "Só usar se lookup_bond NÃO tiver maturity (erro ou campo ausente). "
            "Se maturity existir no lookup, omitir tenor_years e usar bond_maturity."
        ),
    },
    "direction": {
        "type": "string",
        "enum": ["Receive", "Pay"],
        "description": (
            "Receive = recebe USD fixo, paga local fixo. "
            "Pay = paga USD fixo, recebe local fixo."
        ),
    },
    "fixed_rate": {
        "type": "number",
        "description": (
            "Obrigatório. YTM do bond em decimal (ex: 0.0559) — ytm_pct/100 "
            "de lookup_bond (YLD_YTM_MID), não o cupom, na perna USD fixa."
        ),
    },
    "pay_frequency": {
        "type": "string",
        "description": (
            "Frequência de pagamento do bond (Leg 1), ex: SemiAnnual. "
            "Obter de lookup_bond.pay_frequency."
        ),
    },
    "day_count": {
        "type": "string",
        "description": (
            "Day count do bond, ex: 30/360, ACT/360. Obter de lookup_bond.day_count."
        ),
    },
    "valuation_date": {
        "type": "string",
        "description": "YYYY-MM-DD. Padrão: hoje.",
    },
}

_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_bond",
            "description": (
                "Busca características de um título: YTM mid (ytm_pct), cupom, vencimento (maturity YYYY-MM-DD), "
                "moeda, frequência de pagamento, day count, outstanding via Bloomberg Desktop API. "
                "Para asset swap: ytm_pct/100 → fixed_rate; maturity → bond_maturity em price_asset_swap, sem confirmar com o usuário. "
                "ISIN, CUSIP ou ticker (ex: AN9676742 Corp)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Ticker Bloomberg (ex: AN9676742 Corp), ISIN ou CUSIP.",
                    },
                },
                "required": ["identifier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "price_bond_swap",
            "description": (
                "Bond USD + cruzamento LatAm num único passo: faz lookup do título e devolve **duas** "
                "precificações MARS — **IR_NDSFX** (taxa fixa local par que zera NPV com YTM na USD fixa) "
                "e **IR_NDS** (spread par na perna flutuante local, ex. CLICP em USDCLP). "
                "Template: **`local_equiv_fixed_and_float`**. pair **USDCLP** para taxa equivalente em CLP. "
                "**save_to_mars=true** (só live) grava **dois** deals e devolve dois bloomberg_deal_id sob save.IR_NDSFX / save.IR_NDS."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Ticker Bloomberg (ex: AN9676742 Corp), ISIN ou CUSIP.",
                    },
                    "pair": {
                        "type": "string",
                        "enum": _XCCY_PAIRS,
                        "description": "Par XCCY: USDCLP, USDCOP, …",
                    },
                    "template": {
                        "type": "string",
                        "enum": _BOND_SWAP_TEMPLATES,
                        "description": "Produto: local_equiv_fixed_and_float = fixa local + spread flutuante.",
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["Receive", "Pay"],
                        "description": "Receive = recebe USD fixo (YTM), paga local. Padrão Receive.",
                    },
                    "notional_usd": {
                        "type": "number",
                        "description": "Nocional perna USD. Padrão 100.",
                    },
                    "valuation_date": {
                        "type": "string",
                        "description": "YYYY-MM-DD. Padrão hoje.",
                    },
                    "save_to_mars": {
                        "type": "boolean",
                        "description": "Se true e MARS live, grava NDSFX e NDS e devolve deal IDs em save.*",
                    },
                },
                "required": ["identifier", "pair", "template"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "price_asset_swap",
            "description": (
                "Asset swap **IR.NDSFX** (fixo USD vs fixo local) no MARS: com YTM do bond na "
                "perna USD, resolve a **taxa fixa na perna local** (leg 2) que zera o NPV. "
                "Fluxo: (1) lookup_bond (2) price_asset_swap na mesma conversa. "
                "fixed_rate = ytm_pct/100; bond_maturity = maturity do lookup (YYYY-MM-DD) quando existir — "
                "nunca perguntar ao usuário maturity vs tenor. pair USDCLP para CLP. direction Receive por defeito."
            ),
            "parameters": {
                "type": "object",
                "properties": _ASSET_SWAP_TOOL_PROPERTIES,
                "required": ["pair", "direction", "fixed_rate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_asset_swap_deal",
            "description": (
                "**Somente** se o usuário pedir explicitamente salvar/guardar/registrar o deal ou "
                "obter deal ID (SWPM/Terminal). **Não** usar para precificação ou consulta geral — "
                "para isso use price_asset_swap. Guarda no MARS o IR.NDSFX equivalente a "
                "price_asset_swap e devolve bloomberg_deal_id. Mesmos parâmetros que price_asset_swap. "
                "Requer MARS ao vivo; em demo retorna erro."
            ),
            "parameters": {
                "type": "object",
                "properties": _ASSET_SWAP_TOOL_PROPERTIES,
                "required": ["pair", "direction", "fixed_rate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "price_float_asset_swap",
            "description": "Calcula o spread de asset swap flutuante usando o template IR.NDS. Converte a taxa fixa de um bond USD numa perna NDS variável numa outra moeda local e resolve qual o spread par (NPV=0).",
            "parameters": {
                "type": "object",
                "properties": {
                    "identifier": { "type": "string", "description": "Ticker Bloomberg ou CUSIP/ISIN." },
                    "pair":       { "type": "string", "description": "Ex: USDCOP, USDBRL." },
                    "direction":  { "type": "string", "enum": ["Receive", "Pay"] },
                    "notional_usd": { "type": "number" },
                    "valuation_date": { "type": "string" }
                },
                "required": ["identifier", "pair"]
            }
        }
    }

]


def _price_swap(
    swap_key: str,
    swap_type: str,
    direction: str,
    tenor_years: float,
    notional: float,
    fixed_rate: float | None = None,
    valuation_date: str | None = None,
) -> str:
    from datetime import date, timedelta
    from configs.swaps_config import OIS_SWAP_SPECS, XCCY_SWAP_SPECS
    from services.fx_service import FxRateService
    from services.swaps_service import SwapPricingService, SwapQuery
    val_date = date.fromisoformat(valuation_date) if valuation_date else date.today()
    effective = val_date + timedelta(days=2)
    years_int = int(tenor_years)
    months    = round((float(tenor_years) - years_int) * 12)
    mat_year  = effective.year + years_int + (effective.month + months - 1) // 12
    mat_month = (effective.month + months - 1) % 12 + 1
    maturity  = date(mat_year, mat_month, effective.day)

    if swap_type == "OIS":
        if swap_key not in OIS_SWAP_SPECS:
            return json.dumps({"error": f"OIS swap_key inválido: {swap_key}"}, ensure_ascii=False)
        spec = OIS_SWAP_SPECS[swap_key]
        query = SwapQuery(
            key=swap_key,
            swap_type=swap_type,
            direction=direction,
            effective_date=effective,
            maturity_date=maturity,
            valuation_date=val_date,
            curve_date=val_date,
            notional=notional,
            forward_curve=spec.forward_curve,
            discount_curve=spec.discount_curve,
            float_index=spec.float_index,
            pay_frequency=spec.pay_frequency,
            day_count=spec.day_count,
            fixed_rate=fixed_rate,
            solve_for="Coupon" if fixed_rate is None else "None",
        )
    elif swap_type == "XCCY":
        if swap_key not in XCCY_SWAP_SPECS:
            return json.dumps({"error": f"XCCY swap_key inválido: {swap_key}"}, ensure_ascii=False)
        spec = XCCY_SWAP_SPECS[swap_key]
        fx_svc        = FxRateService.from_settings()
        leg2_notional = float(fx_svc.default_leg2_notional(notional, spec.currency))
        query = SwapQuery(
            key=swap_key,
            swap_type=swap_type,
            direction=direction,
            effective_date=effective,
            maturity_date=maturity,
            valuation_date=val_date,
            curve_date=val_date,
            notional=notional,
            forward_curve=spec.forward_curve,
            discount_curve=spec.discount_curve,
            float_index=spec.float_index,
            pay_frequency=spec.pay_frequency,
            day_count=spec.day_count,
            fixed_rate=fixed_rate,
            solve_for="Coupon" if fixed_rate is None else "None",
            leg1_forward_curve=spec.leg1_forward_curve,
            leg1_discount_curve=spec.leg1_discount_curve,
            leg2_notional=leg2_notional,
        )
    else:
        return json.dumps({"error": f"swap_type inválido: {swap_type}"}, ensure_ascii=False)

    try:
        svc = SwapPricingService.from_settings()
        res = svc.price(query)
        if not res.ok:
            return json.dumps({"error": res.error}, ensure_ascii=False)
        out = {
            "MktVal": res.metrics.get("MktValPortCcy") or res.metrics.get("MktVal"),
            "DV01": res.metrics.get("DV01PortCcy") or res.metrics.get("DV01"),
            "PV01": res.metrics.get("PV01"),
            "par_rate_solved": res.par_rate,
            "valuation_date": str(val_date),
            "effective_date": str(effective),
            "maturity_date": str(maturity),
        }
        return json.dumps(out, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _run_stress_test(
    deal_id: str,
    rate_shift_bp: float,
    currency: str,
    valuation_date: str | None = None,
) -> str:
    from datetime import date
    from services.stress_service import StressService, StressScenario
    val_date = date.fromisoformat(valuation_date) if valuation_date else date.today()
    scenario = StressScenario(
        name=f"Shift {rate_shift_bp}bp",
        tenor_shifts={"1D": rate_shift_bp, "1W": rate_shift_bp, "1M": rate_shift_bp, "3M": rate_shift_bp, "6M": rate_shift_bp, "1Y": rate_shift_bp, "2Y": rate_shift_bp, "5Y": rate_shift_bp, "10Y": rate_shift_bp, "20Y": rate_shift_bp, "30Y": rate_shift_bp},
        currency=currency
    )
    try:
        svc = StressService.from_settings()
        res = svc.run_stress_test(deal_id, [scenario], val_date)
        if not res.ok:
            return json.dumps({"error": res.error}, ensure_ascii=False)
        out = {
            "base_metrics": res.base_metrics,
            "scenario_results": [{"name": s.name, "metrics": s.metrics} for s in res.scenario_results]
        }
        return json.dumps(out, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _run_krr(
    target_type: str,
    id_or_name: str,
    valuation_date: str | None = None,
) -> str:
    from datetime import date
    from services.risk_service import KrrService
    val_date = date.fromisoformat(valuation_date) if valuation_date else date.today()
    try:
        svc = KrrService.from_settings()
        if target_type == "deal":
            res = svc.run_deal_krr(id_or_name, val_date)
        elif target_type == "portfolio":
            res = svc.run_portfolio_krr(id_or_name, val_date)
        else:
            return json.dumps({"error": f"Invalid target_type: {target_type}"}, ensure_ascii=False)

        if not res.ok:
            return json.dumps({"error": res.error}, ensure_ascii=False)

        agg = res.aggregate_by_curve()
        return json.dumps({"krr_dv01_by_curve_and_tenor": agg}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _price_portfolio(
    portfolio_name: str,
    valuation_date: str | None = None,
) -> str:
    from datetime import date
    from services.portfolio_service import PortfolioPricingService
    val_date = date.fromisoformat(valuation_date) if valuation_date else date.today()
    try:
        svc = PortfolioPricingService.from_settings()
        res = svc.price_portfolio(portfolio_name, val_date)
        if not res.ok:
            return json.dumps({"error": res.error}, ensure_ascii=False)
        out = {
            "aggregate": res.aggregate,
            "deals": res.deals
        }
        return json.dumps(out, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def _price_float_asset_swap(
    identifier: str,
    pair: str,
    direction: str = "Receive",
    notional_usd: float = 100.0,
    valuation_date: str | None = None,
) -> str:
    """Implementação dedicada do asset swap flutuante (IR.NDS) usando o serviço de swaps."""
    bio = _bond_inputs_for_asset_swap(identifier)
    if isinstance(bio, str):
        return bio
    res = _run_nds_float_spread_for_bond(bio, pair, direction, notional_usd, valuation_date)
    return json.dumps(res, ensure_ascii=False)

def execute_tool(name: str, args: dict[str, Any]) -> str:
    """Dispatch a tool call to the correct implementation."""
    if name == "lookup_bond":
        return _lookup_bond(**args)
    if name == "price_bond_swap":
        return _price_bond_swap(**args)
    if name == "price_asset_swap":
        return _price_asset_swap(**args)
    if name == "save_asset_swap_deal":
        return _save_asset_swap_deal(**args)
    if name == "price_swap":
        return _price_swap(**args)
    if name == "run_stress_test":
        return _run_stress_test(**args)
    if name == "run_krr":
        return _run_krr(**args)
    if name == "price_portfolio":
        return _price_portfolio(**args)
    if name == "price_float_asset_swap":
        return _price_float_asset_swap(**args)
    raise ValueError(f"Unknown tool: {name!r}")
