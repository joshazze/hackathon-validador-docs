"""Agente 5 — Validador Deterministico (Python puro, sem IA).

Regras matematicas/sintaticas que IA nao deve nem precisa fazer.
Por que aqui nao tem IA: dito verificador da CNH e algoritmo publico;
faixa de data e aritmetica; nao tem juizo subjetivo a aplicar.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

ANO_MIN_NASCIMENTO = 1900


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _valida_data_nascimento(d: date | None) -> tuple[bool, str | None]:
    if d is None:
        return False, "data de nascimento ausente"
    hoje = date.today()
    if d.year < ANO_MIN_NASCIMENTO:
        return False, f"ano de nascimento improvavel ({d.year})"
    if d > hoje:
        return False, "data de nascimento no futuro"
    idade = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
    if idade > 130:
        return False, f"idade implausivel ({idade} anos)"
    return True, None


def _valida_data_emissao(d: date | None, nasc: date | None) -> tuple[bool, str | None]:
    # data de emissao pode nao estar visivel — nao penalizar nesse caso
    if d is None:
        return True, None
    hoje = date.today()
    if d > hoje:
        return False, "data de emissao no futuro"
    if nasc and d < nasc:
        return False, "data de emissao anterior ao nascimento"
    return True, None


def _valida_digito_cnh(numero: str | None) -> tuple[bool, str | None]:
    """Algoritmo publico do DENATRAN para o numero de registro da CNH.

    11 digitos. Os dois ultimos sao verificadores calculados sobre os 9 primeiros.
    """
    if not numero:
        return False, "numero da CNH ausente"
    apenas_digitos = re.sub(r"\D", "", numero)
    if len(apenas_digitos) != 11:
        return False, f"CNH deve ter 11 digitos, tem {len(apenas_digitos)}"

    base = apenas_digitos[:9]
    dv_informado = apenas_digitos[9:]

    # 1o digito verificador
    soma = sum(int(d) * (9 - i) for i, d in enumerate(base))
    dv1 = soma % 11
    dsc = 0
    if dv1 >= 10:
        dv1 = 0
        dsc = 2

    # 2o digito verificador
    soma = sum(int(d) * (1 + i) for i, d in enumerate(base))
    dv2 = (soma % 11) - dsc
    if dv2 < 0:
        dv2 += 11
    if dv2 >= 10:
        dv2 = 0

    calculado = f"{dv1}{dv2}"
    if calculado != dv_informado:
        return False, f"digito verificador da CNH nao bate (esperado {calculado}, recebido {dv_informado})"
    return True, None


def _valida_formato_numero_rg(numero: str | None) -> tuple[bool, str | None]:
    """RG nao tem padrao nacional — cada UF emite no seu formato.

    So validamos presenca e que tem digitos suficientes pra parecer um RG real.
    """
    if not numero:
        return False, "numero do RG ausente"
    apenas_alfanum = re.sub(r"[^A-Z0-9]", "", numero.upper())
    if len(apenas_alfanum) < 5:
        return False, f"numero do RG muito curto ({len(apenas_alfanum)} caracteres)"
    return True, None


def validate(*, campos: dict[str, Any], doc_type: str) -> dict[str, Any]:
    """Aplica regras deterministicas conforme o tipo de documento."""
    checks: list[dict[str, Any]] = []

    nasc = _parse_date(campos.get("data_nascimento"))
    emissao = _parse_date(campos.get("data_emissao"))

    ok, msg = _valida_data_nascimento(nasc)
    checks.append({"regra": "data_nascimento_plausivel", "ok": ok, "motivo": msg})

    ok, msg = _valida_data_emissao(emissao, nasc)
    checks.append({"regra": "data_emissao_plausivel", "ok": ok, "motivo": msg})

    numero = campos.get("numero_documento")
    if doc_type == "CNH":
        ok, msg = _valida_digito_cnh(numero)
        checks.append({"regra": "digito_verificador_cnh", "ok": ok, "motivo": msg})
    else:
        ok, msg = _valida_formato_numero_rg(numero)
        checks.append({"regra": "formato_numero_rg", "ok": ok, "motivo": msg})

    passados = sum(1 for c in checks if c["ok"])
    total = len(checks)
    score = passados / total if total else 0.0

    return {
        "agente": "validador",
        "score_validacao": score,
        "checks": checks,
        "passados": passados,
        "total": total,
    }
