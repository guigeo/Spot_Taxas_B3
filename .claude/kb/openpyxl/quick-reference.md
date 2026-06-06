# Openpyxl Quick Reference

> Fast lookup. Para exemplos completos, ver patterns/.

## ExcelWriter (via pandas — preferido)

| Operação | Código |
|----------|--------|
| Escrita simples | `df.to_excel('out.xlsx', index=False)` |
| Com engine explícito | `df.to_excel('out.xlsx', index=False, engine='openpyxl')` |
| Múltiplas abas | `with pd.ExcelWriter('out.xlsx') as w: df1.to_excel(w, sheet_name='B3'); df2.to_excel(w, sheet_name='PTAX')` |

## Acesso direto ao workbook

| Operação | Código |
|----------|--------|
| Abrir existente | `wb = load_workbook('out.xlsx')` |
| Obter aba | `ws = wb['Taxas']` ou `wb.active` |
| Salvar | `wb.save('out.xlsx')` |

## Formatação de células

| Operação | Código |
|----------|--------|
| Negrito | `cell.font = Font(bold=True)` |
| Cor de fundo | `cell.fill = PatternFill('solid', fgColor='4472C4')` |
| Alinhamento | `cell.alignment = Alignment(horizontal='center')` |
| Formato numérico | `cell.number_format = '#,##0.0000'` |

## Ajuste de coluna e painel

| Operação | Código |
|----------|--------|
| Largura manual | `ws.column_dimensions['A'].width = 15` |
| Congelar cabeçalho | `ws.freeze_panes = 'A2'` |

## Imports necessários

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl import load_workbook
```

## Decision Matrix

| Use Case | Choose |
|----------|--------|
| Só exportar DataFrame | `df.to_excel()` via pandas |
| Formatação pós-escrita | `load_workbook` + modificar + `save` |
| Múltiplas abas | `pd.ExcelWriter` com context manager |

## Common Pitfalls

| Don't | Do |
|-------|-----|
| `wb.save()` fora do context manager | Usar `with pd.ExcelWriter(...) as w:` |
| Esquecer `engine='openpyxl'` | Sempre especificar quando a planilha precisa de formatação |
| Modificar sem salvar | Sempre `wb.save(path)` no final |

## Related Documentation

| Topic | Path |
|-------|------|
| Exportar com formatação | `patterns/pandas-to-excel.md` |
| Full Index | `index.md` |
