# Spot Taxas B3

Pipeline Python que extrai as taxas spot de câmbio do arquivo diário da B3, compara com a
PTAX de fechamento do BACEN para 42 moedas e gera uma planilha Excel pronta para
precificação, conciliação, auditoria e compliance cambial.

```
[B3] Indic.txt  ──┐
                  ├──► merge por moeda ──► spread % ──► taxas_spot_b3_{AAAAMMDD}.xlsx
[BACEN] PTAX    ──┘
```

Para entender **o que** o pipeline faz e **por que** cada regra existe (em linguagem
simples, com exemplos reais), veja [instruction/REGRAS_DO_PIPELINE.md](instruction/REGRAS_DO_PIPELINE.md).

---

## Pré-requisitos

- **Python 3.12** (fixado em [.python-version](.python-version))
- **[uv](https://docs.astral.sh/uv/)** — gerenciador de pacotes e ambientes

> ⚠️ Este projeto usa `uv` exclusivamente. Nunca rode `pip install` ou instale pacotes
> diretamente no ambiente local — sempre `uv add <pacote>` e `uv run <comando>`.

---

## Instalação

Clone o repositório e sincronize o ambiente (cria o `.venv` e instala as dependências do
lockfile `uv.lock`):

```bash
uv sync
```

---

## Execução

Roda o pipeline para a **data de referência atual** (resolve automaticamente para o
último dia útil, considerando finais de semana e feriados nacionais via BrasilAPI):

```bash
uv run python main.py
```

Saída esperada no terminal:

```
[INFO] Data de referência: 2026-06-05
[INFO] Baixando arquivo B3...
[INFO] Parseando arquivo...
[INFO] Buscando PTAX BACEN...
[INFO] Calculando spread...
[WARN] Sem PTAX: ['ZAR', 'CLP', 'TRY', 'MXN', 'CNH', 'RUB', 'ARS', 'NZD', 'CNY', 'AED', 'BOB', ...]
[INFO] Gerando planilha...
[INFO] Planilha gerada: data/output/taxas_spot_b3_20260605.xlsx
```

> Os avisos `[WARN] Sem PTAX` são esperados — várias moedas não têm boletim de
> fechamento PTAX publicado pelo BACEN (ver regra R6 em REGRAS_DO_PIPELINE.md). Avisos
> `[WARN] Sem cotação B3` ou `[WARN] Divergência > 20%` merecem investigação manual.

### Janela de execução ideal

| Fonte | Disponível a partir de |
|-------|------------------------|
| PTAX BACEN (fechamento) | ~18h BRT |
| Arquivo `.ex_` da B3 | ~19h BRT |
| **Execução recomendada** | **Após 19h BRT** |

Rodar antes desse horário pode resultar em arquivo da B3 ainda não publicado (o
downloader detecta resposta vazia e tenta novamente, mas eventualmente falha se o
arquivo simplesmente não existir ainda).

### Rodar para uma data específica

`main.py` não expõe um argumento de linha de comando para escolher a data — ele sempre
usa `date.today()` resolvido para o último dia útil. Para reprocessar uma data passada,
invoque as funções do pipeline diretamente em um script ou REPL:

```python
from datetime import date
from pathlib import Path

from src.calculator import calcular
from src.calendario import resolver_data_util
from src.downloader import baixar_e_extrair
from src.exporter import gerar_excel
from src.parser import parsear
from src.ptax import buscar as buscar_ptax

data_ref = resolver_data_util(date(2026, 5, 29))
indic_path = baixar_e_extrair(data_ref, Path("data/raw"))
df_b3 = parsear(indic_path, data_ref)
df_ptax = buscar_ptax(data_ref)
df_final = calcular(df_b3, df_ptax)
gerar_excel(df_final, data_ref, Path("data/output"))
```

```bash
uv run python -c "..."   # ou salve como script e rode com uv run python script.py
```

> A B3 e o BACEN só mantêm os arquivos/cotações de datas relativamente recentes
> disponíveis para download — datas muito antigas podem não retornar dados.

### Rodar em lote para várias datas

Como `gerar_excel` nomeia o arquivo pela data de referência (`taxas_spot_b3_{AAAAMMDD}.xlsx`),
basta repetir o passo acima dentro de um laço — cada data gera uma planilha separada:

```python
from datetime import date
from pathlib import Path

from src.calculator import calcular
from src.calendario import resolver_data_util
from src.downloader import baixar_e_extrair
from src.exporter import gerar_excel
from src.parser import parsear
from src.ptax import buscar as buscar_ptax

datas = [date(2026, 1, 30), date(2026, 2, 27), date(2026, 3, 30), date(2026, 4, 30)]

for d in datas:
    data_ref = resolver_data_util(d)
    indic_path = baixar_e_extrair(data_ref, Path("data/raw"))
    df_b3 = parsear(indic_path, data_ref)
    df_ptax = buscar_ptax(data_ref)
    df_final = calcular(df_b3, df_ptax)
    print(gerar_excel(df_final, data_ref, Path("data/output")))
```

> Cada iteração baixa um novo `.ex_` e sobrescreve `data/raw/Indic.txt` — a planilha de
> saída de cada data já fica salva antes de processar a próxima, então não há perda de dados.

---

## Saída gerada

A planilha é salva em `data/output/taxas_spot_b3_{AAAAMMDD}.xlsx`, com uma linha por
moeda contendo:

| Coluna | Descrição |
|--------|-----------|
| `data_referencia` | Data D usada na execução |
| `moeda_iso` | Código ISO da moeda (USD, EUR, JPY, ...) |
| `cotacao_b3` | Cotação spot extraída do arquivo da B3 |
| `ptax_compra` / `ptax_venda` | PTAX de fechamento do BACEN (`null` se ausente) |
| `spread_b3_ptax` | `(cotacao_b3 / ptax_venda − 1) × 100`, em % |
| `instrumento_b3` | Sufixo do instrumento B3 usado para encontrar a cotação |
| `metodo_calculo` | `direto`, `paridade_multiplicada` (GBP/NZD) ou `paridade_dividida` (CNY) |

`data/raw/` e `data/output/` não são versionados (ver `.gitignore`).

---

## Testes e qualidade

```bash
uv run pytest          # suíte de testes (parser, calculator, calendário)
uv run ruff check .    # lint
```

Os testes mockam as integrações externas (B3, BACEN, BrasilAPI) — eles validam a lógica
de decodificação, mapeamento e cálculo, mas **não substituem rodar o pipeline contra
dados reais** antes de considerar uma mudança pronta (ver lições aprendidas em
`.claude/sdd/archive/PIPELINE_CORE/SHIPPED_20260607.md`).

---

## As 42 moedas cobertas

USD, EUR, AUD, GBP, CAD, CHF, JPY, NZD, SEK, NOK, DKK, ZAR, MXN, ARS, CLP, TRY, CNY, CNH, RUB,
AED, BOB, COP, CRC, CZK, HKD, HUF, IDR, INR, KWD, MYR, PEN, PHP, PLN, PYG, QAR, RON, SAR, SGD,
THB, TWD, UYU, VND

> A lista é curada manualmente em `src/config.py` — o arquivo da B3 não identifica quais
> instrumentos são moedas, então cada novo código precisa ser validado contra dados reais
> antes de entrar na config (escala plausível em BRL, sem alerta de divergência > 20%).

A maioria é calculada diretamente a partir do instrumento B3 correspondente. Três casos
são especiais e dependem do USD spot (processado sempre primeiro):

- **GBP, NZD** — `cotação_BRL = USD_spot × paridade`
- **CNY** — `cotação_BRL = USD_spot ÷ paridade`

Detalhes completos do mapeamento moeda → instrumento B3 em
[instruction/REGRAS_DO_PIPELINE.md](instruction/REGRAS_DO_PIPELINE.md#4-as-moedas-e-como-cada-uma-é-calculada).

---

## Estrutura do projeto

```text
Spot_Taxas_B3/
├── instruction/
│   ├── PRD_Taxas_Spot_B3.md      # PRD original — escopo e contexto de negócio
│   └── REGRAS_DO_PIPELINE.md     # As 10 regras de negócio explicadas em linguagem simples
├── src/
│   ├── config.py                  # Mapa das 42 moedas → instrumento B3
│   ├── calendario.py              # Resolução de dia útil (feriados via BrasilAPI)
│   ├── downloader.py              # Download e extração do arquivo .ex_ da B3
│   ├── parser.py                  # Parse posicional, decodificação e paridades
│   ├── ptax.py                    # Busca da PTAX de fechamento no BACEN
│   ├── calculator.py              # Merge B3 + PTAX e cálculo de spread
│   └── exporter.py                # Geração da planilha Excel final
├── tests/                         # Testes unitários (pytest)
├── data/{raw,output}/             # Downloads e planilhas geradas (não versionado)
└── main.py                        # Entrypoint
```

---

## Documentação adicional

- **Regras de negócio em linguagem simples:** [instruction/REGRAS_DO_PIPELINE.md](instruction/REGRAS_DO_PIPELINE.md)
- **PRD original:** [instruction/PRD_Taxas_Spot_B3.md](instruction/PRD_Taxas_Spot_B3.md)
- **Histórico de desenvolvimento (SDD):** [.claude/sdd/archive/PIPELINE_CORE/](.claude/sdd/archive/PIPELINE_CORE/)
- **Contexto para Claude Code:** [.claude/CLAUDE.md](.claude/CLAUDE.md)
