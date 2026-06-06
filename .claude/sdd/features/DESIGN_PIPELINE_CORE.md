# DESIGN: Pipeline Core — Parser B3, PTAX BACEN e Geração de Excel

> Arquitetura modular em 6 módulos Python: calendário → download → parse → PTAX → cálculo → Excel.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PIPELINE_CORE |
| **Date** | 2026-06-05 |
| **Author** | design-agent |
| **DEFINE** | [DEFINE_PIPELINE_CORE.md](./DEFINE_PIPELINE_CORE.md) |
| **Status** | Ready for Build |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                      main.py  (orquestrador)                    │
│                                                                 │
│  data_ref = calendario.resolver_data_util(hoje)                 │
│       │                                                         │
│       ▼                                                         │
│  indic_path = downloader.baixar_e_extrair(data_ref)             │
│       │                                                         │
│       ▼                                                         │
│  df_b3 = parser.parsear(indic_path, data_ref)                   │
│       │                                                         │
│       ├──────────────────────────────────────┐                  │
│       ▼                                      ▼                  │
│  df_ptax = ptax.buscar(data_ref)      (paralelo conceitual)     │
│       │                                                         │
│       └──────────────┬───────────────────────┘                  │
│                      ▼                                          │
│  df_final = calculator.calcular(df_b3, df_ptax)                 │
│                      │                                          │
│                      ▼                                          │
│  path = exporter.gerar_excel(df_final, data_ref)                │
│                      │                                          │
│                      ▼                                          │
│  data/output/taxas_spot_b3_{YYYYMMDD}.xlsx  ✓                   │
└─────────────────────────────────────────────────────────────────┘

Fontes externas:
  [B3]   https://www.b3.com.br/pesquisapregao/download?filelist=ID{YYMMDD}.ex_,
  [BACEN] https://olinda.bcb.gov.br/.../CotacaoTodosComercialDia
  [BACEN] https://olinda.bcb.gov.br/.../Feriados (calendário)
