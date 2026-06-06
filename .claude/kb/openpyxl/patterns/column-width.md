# Pattern: Ajuste Automático de Largura de Coluna

> Calcular e aplicar largura ideal para cada coluna de uma planilha.

## Implementação

```python
from openpyxl.utils import get_column_letter

def ajustar_largura_colunas(ws, min_width: int = 8, max_width: int = 40) -> None:
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(min_width, min(max_len + 4, max_width))
```

## Uso

```python
wb = load_workbook('out.xlsx')
ws = wb.active
ajustar_largura_colunas(ws)
wb.save('out.xlsx')
```

## Pitfalls

| Don't | Do |
|-------|-----|
| `ws.column_dimensions['A'].auto_size = True` (não funciona) | Calcular `max_len` manualmente |
| Largura sem limite | Usar `min(max_len + 4, max_width)` |
| Esquecer de salvar | `wb.save(caminho)` ao final |
