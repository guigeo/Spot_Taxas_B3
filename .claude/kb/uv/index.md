# uv Knowledge Base

> **Purpose**: Gerenciador de pacotes e ambientes Python — substituto do pip/venv
> **MCP Validated**: 2026-06-05

## Quick Navigation

### Concepts

| File | Purpose |
|------|---------|
| [concepts/project-structure.md](concepts/project-structure.md) | pyproject.toml, uv.lock e .venv gerenciado |
| [concepts/uv-vs-pip.md](concepts/uv-vs-pip.md) | Por que e como substituir pip por uv |

### Patterns

| File | Purpose |
|------|---------|
| [patterns/init-project.md](patterns/init-project.md) | Inicializar projeto Python do zero com uv |

---

## Quick Reference

- [quick-reference.md](quick-reference.md) - Comandos do dia a dia

---

## Key Concepts

| Concept | Description |
|---------|-------------|
| **uv add** | Adiciona dependência ao projeto (substitui `pip install`) |
| **uv run** | Executa script/comando no ambiente do projeto |
| **uv.lock** | Lockfile determinístico para reprodutibilidade |

## REGRA DO PROJETO

**NUNCA** usar `pip install`. Sempre `uv add <pacote>` ou `uv run <cmd>`.

---

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| b3-pipeline-developer | quick-reference.md, patterns/init-project.md | Gerenciar dependências do pipeline |
| spot-taxas-b3-expert | quick-reference.md | Configurar e manter o ambiente do projeto |
