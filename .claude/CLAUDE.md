# Spot Taxas B3

> Pipeline Python que extrai taxas spot de câmbio do arquivo diário da B3, compara com a PTAX do BACEN e gera uma planilha Excel.

---

## Contexto do Projeto

**Problema:** A B3 e o BACEN publicam taxas de câmbio diariamente em formatos distintos (arquivo posicional e API OData). Conciliar essas fontes manualmente é trabalhoso e sujeito a erros de escala/paridade.

**Solução:** Pipeline local Python que automatiza o download, parse, transformação e comparação de moedas (atualmente 42, com cobertura ampliável conforme novos códigos aparecem no arquivo da B3), gerando uma planilha Excel pronta para uso em precificação, conciliação, auditoria e compliance cambial.

**Stack:** Python 3.12 + pandas + openpyxl + requests — gerenciado com **uv**

**Mantenedor:** Guilherme Ramos — projeto solo

---

## Restrições Absolutas

| Restrição | Regra |
|-----------|-------|
| Gerenciador de pacotes | **SEMPRE** `uv add <pacote>` — NUNCA `pip install` |
| Execução de scripts | `uv run python <script>` |
| Ambiente local | Não instalar nada diretamente no ambiente local |
| Fonte de verdade | `instruction/PRD_Taxas_Spot_B3.md` |

---

## Arquitetura do Pipeline

```text
[B3] ID{AAMMDD}.ex_  →  baixar (zip→SFX→Indic.txt em memória)  →  Indic.txt
                                                    ↓
                                               parse posicional
                                               decode campo numérico (R2)
                                               filtrar data D (R1)
                                               mapear instrumento → moeda (sufixo, R8)
                                               USD primeiro → paridade GBP/NZD/CNY (R4/R5)
                                                    ↓
[BACEN] CotacaoMoedaDia (1 chamada/moeda)  →  filtrar "Fechamento PTAX"  →  PTAX por moeda
                                                    ↓
                            merge B3 + PTAX  →  calcular spread  →  alerta se >20% (R10)
                                                    ↓
                                          taxas_spot_b3_{AAAAMMDD}.xlsx
```

> Implementação real validada em produção (2026-06-07) — divergiu do desenho original do
> PRD em vários pontos (ver [instruction/REGRAS_DO_PIPELINE.md](../instruction/REGRAS_DO_PIPELINE.md)
> e `.claude/sdd/archive/PIPELINE_CORE/SHIPPED_20260607.md`).

---

## Contexto de Negócio

### Entidades

| Entidade | Descrição |
|----------|-----------|
| `Indic.txt` | Arquivo posicional B3, ~3.600–3.800 linhas, publicado ~19h BRT |
| Taxa Spot | Cotação para liquidação imediata (D+0 ou D+1) |
| PTAX | Taxa de câmbio de referência oficial do Banco Central |
| Data D | Data mais recente do arquivo — usar sempre D, nunca D-1 |
| Paridade | Razão entre duas moedas (ex: GBP/USD = 1.35) |

### 42 moedas cobertas

USD, EUR, AUD, GBP, CAD, CHF, JPY, NZD, SEK, NOK, DKK, ZAR, MXN, ARS, CLP, TRY, CNY, CNH, RUB,
AED, BOB, COP, CRC, CZK, HKD, HUF, IDR, INR, KWD, MYR, PEN, PHP, PLN, PYG, QAR, RON, SAR, SGD,
THB, TWD, UYU, VND

> A lista é curada manualmente em `src/config.py` (`INSTRUMENTOS`) — não existe campo no
> arquivo da B3 que identifique "isto é uma moeda", então cada novo código precisa ser
> validado contra dados reais (escala plausível, ausência de alerta de divergência) antes
> de entrar na config. Ver R8 e a seção "Pontos de atenção" em REGRAS_DO_PIPELINE.md.

### Regras de negócio críticas

1. Usar **data D** (mais recente do arquivo), nunca D-1
2. **Indicador de casas decimais:** últimos 2 dígitos do campo numérico definem a escala — o valor decodificado já é a taxa final (não existe divisor extra por moeda)
3. ~~EUR tem divisor especial 10^7~~ — **revisada**: não há divisor algum (premissa do PRD original estava errada, ver REGRAS_DO_PIPELINE.md R3)
4. **NZD e GBP** dependem do USD spot — processar USD primeiro (`cotação = USD_spot × paridade`)
5. **CNY** é paridade inversa: `USD_BRL ÷ paridade_CNY_USD`
6. PTAX ausente → `null` (não é erro fatal — várias moedas não têm boletim de fechamento no BACEN)
7. Instrumento ausente → `null` + alerta `[WARN]`
8. Busca de instrumento por **sufixo completo** (não match exato, não truncar no `-`) — nomes podem mudar
9. Dias não úteis → recuar para o último dia útil (calendário via BrasilAPI)
10. Divergência > 20% B3 vs PTAX → gerar alerta `[WARN]`

> Detalhamento completo, em linguagem simples e com exemplos reais de execução, em
> [instruction/REGRAS_DO_PIPELINE.md](../instruction/REGRAS_DO_PIPELINE.md).

### Janela de disponibilidade

| Fonte | Disponível | Endpoint real |
|-------|-----------|----------|
| PTAX BACEN fechamento | ~18h BRT | `CotacaoMoedaDia(moeda,dataCotacao)` — 1 chamada por moeda, filtro `tipoBoletim == "Fechamento PTAX"` |
| Arquivo B3 `.ex_` | ~19h BRT | `b3.com.br/pesquisapregao/download` (zip aninhado: zip → SFX → `Indic.txt`) |
| Calendário de feriados | — | BrasilAPI `brasilapi.com.br/api/feriados/v1/{ano}` (endpoint do BACEN não existe) |
| Execução ideal | Após 19h BRT | — |

