# Validador Inteligente de Documentos — Parlamento de Agentes

> Hackathon Grupo Fácil — Programa de Estágio IA
> Validação automatizada de RG / CNH para cadastro de plano de saúde

---

## A ideia em uma frase

Em vez de uma única chamada de IA decidindo "aprovo ou rejeito", a solução é um **parlamento de agentes especializados**: cada um opina em uma dimensão específica (legibilidade, anomalia, etc.), e a decisão final é determinística em código puro.

**IA percebe. Código julga.**

---

## Como rodar

```bash
# clonar
git clone https://github.com/<usuario>/hackathon-validador-docs.git
cd hackathon-validador-docs

# instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# precisa de poppler pra converter PDF -> imagem
brew install poppler   # mac
# ou: sudo apt-get install poppler-utils   # linux

# configurar API key
cp .env.example .env
# edite .env e cole sua ANTHROPIC_API_KEY

# subir
python app.py
# abre em http://localhost:5050
```

---

## Arquitetura

```
upload (jpg/png/pdf)
      ↓
[Classificador]  ←  Haiku 4.5  (porteiro: RG / CNH / OUTRO / ILEGIVEL)
      │
      ├── ILEGIVEL → REJEITADO (curto-circuito, economiza 3 chamadas)
      ├── OUTRO    → REVISAR
      └── RG ou CNH
            ↓
[fase paralela — ThreadPoolExecutor]
   ├─ Extrator        ←  Sonnet 4.6  (campos JSON)
   ├─ Legibilidade    ←  Haiku 4.5   (score visual)
   └─ Anomalia        ←  Sonnet 4.6  (sinais de fraude)
            ↓
[deterministicos — Python puro, sem IA]
   ├─ Validador     (digito CNH, datas, plausibilidade)
   └─ Cross-checker (similaridade nome, data nascimento)
            ↓
[Relator] — agrega scores ponderados, aplica thresholds, emite veredito
            ↓
APROVADO ≥ 0.80  |  REVISAR ≥ 0.50  |  REJEITADO < 0.50
```

### Os 7 agentes

| # | Agente | Modelo | Pergunta | Saída |
|---|---|---|---|---|
| 1 | Classificador      | Haiku 4.5  | Que doc é esse?               | tipo + confiança |
| 2 | Extrator           | Sonnet 4.6 | Quais os campos?              | JSON estruturado |
| 3 | Legibilidade       | Haiku 4.5  | Está legível?                 | score 0-1 + problemas |
| 4 | Anomalia           | Sonnet 4.6 | Tem sinal de fraude?          | score 0-1 + suspeitas |
| 5 | Validador          | Python     | Datas/dígito plausíveis?      | bools + score |
| 6 | Cross-checker      | Python     | Bate com o cadastro digitado? | similaridade nome + score |
| 7 | Relator            | Python     | Veredito final                | APROVADO/REVISAR/REJEITADO |

### Por que mix Haiku + Sonnet?

| Tarefa | Modelo | Por quê |
|---|---|---|
| Classificar tipo | Haiku  | Resposta curta, alta confiança, rapidíssimo. Custo ~$0.002/doc |
| Avaliar legibilidade | Haiku | Julgamento grosseiro, OK rápido |
| Extrair campos | Sonnet | Precisão crítica — alucinação aqui propaga pro cross-checker |
| Detectar fraude | Sonnet | Raciocínio sutil sobre pixels, fontes, alinhamento |

Custo médio por documento válido: **~$0.02**. Documento ilegível ou OUTRO custa ~$0.002 (curto-circuito).

---

## Cálculo do score final

```
score_final =
   0.25 × legibilidade
 + 0.20 × extração            (% campos obrigatórios preenchidos)
 + 0.20 × validação           (% regras determinísticas passadas)
 + 0.20 × consistência        (cross-check com cadastro)
 + 0.15 × (1 − anomalia)
```

Os pesos vivem em `parliament/rapporteur.py` — calibráveis sem mexer em prompt.

---

## Estrutura de arquivos

A raiz contém **o modelo (código)**. A pasta `apresentacao/` contém **o material de entrega** (slides + exemplos pra demo).

