# Pattern: DataFrame para Excel com Formatação

> Exportar DataFrame pandas para Excel com cabeçalho formatado e colunas ajustadas.

## Implementação completa

```python
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


def exportar_taxas(df: pd.DataFrame, data_ref: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    caminho = output_dir / f"taxas_spot_b3_{data_ref}.xlsx"

    # 1. Escrever com pandas
    with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Taxas B3 vs PTAX', index=False)

    # 2. Reabrir para formatação
    wb = load_workbook(caminho)
    ws = wb['Taxas B3 vs PTAX']

    # 3. Formatar cabeçalho
    header_font  = Font(bold=True, color='FFFFFF')
    header_fill  = PatternFill('solid', fgColor='2F5496')
    header_align = Alignment(horizontal='center')
    for cell in ws[1]:  # primeira linha
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = header_align

    # 4. Formatar colunas numéricas
    colunas_taxa = ['cotacao_b3', 'ptax_compra', 'ptax_venda']
    col_idx_map  = {cell.value: cell.column for cell in ws[1]}
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            col_name = ws.cell(row=1, column=cell.column).value
            if col_name in colunas_taxa:
                cell.number_format = '#,##0.0000'
            elif col_name == 'spread_b3_ptax':
                cell.number_format = '0.0000"%"'

    # 5. Ajustar largura de colunas
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 30)

    # 6. Congelar cabeçalho
    ws.freeze_panes = 'A2'

    wb.save(caminho)
    return caminho
```

## Colunas esperadas no output

| Coluna | Formato Excel |
|--------|---------------|
| `data_referencia` | `DD/MM/YYYY` |
| `moeda_iso` | texto |
| `cotacao_b3` | `#,##0.0000` |
| `ptax_compra` | `#,##0.0000` |
| `ptax_venda` | `#,##0.0000` |
| `spread_b3_ptax` | `0.0000"%"` |
| `instrumento_b3` | texto |
| `metodo_calculo` | texto |
