# Formatação de Células

> Fontes, cores, bordas, alinhamento e formatos numéricos com openpyxl.

## Imports necessários

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
```

## Fonte

```python
from openpyxl.styles import Font

cell.font = Font(bold=True, size=12, color='FFFFFF')
```

## Cor de fundo

```python
from openpyxl.styles import PatternFill

cell.fill = PatternFill('solid', fgColor='4472C4')  # azul
```

## Alinhamento

```python
from openpyxl.styles import Alignment

cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
```

## Formato numérico

```python
# 4 casas decimais para taxas de câmbio
cell.number_format = '#,##0.0000'

# Percentual
cell.number_format = '0.00%'

# Data
cell.number_format = 'DD/MM/YYYY'
```

## Borda

```python
from openpyxl.styles import Border, Side

thin = Side(border_style='thin', color='000000')
cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
```

## Aplicar em linha inteira (cabeçalho)

```python
header_font = Font(bold=True, color='FFFFFF')
header_fill = PatternFill('solid', fgColor='2F5496')
header_align = Alignment(horizontal='center')

for col_idx, col_name in enumerate(df.columns, start=1):
    cell = ws.cell(row=1, column=col_idx)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align
```
