# Openpyxl Knowledge Base

> **Purpose**: Geração e formatação de planilhas Excel (.xlsx) em Python
> **MCP Validated**: 2026-06-05

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/workbook-worksheet.md](concepts/workbook-worksheet.md) | Estrutura de arquivo Excel com openpyxl |
| [concepts/cell-formatting.md](concepts/cell-formatting.md) | Formatação de células, fontes e bordas |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/pandas-to-excel.md](patterns/pandas-to-excel.md) | Exportar DataFrame com formatação personalizada |
| [patterns/column-width.md](patterns/column-width.md) | Ajuste automático de largura de coluna |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Cheatsheet de operações comuns

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Workbook** | Arquivo Excel completo (.xlsx) |
| **Worksheet** | Aba individual dentro do Workbook |
| **ExcelWriter** | Interface pandas para escrita com engine openpyxl |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| b3-pipeline-developer | quick-reference.md, patterns/pandas-to-excel.md | Geração da planilha final de taxas |
