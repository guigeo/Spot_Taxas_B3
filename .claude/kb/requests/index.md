# Requests Knowledge Base

> **Purpose**: Chamadas HTTP em Python — download de arquivos e consumo de APIs REST/OData
> **MCP Validated**: 2026-06-05

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/session-basics.md](concepts/session-basics.md) | Session, headers e reutilização de conexão |
| [concepts/response-handling.md](concepts/response-handling.md) | Status codes, JSON e download de binários |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/download-binary.md](patterns/download-binary.md) | Download de arquivo comprimido (B3 .ex_) |
| [patterns/odata-api.md](patterns/odata-api.md) | Consumo de API OData (BACEN PTAX) |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Cheatsheet de operações comuns

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Session** | Reutiliza conexões TCP e headers — preferir sobre `requests.get` isolado |
| **stream** | `stream=True` para download de arquivos grandes sem carregar tudo em memória |
| **raise_for_status** | Lança exceção automática para respostas 4xx/5xx |

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| b3-pipeline-developer | quick-reference.md, patterns/download-binary.md, patterns/odata-api.md | Download B3 e PTAX BACEN |
