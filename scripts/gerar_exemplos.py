"""Gera imagens sinteticas de teste para a demo do hackathon.

NAO usar imagens de documentos reais — dados pessoais, LGPD.
Estes 3 arquivos sao espécimen pedagogicos: claros, controlados, reproduziveis.

Saida:
  exemplos/01-rg-valido.jpg    → deve ser APROVADO se cadastro bater
  exemplos/02-cnh-borrado.jpg  → deve cair em REVISAR (baixa legibilidade)
  exemplos/03-nao-doc.jpg      → curto-circuito ILEGIVEL/OUTRO → REJEITADO/REVISAR
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent.parent / "exemplos"
OUT.mkdir(parents=True, exist_ok=True)


def _carrega_fonte(size: int) -> ImageFont.FreeTypeFont:
    candidatos = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidatos:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def gera_rg_valido():
    """RG sintetico, legivel, dados ficticios. Cadastro com mesmo nome -> APROVADO."""
    w, h = 1000, 630
    img = Image.new("RGB", (w, h), (240, 238, 228))
    d = ImageDraw.Draw(img)

    # moldura
    d.rectangle([10, 10, w - 10, h - 10], outline=(80, 80, 100), width=3)

    # cabecalho
    d.rectangle([10, 10, w - 10, 80], fill=(45, 65, 110))
    d.text((30, 28), "REPUBLICA FEDERATIVA DO BRASIL", fill="white", font=_carrega_fonte(18))
    d.text((30, 50), "GOVERNO DE MINAS GERAIS — SECRETARIA DE SEGURANCA PUBLICA",
           fill="white", font=_carrega_fonte(13))

    # titulo
    d.text((30, 100), "CARTEIRA DE IDENTIDADE", fill=(45, 65, 110), font=_carrega_fonte(28))

    # area da foto
    d.rectangle([30, 150, 230, 400], outline=(120, 120, 120), width=2)
    d.text((90, 260), "FOTO", fill=(160, 160, 160), font=_carrega_fonte(22))

    # campos
    campos = [
        ("REGISTRO GERAL", "MG-12.345.678"),
        ("NOME", "ANTONIA SILVA SANTOS"),
        ("FILIACAO", "MARIA DA SILVA / JOAO SANTOS"),
        ("DATA DE NASCIMENTO", "15/03/2002"),
        ("NATURALIDADE", "BELO HORIZONTE / MG"),
        ("DOC. ORIGEM", "C.NASC. LV-43 FL-12"),
        ("DATA DE EXPEDICAO", "10/06/2018"),
    ]
    y = 155
    for label, valor in campos:
        d.text((260, y), label, fill=(100, 100, 100), font=_carrega_fonte(12))
        d.text((260, y + 16), valor, fill=(20, 20, 20), font=_carrega_fonte(18))
        y += 50

    # rodape
    d.text((30, h - 50), "SSP/MG", fill=(45, 65, 110), font=_carrega_fonte(20))
    d.text((30, h - 28), "VALIDA EM TODO O TERRITORIO NACIONAL",
           fill=(80, 80, 80), font=_carrega_fonte(11))

    img.save(OUT / "01-rg-valido.jpg", "JPEG", quality=92)
    print("ok 01-rg-valido.jpg")


def gera_cnh_borrada():
    """CNH com forte desfoque — simula foto tremida."""
    w, h = 1000, 630
    img = Image.new("RGB", (w, h), (230, 235, 245))
    d = ImageDraw.Draw(img)

    d.rectangle([10, 10, w - 10, h - 10], outline=(60, 80, 120), width=3)
    d.rectangle([10, 10, w - 10, 90], fill=(30, 60, 120))
    d.text((30, 35), "CARTEIRA NACIONAL DE HABILITACAO", fill="white", font=_carrega_fonte(20))

    d.rectangle([30, 110, 230, 360], outline=(120, 120, 120), width=2)
    d.text((90, 220), "FOTO", fill=(160, 160, 160), font=_carrega_fonte(22))

    campos = [
        ("NOME", "MARCOS PEREIRA OLIVEIRA"),
        ("DATA NASCIMENTO", "22/07/1995"),
        ("N. REGISTRO", "12345678900"),
        ("CATEGORIA", "AB"),
        ("VALIDADE", "10/03/2028"),
        ("1A HABILITACAO", "05/08/2014"),
        ("ORGAO EMISSOR", "DETRAN/MG"),
    ]
    y = 115
    for label, valor in campos:
        d.text((260, y), label, fill=(80, 80, 80), font=_carrega_fonte(12))
        d.text((260, y + 16), valor, fill=(20, 20, 20), font=_carrega_fonte(18))
        y += 50

    # aplica desfoque pesado pra simular foto borrada
    img = img.filter(ImageFilter.GaussianBlur(radius=4.5))
    img.save(OUT / "02-cnh-borrado.jpg", "JPEG", quality=70)
    print("ok 02-cnh-borrado.jpg")


def gera_nao_doc():
    """Imagem que nao e documento — gradient + texto aleatorio."""
    w, h = 800, 600
    img = Image.new("RGB", (w, h), (200, 220, 240))
    d = ImageDraw.Draw(img)
    for i in range(h):
        c = int(200 - (i / h) * 60)
        d.line([(0, i), (w, i)], fill=(c, c + 20, c + 40))
    d.text((180, 250), "FOTO DE PAISAGEM", fill="white", font=_carrega_fonte(36))
    d.text((220, 310), "(nao e documento)", fill=(220, 220, 220), font=_carrega_fonte(20))
    img.save(OUT / "03-nao-doc.jpg", "JPEG", quality=88)
    print("ok 03-nao-doc.jpg")


if __name__ == "__main__":
    gera_rg_valido()
    gera_cnh_borrada()
    gera_nao_doc()
    print(f"3 exemplos gerados em {OUT}")
