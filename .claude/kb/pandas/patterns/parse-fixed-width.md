# Pattern: Parse de Arquivo de Largura Fixa (B3)

> Leitura do arquivo Indic.txt (posicional, largura fixa) da B3.

## Contexto

O arquivo `Indic.txt` tem colunas em posições fixas — não tem delimitador. Cada linha tem 116+ caracteres.

```
Posições  Campo
1–6       Sequencial
7–11      Código de campo (00101 = taxa spot)
12–19     Data (YYYYMMDD)
20–21     Tipo instrumento
22–46     Nome instrumento (padded)
47+       Valor numérico (+NNNNNCC)
```

## Implementação recomendada (slicing manual)

```python
import pandas as pd
from pathlib import Path

def parse_indic(path: Path) -> pd.DataFrame:
    rows = []
    with open(path, encoding='latin-1') as f:
        for line in f:
            if len(line) < 47:
                continue
            rows.append({
                'sequencial':       line[0:6].strip(),
                'codigo_campo':     line[6:11].strip(),
                'data':             line[11:19].strip(),
                'tipo_instrumento': line[19:21].strip(),
                'nome_instrumento': line[21:46].strip(),
                'valor_raw':        line[46:].strip(),
            })
    df = pd.DataFrame(rows)
    # Apenas registros de taxa spot
    df = df[df['codigo_campo'] == '00101'].copy()
    return df
```

## Decodificação do campo numérico

```python
def decode_valor(valor_raw: str) -> float:
    digits = valor_raw.lstrip('+').lstrip('-')
    indicador_casas = int(digits[-2:])
    valor_inteiro   = int(digits[:-2])
    valor_real      = valor_inteiro / (10 ** indicador_casas)
    if valor_raw.startswith('-'):
        valor_real = -valor_real
    return valor_real

df['valor_decodificado'] = df['valor_raw'].apply(decode_valor)
```

## Selecionar data D (mais recente)

```python
data_d = df['data'].max()  # data mais recente do arquivo
df_d = df[df['data'] == data_d].copy()
```

## Lookup de instrumento por moeda

```python
INSTRUMENTOS = {
    'USD': ('RT', 'DOL-D1'),
    'EUR': ('RT', 'REUR-D1'),
    'JPY': ('TX', 'JPY'),
    # ...
}

def buscar_instrumento(df: pd.DataFrame, tipo: str, sufixo: str) -> float | None:
    # Busca por sufixo (nome pode mudar entre arquivos)
    mask = (df['tipo_instrumento'] == tipo) & df['nome_instrumento'].str.endswith(sufixo.split('-')[0])
    rows = df[mask]
    if rows.empty:
        return None
    return rows.iloc[0]['valor_decodificado']
```
