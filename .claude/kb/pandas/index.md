# Pandas Knowledge Base

> **Purpose**: Manipulação e transformação de dados tabulares em Python
> **MCP Validated**: 2026-06-05

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/dataframe-basics.md](concepts/dataframe-basics.md) | Estrutura, tipos e operações fundamentais |
| [concepts/merge-join.md](concepts/merge-join.md) | Combinação de DataFrames |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/parse-fixed-width.md](patterns/parse-fixed-width.md) | Leitura de arquivo posicional (largura fixa) |
| [patterns/transform-export.md](patterns/transform-export.md) | Transformação e exportação para Excel |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Cheatsheet de operações comuns

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **DataFrame** | Tabela bidimensional com índice e colunas tipadas |
| **dtype** | Tipo de dado por coluna — impacta memória e operações |
| **merge** | Join entre DataFrames (equivalente ao SQL JOIN) |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| b3-pipeline-developer | quick-reference.md, patterns/parse-fixed-width.md | Parse do arquivo B3 e join com PTAX |