```

---

## Components

| Componente | Arquivo | Responsabilidade |
|------------|---------|-----------------|
| Config | `src/config.py` | Tabela de instrumentos B3 por moeda (tipo, nome, divisor, método) |
| Calendário | `src/calendario.py` | Resolver data útil de referência; consultar feriados BACEN |
| Downloader | `src/downloader.py` | Baixar `.ex_`, extrair `Indic.txt`; retry em falha de rede |
| Parser | `src/parser.py` | Parse do arquivo largura fixa; decodificar campo numérico; filtrar data D |
| PTAX | `src/ptax.py` | Consultar API BACEN; filtrar `tipoBoletim=Fechamento`; retornar dict |
| Calculator | `src/calculator.py` | Aplicar divisores, paridades (GBP/NZD/CNY); join B3+PTAX; calcular spread |
| Exporter | `src/exporter.py` | Gerar planilha Excel formatada com openpyxl |
| Entrypoint | `main.py` | Orquestrar todos os módulos; logging; exit code |

---

## Key Decisions

### Decision 1: Módulos planos em src/ (sem subpacotes)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-05 |

**Context:** Pipeline pequeno com ~7 módulos. Precisamos de separação de responsabilidades sem burocracia.

**Choice:** Módulos Python planos em `src/` — sem `src/pipeline/`, sem namespace aninhado.

**Rationale:** Sete arquivos são fáceis de navegar. Subpacotes adicionam `__init__.py` extras e imports mais longos sem benefício para este tamanho.

**Alternatives Rejected:**
1. Pacote `src/pipeline/` com submódulos — desnecessário para 7 arquivos
2. Tudo em `main.py` — impossível testar unitariamente

**Consequences:**
- Imports simples: `from src.parser import parsear`
- Qualquer crescimento futuro pode migrar para subpacotes sem quebrar contratos

---

### Decision 2: Tabela de instrumentos como dict Python (não YAML)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-05 |

**Context:** A tabela de mapeamento moeda → instrumento B3 é estável, vem do PRD e muda raramente.

**Choice:** `INSTRUMENTOS: dict` em `src/config.py`.

**Rationale:** Sem dependência extra de parser YAML. Fácil de validar com type hints. A tabela é código, não configuração operacional.

**Alternatives Rejected:**
1. `config.yaml` — leitura em runtime, dependência de `PyYAML` ou `tomllib`, sem ganho real
2. Enum — verboso, não agrega legibilidade para este caso

**Consequences:**
- Mudança na tabela = mudança de código + commit (desejável — rastreável no git)

---

### Decision 3: DataFrames pandas como interface entre módulos

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-05 |

**Context:** `parser`, `ptax`, `calculator` todos manipulam dados tabulares. Precisamos de uma interface comum.

**Choice:** Cada módulo recebe e retorna `pd.DataFrame` com schema definido na docstring.

**Rationale:** Pandas já é dependência obrigatória. O `merge` final (B3 + PTAX) é trivial com DataFrames. Type hints com `pd.DataFrame` são suficientes para projeto solo.

**Alternatives Rejected:**
1. Dataclasses por linha — muito verbose para 19 moedas × 8 campos
2. Dicts aninhados — dificulta o `merge` final e debugging

**Consequences:**
- Schema de cada DataFrame documentado em `src/config.py`
- Testes unitários usam `pd.testing.assert_frame_equal`

---

### Decision 4: Logging com print estruturado (sem biblioteca de logging)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-05 |

**Context:** Pipeline local, execução manual, único usuário. Sem necessidade de log estruturado para sistemas externos.

**Choice:** `print()` com prefixos `[INFO]`, `[WARN]`, `[ERROR]` em `main.py`. Módulos levantam exceções, não logam diretamente.

**Rationale:** Sem overhead de configuração de `logging`. Saída limpa no terminal. Para escalar para produção no futuro, basta trocar os prints por `logging.info/warning/error`.

**Alternatives Rejected:**
1. `logging` stdlib — configuração desnecessária para CLI solo
2. `loguru` — dependência extra sem ganho relevante

**Consequences:**
- Saída visível no terminal durante execução
- Módulos não têm efeitos colaterais de I/O (apenas retornam dados ou levantam exceções)

---

### Decision 5: Retry simples com loop manual (sem urllib3 Retry)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-05 |

**Context:** Conexão pode falhar por instabilidade momentânea. Precisamos de resiliência básica.

**Choice:** Loop `for tentativa in range(3)` com `time.sleep(2 ** tentativa)` em `downloader.py` e `ptax.py`.

**Rationale:** Sem dependência extra. Fácil de entender. 3 tentativas com backoff 1s/2s/4s é suficiente para instabilidade momentânea.

**Alternatives Rejected:**
1. `urllib3.util.retry.Retry` — mais configuração para o mesmo resultado
2. Sem retry — falha rígida por queda momentânea de rede

**Consequences:**
- Timeout máximo de ~7s em caso de falha consecutiva
- Comportamento previsível e testável com mock de requests

---

## File Manifest

| # | Arquivo | Ação | Propósito | Agente | Depende de |
|---|---------|------|-----------|--------|------------|
| 1 | `src/config.py` | Criar | Tabela de instrumentos + schemas de DataFrame | @b3-pipeline-developer | — |
| 2 | `src/calendario.py` | Criar | Resolver data útil; feriados BACEN | @b3-pipeline-developer | 1 |
| 3 | `src/downloader.py` | Criar | Download `.ex_` + extração `Indic.txt` | @b3-pipeline-developer | 1 |
| 4 | `src/parser.py` | Criar | Parse largura fixa + decodificação numérica | @b3-pipeline-developer | 1 |
| 5 | `src/ptax.py` | Criar | API PTAX BACEN | @b3-pipeline-developer | 1 |
| 6 | `src/calculator.py` | Criar | Divisores, paridades, join, spread | @b3-pipeline-developer | 1, 4, 5 |
| 7 | `src/exporter.py` | Criar | Planilha Excel formatada | @b3-pipeline-developer | 1, 6 |
| 8 | `main.py` | Modificar | Orquestrador + logging + exit code | @b3-pipeline-developer | 2–7 |
| 9 | `tests/test_parser.py` | Criar | Testes unitários: parse + decode numérico | @test-generator | 4 |
| 10 | `tests/test_calculator.py` | Criar | Testes unitários: divisores, paridades, spread | @test-generator | 6 |
| 11 | `tests/test_calendario.py` | Criar | Testes unitários: lógica de dia útil | @test-generator | 2 |

**Total:** 11 arquivos (8 criações, 1 modificação, 3 novos de teste)

---

## Agent Assignment Rationale

| Agente | Arquivos | Por quê |
|--------|----------|---------|
| @b3-pipeline-developer | 1–8 | Especialista em parse B3, API BACEN, divisores/paridades — domínio completo do pipeline |
| @test-generator | 9–11 | Especialista em geração de fixtures pytest e casos de borda |

---

## Code Patterns

### Pattern 1: Tabela de instrumentos (src/config.py)

```python
from dataclasses import dataclass
from typing import Literal

