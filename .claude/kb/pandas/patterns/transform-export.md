# Pattern: Transformação e Exportação para Excel

> Montar o DataFrame final e exportar com formatação.

## Estrutura do resultado final

```python
import pandas as pd

# Colunas esperadas no output (PRD seção 5)
COLUNAS_FINAIS = [
    'data_referencia',
    'moeda_iso',
    'cotacao_b3',
    'ptax_compra',
    'ptax_venda',
    'spread_b3_ptax',
    'instrumento_b3',
    'metodo_calculo',
]
```

## Construir DataFrame a partir de lista de dicts

```python
rows = []
for moeda, dados in resultado_por_moeda.items():
    rows.append({
        'data_referencia': data_d,
        'moeda_iso':       moeda,
        'cotacao_b3':      dados.get('cotacao_b3'),
        'ptax_compra':     dados.get('ptax_compra'),
        'ptax_venda':      dados.get('ptax_venda'),
        'spread_b3_ptax':  calcular_spread(dados),
        'instrumento_b3':  dados.get('instrumento'),
        'metodo_calculo':  dados.get('metodo'),
    })

df_final = pd.DataFrame(rows, columns=COLUNAS_FINAIS)
```

## Calcular spread percentual

```python
def calcular_spread(dados: dict) -> float | None:
    b3 = dados.get('cotacao_b3')
    ptax = dados.get('ptax_venda')
    if b3 is None or ptax is None or ptax == 0:
        return None
    return round((b3 / ptax - 1) * 100, 4)
```

## Exportar para Excel

```python
from pathlib import Path

def exportar_excel(df: pd.DataFrame, data_ref: str, output_dir: Path) -> Path:
    nome = f"taxas_spot_b3_{data_ref}.xlsx"
    caminho = output_dir / nome
    with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Taxas B3 vs PTAX', index=False)
    return caminho
```
