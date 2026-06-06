# Workbook e Worksheet

> Estrutura hierárquica de um arquivo Excel com openpyxl.

## Hierarquia

```
Workbook (.xlsx)
└── Worksheet (aba)
    └── Cell (célula)
```

## Criar / abrir

```python
from openpyxl import Workbook, load_workbook

# Novo
wb = Workbook()
ws = wb.active          # aba padrão criada automaticamente
ws.title = 'Taxas B3'

# Nova aba
ws2 = wb.create_sheet('PTAX BACEN')

# Abrir existente
wb = load_workbook('out.xlsx')
ws = wb['Taxas B3']
```

## Escrita de células

```python
ws['A1'] = 'Moeda'
ws.cell(row=1, column=2, value='Cotação B3')

# Iterar e preencher
for i, row in df.iterrows():
    ws.cell(row=i+2, column=1, value=row['moeda_iso'])
    ws.cell(row=i+2, column=2, value=row['cotacao_b3'])
```

## Salvar

```python
wb.save('output/taxas.xlsx')
```

## Via pandas (preferido para DataFrames)

```python
with pd.ExcelWriter('output/taxas.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Taxas B3 vs PTAX', index=False)
```

> Para formatação pós-escrita: `load_workbook` no arquivo gerado e `wb.save`.