Method = Literal["direto", "paridade_multiplicada", "paridade_dividida"]

@dataclass(frozen=True)
class Instrumento:
    tipo: str          # ex: "RT", "TX"
    nome_sufixo: str   # ex: "DOL-D1" (busca por sufixo)
    divisor: float     # divisor extra após decodificação
    metodo: Method

INSTRUMENTOS: dict[str, Instrumento] = {
    "USD": Instrumento("RT", "DOL-D1",  1_000,       "direto"),
    "EUR": Instrumento("RT", "REUR-D1", 10_000_000,  "direto"),
    "JPY": Instrumento("TX", "JPY",     1_000,       "direto"),
    "AUD": Instrumento("RT", "AUD-T1",  1_000,       "direto"),
    "DKK": Instrumento("RT", "DKK-T1",  1_000,       "direto"),
    "SEK": Instrumento("RT", "RSEK-D1", 1_000,       "direto"),
    "CHF": Instrumento("RT", "RCHF-D1", 1_000,       "direto"),
    "ZAR": Instrumento("RT", "RZAR-D1", 1_000,       "direto"),
    "CLP": Instrumento("RT", "RCLP-D1", 1_000,       "direto"),
    "TRY": Instrumento("RT", "RTRY-D1", 1_000,       "direto"),
    "NOK": Instrumento("RT", "RNOK-D1", 1_000,       "direto"),
    "MXN": Instrumento("RT", "RMXN-D1", 1_000,       "direto"),
    "CNH": Instrumento("RT", "RCNH-D1", 1_000,       "direto"),
    "RUB": Instrumento("RT", "RRUB-D1", 1_000,       "direto"),
    "CAD": Instrumento("RT", "RCAD-D1", 1_000,       "direto"),
    "ARS": Instrumento("RT", "RARS-D1", 1_000,       "direto"),
    "GBP": Instrumento("RT", "GBP-PF",  1,           "paridade_multiplicada"),
    "NZD": Instrumento("RT", "NZD-PF",  1,           "paridade_multiplicada"),
    "CNY": Instrumento("RT", "CNY-PF",  1,           "paridade_dividida"),
}

# Schemas de DataFrame (documentação — não validação em runtime)
# df_b3 colunas:   moeda_iso, cotacao_b3, instrumento_b3, metodo_calculo
# df_ptax colunas: moeda_iso (codISO), ptax_compra, ptax_venda
# df_final colunas: data_referencia, moeda_iso, cotacao_b3, ptax_compra,
#                   ptax_venda, spread_b3_ptax, instrumento_b3, metodo_calculo
```

### Pattern 2: Decodificação do campo numérico (src/parser.py)

```python
from pathlib import Path
from datetime import date
import pandas as pd
from src.config import INSTRUMENTOS, Instrumento


def _decode_valor(valor_raw: str) -> float:
    digits = valor_raw.lstrip('+').lstrip('-')
    casas = int(digits[-2:])
    inteiro = int(digits[:-2])
    valor = inteiro / (10 ** casas)
    return -valor if valor_raw.startswith('-') else valor


def _buscar_instrumento(df: pd.DataFrame, tipo: str, sufixo: str) -> float | None:
    mask = (df["tipo"] == tipo) & df["nome"].str.endswith(sufixo.split("-")[0])
    rows = df[mask]
    return rows.iloc[0]["valor"] if not rows.empty else None