---

## Estrutura do Projeto

```text
Spot_Taxas_B3/
├── instruction/
│   ├── PRD_Taxas_Spot_B3.md      # PRD original — fonte de verdade do escopo
│   └── REGRAS_DO_PIPELINE.md     # Guia das 10 regras de negócio em linguagem simples
├── src/                           # Código-fonte do pipeline
│   ├── __init__.py
│   ├── config.py                  # Instrumento (dataclass) + mapa das 42 moedas → instrumento B3
│   ├── calendario.py              # resolver_data_util — calendário de feriados via BrasilAPI
│   ├── downloader.py              # baixar_e_extrair — download .ex_ + extração zip→SFX→Indic.txt
│   ├── parser.py                  # parsear, _decode_valor — parse posicional + paridades
│   ├── ptax.py                    # buscar — PTAX BACEN (CotacaoMoedaDia, 1 chamada/moeda)
│   ├── calculator.py              # calcular — merge B3 + PTAX e cálculo de spread
│   └── exporter.py                # gerar_excel — geração da planilha final
├── data/
│   ├── raw/                       # Arquivos .ex_ e Indic.txt baixados (não versionado)
│   └── output/                    # Planilhas Excel geradas (não versionado)
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_calculator.py
│   └── test_calendario.py
├── main.py                        # Entrypoint: uv run python main.py
├── pyproject.toml                 # Dependências: pandas, openpyxl, requests, pytest, ruff
├── .python-version                # Python 3.12 fixado
├── uv.lock                        # Lockfile determinístico — commitar
└── .claude/
    ├── CLAUDE.md                  # Este arquivo
    ├── kb/                        # Knowledge Base (pandas, openpyxl, requests, uv)
    ├── agents/domain/             # b3-pipeline-developer, spot-taxas-b3-expert
    └── sdd/archive/PIPELINE_CORE/ # Ciclo SDD arquivado (DEFINE/DESIGN/BUILD/SHIPPED)
```

---

## Workflows de Desenvolvimento

### AgentSpec 4.2 (Spec-Driven Development)

```text
/brainstorm → /define → /design → /build → /ship
  (Opus)      (Opus)    (Opus)   (Sonnet)  (Haiku)
```

### Dev Loop

```bash
/dev "Quero construir X"
/dev tasks/PROMPT_FEATURE.md
```

---

## Diretrizes de Uso de Agentes

| Categoria | Agentes | Quando usar |
|-----------|---------|-------------|
| **Domínio** | `b3-pipeline-developer` | Parse B3, download, decodificação, paridades |
| **Domínio** | `spot-taxas-b3-expert` | Decisões arquiteturais, regras de negócio |
| **Workflow** | brainstorm, define, design, build, ship | Construir features com SDD |
| **Qualidade** | code-reviewer, test-generator | Revisar e testar código |
| **Exploração** | codebase-explorer | Mapear estrutura atual |

---

## Comandos

| Comando | Propósito |
|---------|-----------|
| `/brainstorm` | Explorar ideias |
| `/define` | Capturar requisitos |
| `/design` | Criar arquitetura |
| `/build` | Executar implementação |
| `/ship` | Arquivar feature concluída |
| `/dev` | Dev Loop |
| `/create-kb` | Criar domínio de KB |
| `/review` | Revisão de código |
| `/sync-context` | Atualizar esta seção de Arquitetura |

---

## Knowledge Base

| Domínio | Propósito | Ponto de entrada |
|---------|-----------|-----------------|
| `pandas` | Manipulação e transformação de dados | `.claude/kb/pandas/index.md` |
| `openpyxl` | Geração de planilha Excel | `.claude/kb/openpyxl/index.md` |
| `requests` | HTTP — download B3 e API BACEN | `.claude/kb/requests/index.md` |
| `uv` | Gerenciador de dependências | `.claude/kb/uv/index.md` |

---

## Features Ativas

| Feature | Status | Descrição |
|---------|--------|-----------|
| Setup inicial | ✅ | KBs, agentes de domínio e CLAUDE.md configurados |

---

## Features Shipadas (SDD Archive)

| Feature | Shipped | Descrição |
|---------|---------|-----------|
| Pipeline core | 2026-06-07 | Parser B3 + PTAX BACEN + join + Excel — `.claude/sdd/archive/PIPELINE_CORE/` |

> **Pós-ship (2026-06-07):** cobertura de moedas expandida de 19 → 42 (curadoria manual de
> 23 novas moedas via instrumentos `{CÓDIGO}-T1`, validadas ponta a ponta contra dados
> reais de 29/05/2026 — ver seção "42 moedas cobertas" e `instruction/REGRAS_DO_PIPELINE.md`).

---

## Ajuda

- **README de execução:** [README.md](../README.md)
- **PRD:** [instruction/PRD_Taxas_Spot_B3.md](../instruction/PRD_Taxas_Spot_B3.md)
- **Regras do pipeline (linguagem simples):** [instruction/REGRAS_DO_PIPELINE.md](../instruction/REGRAS_DO_PIPELINE.md)
- **Workflow SDD:** [.claude/sdd/_index.md](.claude/sdd/_index.md)
- **Agentes:** [.claude/agents/domain/](.claude/agents/domain/)
- **KB Index:** [.claude/kb/_index.yaml](.claude/kb/_index.yaml)
