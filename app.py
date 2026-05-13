"""App Flask — orquestrador do Parlamento de Agentes.

Endpoint:
- GET  /          : HTML drag-and-drop
- POST /validate  : recebe imagem + dados do cadastro, devolve veredito JSON

O orquestrador roda o Classificador primeiro (porteiro Haiku) e,
se o documento for valido, dispara os 3 agentes IA em paralelo via threads.
Os validadores deterministicos rodam em sequencia (sao instantaneos).
"""
from __future__ import annotations

import io
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from parliament._client import prepare_image
from parliament import (
    anomaly,
    classifier,
    crosscheck,
    extractor,
    legibility,
    rapporteur,
    validator,
)

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


def _pdf_para_imagem_bytes(raw: bytes) -> tuple[bytes, str]:
    """Converte primeira pagina de um PDF em JPEG."""
    from pdf2image import convert_from_bytes

    images = convert_from_bytes(raw, first_page=1, last_page=1, dpi=200)
    if not images:
        raise ValueError("PDF sem paginas legiveis")
    buf = io.BytesIO()
    images[0].save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def _preparar_image_block(file_storage) -> dict[str, Any]:
    raw = file_storage.read()
    mime = file_storage.mimetype or "image/jpeg"
    if mime == "application/pdf" or file_storage.filename.lower().endswith(".pdf"):
        raw, mime = _pdf_para_imagem_bytes(raw)
    return prepare_image(raw, mime)


def _resposta_curto_circuito(
    tipo_doc: str,
    classificador_out: dict[str, Any],
    veredito: str,
    motivo: str,
) -> dict[str, Any]:
    """Quando o porteiro recusa, montamos uma resposta minima — economiza chamadas."""
    return {
        "veredito": veredito,
        "tipo_documento": tipo_doc,
        "score_final": 0.0,
        "scores": {},
        "motivos": [motivo],
        "curto_circuito": True,
        "agentes": {"classificador": classificador_out},
        "tempos_ms": {},
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/validate")
def validate():
    tempos: dict[str, float] = {}
    t0 = time.perf_counter()

    if "documento" not in request.files:
        return jsonify({"erro": "envie o arquivo no campo 'documento'"}), 400
    file = request.files["documento"]
    if not file.filename:
        return jsonify({"erro": "arquivo sem nome"}), 400

    cadastro = {
        "nome_completo": request.form.get("nome_completo", "").strip(),
        "data_nascimento": request.form.get("data_nascimento", "").strip(),
    }
    if not cadastro["nome_completo"] or not cadastro["data_nascimento"]:
        return jsonify({"erro": "preencha nome e data de nascimento do cadastro"}), 400

    try:
        image_block = _preparar_image_block(file)
    except Exception as e:
        return jsonify({"erro": f"falha ao processar imagem: {e}"}), 400
    tempos["preprocesso"] = (time.perf_counter() - t0) * 1000

    # Fase 1: porteiro
    t1 = time.perf_counter()
    cls = classifier.classify(image_block)
    tempos["classificador"] = (time.perf_counter() - t1) * 1000

    if cls["tipo"] == "ILEGIVEL":
        return jsonify(
            _resposta_curto_circuito(
                "ILEGIVEL",
                cls,
                "REJEITADO",
                "Documento ilegivel — reenvie uma foto mais nitida.",
            )
            | {"tempos_ms": tempos}
        )
    if cls["tipo"] == "OUTRO":
        return jsonify(
            _resposta_curto_circuito(
                "OUTRO",
                cls,
                "REVISAR",
                f"Documento nao identificado como RG ou CNH ({cls.get('justificativa', '')}). Enviar a analista.",
            )
            | {"tempos_ms": tempos}
        )

    # Fase 2: paralelo (Extrator + Legibilidade + Anomalia)
    t2 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_ext = pool.submit(extractor.extract, image_block, cls["tipo"])
        f_leg = pool.submit(legibility.audit, image_block)
        f_ano = pool.submit(anomaly.detect, image_block)
        ext = f_ext.result()
        leg = f_leg.result()
        ano = f_ano.result()
    tempos["fase_paralela"] = (time.perf_counter() - t2) * 1000

    # Fase 3: deterministicos
    t3 = time.perf_counter()
    val = validator.validate(campos=ext["campos"], doc_type=cls["tipo"])
    crs = crosscheck.crosscheck(cadastro=cadastro, extraido=ext["campos"])
    tempos["deterministicos"] = (time.perf_counter() - t3) * 1000

    # Fase 4: relator
    veredito = rapporteur.relate(
        classificador=cls,
        extrator=ext,
        legibilidade=leg,
        anomalia=ano,
        validador=val,
        crosschecker=crs,
    )

    tempos["total"] = (time.perf_counter() - t0) * 1000

    return jsonify(
        veredito | {
            "agentes": {
                "classificador": cls,
                "extrator": ext,
                "legibilidade": leg,
                "anomalia": ano,
                "validador": val,
                "crosschecker": crs,
            },
            "cadastro_enviado": cadastro,
            "tempos_ms": {k: round(v, 1) for k, v in tempos.items()},
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
