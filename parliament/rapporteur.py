"""Relator — agrega pareceres dos agentes e emite veredito.

NAO usa IA. E justamente o ponto da arquitetura: a decisao final
e deterministica, auditavel, calibravel. A IA opina em dimensoes;
o codigo julga.
"""
from __future__ import annotations

from typing import Any, Literal

Veredito = Literal["APROVADO", "REVISAR", "REJEITADO"]

PESOS = {
    "legibilidade": 0.25,
    "extracao": 0.20,
    "validacao": 0.20,
    "consistencia": 0.20,
    "anomalia": 0.15,  # entra como (1 - score_anomalia)
}

THRESHOLD_APROVADO = 0.80
THRESHOLD_REVISAR = 0.50


def _veredito(score: float) -> Veredito:
    if score >= THRESHOLD_APROVADO:
        return "APROVADO"
    if score >= THRESHOLD_REVISAR:
        return "REVISAR"
    return "REJEITADO"


def relate(
    *,
    classificador: dict[str, Any],
    extrator: dict[str, Any],
    legibilidade: dict[str, Any],
    anomalia: dict[str, Any],
    validador: dict[str, Any],
    crosschecker: dict[str, Any],
) -> dict[str, Any]:
    score_legibilidade = legibilidade["score_legibilidade"]
    score_extracao = extrator["score_extracao"]
    score_validacao = validador["score_validacao"]
    score_consistencia = crosschecker["score_consistencia"]
    score_anomalia = anomalia["score_anomalia"]

    score_final = (
        PESOS["legibilidade"] * score_legibilidade
        + PESOS["extracao"] * score_extracao
        + PESOS["validacao"] * score_validacao
        + PESOS["consistencia"] * score_consistencia
        + PESOS["anomalia"] * (1.0 - score_anomalia)
    )
    score_final = round(score_final, 3)

    veredito = _veredito(score_final)

    motivos: list[str] = []
    if score_legibilidade < 0.6:
        motivos.extend(legibilidade.get("problemas", []))
    if score_anomalia > 0.4:
        motivos.extend(anomalia.get("suspeitas", []))
    for c in validador.get("checks", []):
        if not c["ok"] and c.get("motivo"):
            motivos.append(c["motivo"])
    for c in crosschecker.get("checks", []):
        if not c["ok"] and c.get("motivo"):
            motivos.append(c["motivo"])

    if not motivos and veredito == "APROVADO":
        motivos.append("Documento aprovado em todas as dimensoes avaliadas.")
    elif not motivos:
        motivos.append("Sem problemas especificos detectados, mas score abaixo do limite.")

    return {
        "veredito": veredito,
        "score_final": score_final,
        "scores": {
            "legibilidade": round(score_legibilidade, 3),
            "extracao": round(score_extracao, 3),
            "validacao": round(score_validacao, 3),
            "consistencia": round(score_consistencia, 3),
            "anomalia_invertida": round(1.0 - score_anomalia, 3),
        },
        "motivos": motivos,
        "tipo_documento": classificador["tipo"],
    }