def parsear(indic_path: Path, data_ref: date) -> pd.DataFrame:
    rows = []
    with open(indic_path, encoding="latin-1") as f:
        for line in f:
            if len(line) < 47 or line[6:11] != "00101":
                continue
            rows.append({
                "data":  line[11:19].strip(),
                "tipo":  line[19:21].strip(),
                "nome":  line[21:46].strip(),
                "valor": _decode_valor(line[46:].strip()),
            })

    df = pd.DataFrame(rows)
    data_d = df["data"].max()
    df = df[df["data"] == data_d].copy()

    resultados = []
    usd_spot: float | None = None

    for moeda, inst in INSTRUMENTOS.items():
        val_raw = _buscar_instrumento(df, inst.tipo, inst.nome_sufixo)

        if moeda == "USD" and val_raw is not None:
            usd_spot = val_raw / inst.divisor

        cotacao: float | None = None
        if val_raw is not None:
            if inst.metodo == "direto":
                cotacao = val_raw / inst.divisor
            elif inst.metodo == "paridade_multiplicada" and usd_spot:
                cotacao = usd_spot * val_raw
            elif inst.metodo == "paridade_dividida" and usd_spot and val_raw != 0:
                cotacao = usd_spot / val_raw

        resultados.append({
            "moeda_iso":      moeda,
            "cotacao_b3":     cotacao,
            "instrumento_b3": inst.nome_sufixo,
            "metodo_calculo": inst.metodo,
        })

    return pd.DataFrame(resultados)
```

### Pattern 3: API PTAX BACEN (src/ptax.py)

```python
import time
import requests
import pandas as pd
from datetime import date


def buscar(data_ref: date) -> pd.DataFrame:
    data_str = data_ref.strftime("%m-%d-%Y")
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoTodosComercialDia(dataCotacao=@dataCotacao)"
    )
    params = {"@dataCotacao": f"'{data_str}'", "$format": "json"}

    for tentativa in range(3):
        try:
            with requests.Session() as s:
                r = s.get(url, params=params, timeout=(5, 30))
                r.raise_for_status()
            break
        except requests.RequestException:
            if tentativa == 2:
                raise
            time.sleep(2 ** tentativa)

    registros = r.json().get("value", [])
    df = pd.DataFrame(registros)
    if df.empty:
        return pd.DataFrame(columns=["moeda_iso", "ptax_compra", "ptax_venda"])

    df = df[df["tipoBoletim"] == "Fechamento"].copy()
    return df.rename(columns={"codISO": "moeda_iso",
                               "cotacaoCompra": "ptax_compra",
                               "cotacaoVenda": "ptax_venda"})[
        ["moeda_iso", "ptax_compra", "ptax_venda"]
    ]
```

### Pattern 4: Join e spread (src/calculator.py)

```python
import pandas as pd