```
.
├── app.py                       # Flask + orquestrador
├── parliament/                  # MODELO — agentes
│   ├── _client.py               # cliente Anthropic + utils de imagem
│   ├── classifier.py            # agente 1 (Haiku)
│   ├── extractor.py             # agente 2 (Sonnet)
│   ├── legibility.py            # agente 3 (Haiku)
│   ├── anomaly.py               # agente 4 (Sonnet)
│   ├── validator.py             # agente 5 (Python puro)
│   ├── crosscheck.py            # agente 6 (Python puro)
│   └── rapporteur.py            # relator final
├── templates/
│   └── index.html               # drag-and-drop + dashboard
├── scripts/
│   └── gerar_exemplos.py        # regenera os exemplos da apresentação
├── apresentacao/                # ENTREGA — pra banca, não é código de produção
│   ├── slides.md                # fonte da apresentação (Marp)
│   ├── slides.pdf               # apresentação 15min (gerada)
│   └── exemplos/                # 3 documentos sintéticos pra demo
│       ├── 01-rg-valido.jpg
│       ├── 02-cnh-borrado.jpg
│       └── 03-nao-doc.jpg
├── requirements.txt
└── .env.example
```

## Demo (apresentacao/exemplos)

Os 3 exemplos em `apresentacao/exemplos/` cobrem os 3 vereditos possíveis:

| Arquivo | Cadastro esperado | Veredito |
|---|---|---|
| `01-rg-valido.jpg` | Nome: ANTONIA SILVA SANTOS, Nasc: 2002-03-15 | APROVADO |
| `02-cnh-borrado.jpg` | Nome: MARCOS PEREIRA OLIVEIRA, Nasc: 1995-07-22 | REVISAR (legibilidade ruim) |
| `03-nao-doc.jpg` | qualquer | REJEITADO (curto-circuito ILEGIVEL) |

São imagens **sintéticas** geradas por código (`scripts/gerar_exemplos.py`) — sem dados pessoais reais.

## Slides

Gerados a partir de `apresentacao/slides.md` via Marp:

```bash
npm i -g @marp-team/marp-cli
marp apresentacao/slides.md --pdf -o apresentacao/slides.pdf
```

1 agente = 1 arquivo. Cada arquivo é justificado de forma independente.

---

## Reflexão sobre uso da IA

### Onde discordei da IA

| Sugestão original | Decisão | Motivo |
|---|---|---|
| "IA decide aprovar/rejeitar direto" | Rejeitada | IA é complacente; perdia auditabilidade. **Mudança:** IA percebe, código julga. |
| "Validar número de RG por regex nacional" | Rejeitada | RG não tem padrão nacional — cada estado emite diferente. **Mudança:** só valida presença e legibilidade. |
| "Tesseract para OCR local" | Rejeitada (por hora) | Em 2h não dá pra calibrar. **Mudança:** visão multimodal direta. Anotado como limitação de produção. |
| "Confiança declarada pelo modelo (0.95)" | Ignorada | LLMs são otimistas. **Mudança:** score em código, baseado em campos extraídos × regras passadas. |

### Onde concordei

- **Cross-check com cadastro digitado** — é a validação que pega fraude grosseira (mandar doc de outra pessoa).
- **Pré-processar PDF para imagem** antes de chamar o modelo multimodal.
- **Separar percepção em agentes especializados** — uma chamada única é caixa preta.

---

## Pontos fortes

- **Auditável**: cada decisão traz 5 scores e lista de motivos. Analista humano consegue intervir.
- **Calibrável**: pesos do Relator são números num dicionário.
- **Tolerante a falha**: se um agente errar, os outros amortecem.
- **Mix IA + código**: usa IA onde código não consegue (visão), e código onde IA não deve (decisão).
- **Decisão tripartite** (APROVADO / REVISAR / REJEITADO): reconhece o limite da automação.

## Limitações

- Depende de API multimodal paga — em produção, migrar para OCR local + modelo open-source.
- Não detecta fraude sofisticada (deepfake, montagem perfeita) — precisaria de análise de metadados EXIF, detecção de moiré, hash perceptual.
- RG não tem validação determinística do número — depende de integração com base do Serpro.
- Latência ~3-5s — em produção, fila assíncrona com cache por hash.

## Exemplo de erro previsível

**Cenário:** CNH legítima com **reflexo cobrindo o nome**.
- Extrator pode alucinar um nome → cross-checker pega (não bate com cadastro).
- Auditor de Legibilidade detecta o reflexo → score 0.4.
- Validador valida o dígito (que foi lido OK).
- **Veredito final: REVISAR**, não rejeita injustamente. O caso vai pra analista humano com contexto.

---

## Licença

MIT.