def calcular(df_b3: pd.DataFrame, df_ptax: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(df_b3, df_ptax, on="moeda_iso", how="left")

    def spread(row) -> float | None:
        b3, ptax = row["cotacao_b3"], row["ptax_venda"]
        if b3 is None or ptax is None or pd.isna(b3) or pd.isna(ptax) or ptax == 0:
            return None
        return round((b3 / ptax - 1) * 100, 4)

    df["spread_b3_ptax"] = df.apply(spread, axis=1)
    return df
```

### Pattern 5: Exportação Excel (src/exporter.py)

```python
from pathlib import Path
from datetime import date
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


COLUNAS_FINAIS = [
    "data_referencia", "moeda_iso", "cotacao_b3",
    "ptax_compra", "ptax_venda", "spread_b3_ptax",
    "instrumento_b3", "metodo_calculo",
]

COLUNAS_TAXA = {"cotacao_b3", "ptax_compra", "ptax_venda"}


def gerar_excel(df: pd.DataFrame, data_ref: date, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    caminho = output_dir / f"taxas_spot_b3_{data_ref.strftime('%Y%m%d')}.xlsx"

    df = df.copy()
    df.insert(0, "data_referencia", data_ref.isoformat())
    df = df[COLUNAS_FINAIS]

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Taxas B3 vs PTAX", index=False)

    wb = load_workbook(caminho)
    ws = wb["Taxas B3 vs PTAX"]

    hdr_font = Font(bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="2F5496")
    hdr_align = Alignment(horizontal="center")
    for cell in ws[1]:
        cell.font, cell.fill, cell.alignment = hdr_font, hdr_fill, hdr_align

    col_names = {cell.value: cell.column for cell in ws[1]}
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            col_name = ws.cell(row=1, column=cell.column).value
            if col_name in COLUNAS_TAXA:
                cell.number_format = "#,##0.0000"
            elif col_name == "spread_b3_ptax":
                cell.number_format = "0.0000"

    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 30)

    ws.freeze_panes = "A2"
    wb.save(caminho)
    return caminho
```

### Pattern 6: Orquestrador (main.py)

```python
import sys
from datetime import date
from pathlib import Path
from src.calendario import resolver_data_util
from src.downloader import baixar_e_extrair
from src.parser import parsear
from src.ptax import buscar as buscar_ptax
from src.calculator import calcular
from src.exporter import gerar_excel

DATA_DIR  = Path("data")
RAW_DIR   = DATA_DIR / "raw"
OUT_DIR   = DATA_DIR / "output"


def main() -> None:
    data_ref = resolver_data_util(date.today())
    print(f"[INFO] Data de referência: {data_ref.isoformat()}")

    print("[INFO] Baixando arquivo B3...")
    indic_path = baixar_e_extrair(data_ref, RAW_DIR)

    print("[INFO] Parseando arquivo...")
    df_b3 = parsear(indic_path, data_ref)

    print("[INFO] Buscando PTAX BACEN...")
    df_ptax = buscar_ptax(data_ref)

    print("[INFO] Calculando spread...")
    df_final = calcular(df_b3, df_ptax)

    # Alertas
    sem_b3   = df_final[df_final["cotacao_b3"].isna()]["moeda_iso"].tolist()
    sem_ptax = df_final[df_final["ptax_venda"].isna()]["moeda_iso"].tolist()
    if sem_b3:
        print(f"[WARN] Sem cotação B3: {sem_b3}")
    if sem_ptax:
        print(f"[WARN] Sem PTAX: {sem_ptax}")

    print("[INFO] Gerando planilha...")
    caminho = gerar_excel(df_final, data_ref, OUT_DIR)
    print(f"[INFO] Planilha gerada: {caminho}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
```

---

## Data Flow

```text
1. calendario.resolver_data_util(hoje)
   → Consulta feriados BACEN para o ano atual
   → Recua se sábado, domingo ou feriado
   → Retorna: date (data D)
   │
   ▼
2. downloader.baixar_e_extrair(data_ref, raw_dir)
   → GET b3.com.br/pesquisapregao/download?filelist=ID{YYMMDD}.ex_,
   → Salva ID{YYMMDD}.ex_ em data/raw/
   → Extrai Indic.txt com zipfile
   → Retorna: Path(data/raw/Indic.txt)
   │
   ▼
3. parser.parsear(indic_path, data_ref)
   → Lê Indic.txt linha a linha (encoding latin-1)
   → Filtra codigo_campo == "00101"
   → Seleciona linhas com data D (max)
   → Decodifica valor numérico (indicador de casas decimais)
   → Mapeia instrumentos → moedas (por sufixo de nome)
   → Aplica divisores diretos
   → Calcula paridades (GBP/NZD: × USD; CNY: ÷ USD)
   → Retorna: DataFrame[moeda_iso, cotacao_b3, instrumento_b3, metodo_calculo]
   │
   ▼
4. ptax.buscar(data_ref)
   → GET olinda.bcb.gov.br/.../CotacaoTodosComercialDia?dataCotacao=MM-DD-YYYY
   → Filtra tipoBoletim == "Fechamento"
   → Retorna: DataFrame[moeda_iso, ptax_compra, ptax_venda]
   │
   ▼
5. calculator.calcular(df_b3, df_ptax)
   → LEFT JOIN por moeda_iso
   → spread = (cotacao_b3 / ptax_venda - 1) × 100
   → Retorna: DataFrame[8 colunas do PRD]
   │
   ▼
6. exporter.gerar_excel(df_final, data_ref, output_dir)
   → ExcelWriter → "Taxas B3 vs PTAX"
   → load_workbook → formatar cabeçalho, números, largura, freeze
   → Salva em data/output/taxas_spot_b3_{YYYYMMDD}.xlsx
   → Retorna: Path
```

---

## Integration Points

| Sistema Externo | Tipo | Auth | URL |
|-----------------|------|------|-----|
| B3 download | REST GET (binário) | Nenhuma | `b3.com.br/pesquisapregao/download` |
| BACEN PTAX | OData GET (JSON) | Nenhuma | `olinda.bcb.gov.br/.../CotacaoTodosComercialDia` |
| BACEN Feriados | OData GET (JSON) | Nenhuma | `olinda.bcb.gov.br/.../Feriados` |

---

## Testing Strategy

| Tipo | Escopo | Arquivos | Ferramentas | Meta |
|------|--------|----------|-------------|------|
| Unitário | `_decode_valor`, `parsear`, `calcular`, `resolver_data_util` | `tests/test_parser.py`, `test_calculator.py`, `test_calendario.py` | pytest | Cobrir todos os ATs do DEFINE |
| Integração | Download real + parse | Manual com arquivo real do dia | `uv run python main.py` | AT-001 happy path |

**Casos prioritários para testes unitários:**
- `_decode_valor`: USD (10^3), EUR (10^7), JPY (10^3), valores negativos
- `parsear`: instrumento ausente → None; USD processado antes de GBP/NZD/CNY
- `calcular`: spread correto (AT-008: 5.0099/5.0050 = 0.0978%); PTAX null → spread null
- `resolver_data_util`: sexta → sexta; sábado → sexta; feriado → dia útil anterior

---

## Error Handling

| Erro | Módulo | Estratégia | Fatal? |
|------|--------|------------|--------|
| HTTP 4xx/5xx B3 | downloader | `raise_for_status()` → RuntimeError | Sim |
| Timeout de rede | downloader, ptax | Retry 3× com backoff 1s/2s/4s, depois RuntimeError | Sim |
| Arquivo `.ex_` inválido (não ZIP) | downloader | `BadZipFile` → RuntimeError com mensagem clara | Sim |
| Instrumento não encontrado | parser | `cotacao_b3 = None`, `[WARN]` no log | Não |
| PTAX ausente para moeda | calculator | `ptax_compra/venda = NaN` (left join), `[WARN]` | Não |
| Divergência > 20% B3 vs PTAX | main | `[WARN]` informativo | Não |
| Data futura ou sem dados | calendario | `ValueError` com mensagem | Sim |

---

## Configuration

| Config | Onde | Tipo | Valor padrão | Descrição |
|--------|------|------|-------------|-----------|
| `RAW_DIR` | `main.py` | `Path` | `data/raw/` | Diretório de arquivos brutos |
| `OUT_DIR` | `main.py` | `Path` | `data/output/` | Diretório de planilhas geradas |
| `INSTRUMENTOS` | `src/config.py` | `dict` | (tabela do PRD) | Mapeamento moeda → instrumento B3 |
| Timeout HTTP | `downloader.py`, `ptax.py` | `tuple[int,int]` | `(5, 30)` | (connect_timeout, read_timeout) em segundos |
| Tentativas retry | `downloader.py`, `ptax.py` | `int` | `3` | Número de tentativas em falha de rede |

---

## Security Considerations

- Endpoints B3 e BACEN são públicos (sem credenciais) — sem segredo a proteger
- `data/raw/` e `data/output/` no `.gitignore` — arquivos com dados de mercado não versionados
- Sem execução de código externo — `zipfile` extrai apenas conteúdo do `.ex_` da B3

---

## Observability

| Aspecto | Implementação |
|---------|---------------|
| Logging | `print()` com prefixos `[INFO]`, `[WARN]`, `[ERROR]` em `main.py` |
| Alertas | `[WARN]` para moedas sem B3 ou sem PTAX; `[WARN]` para divergência > 20% |
| Exit code | `sys.exit(1)` em exceção fatal; `0` em sucesso |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-05 | design-agent | Versão inicial |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_PIPELINE_CORE.md`
