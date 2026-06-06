# Claude Project Template — AgentSpec 4.2

> Template de projeto com SDD, agentes, KBs e Dev Loop pré-configurados para Claude Code.

---

## Contexto do Projeto

**Problema:** Cada novo projeto exige reconfigurar manualmente agentes, comandos e workflows no Claude Code — trabalho repetitivo que atrasa o início do desenvolvimento real.

**Solução:** Um repositório template que contém toda a estrutura `.claude/` pré-configurada. Um `setup.sh` cria o projeto novo em segundos; o `/project-init` instala KBs e agentes de domínio antes da primeira feature.

**Stack:** Markdown, Shell script (bash), Claude Code slash commands, AgentSpec 4.2

**Mantenedor:** Guilherme Ramos — projeto solo

---

## Arquitetura do Template

```text
0_modelo-base-projeto-sdd-agent-spec/
├── .claude/
│   ├── CLAUDE.md                    # Este arquivo
│   ├── agents/
│   │   ├── _template.md.example     # Template para novos agentes
│   │   ├── workflow/                # Agentes SDD (6)
│   │   ├── code-quality/            # Agentes de qualidade (6)
│   │   ├── communication/           # Agentes de comunicação (3)
│   │   ├── exploration/             # kb-architect, codebase-explorer (2)
│   │   ├── ai-ml/                   # Agentes LLM/AI (4)
│   │   ├── dev/                     # Dev Loop agents (2)
│   │   ├── aws/                     # Agentes AWS (4)
│   │   ├── data-engineering/        # Agentes Spark/Databricks (8)
│   │   └── domain/                  # Vazio — criado por /project-init nos projetos filhos
│   ├── commands/
│   │   ├── core/                    # project-init, sync-context, memory, readme-maker
│   │   ├── workflow/                # brainstorm, define, design, build, ship, iterate
│   │   ├── knowledge/               # create-kb
│   │   ├── review/                  # review
│   │   └── dev/                     # dev
│   ├── sdd/                         # Framework SDD: templates, exemplos, arquitetura
│   ├── dev/                         # Dev Loop: templates de PROMPT
│   └── kb/
│       ├── _index.yaml              # Registro de domínios KB
│       └── _templates/              # Templates para criação de KBs
├── setup.sh                         # Cria projeto novo a partir deste template
└── README.md                        # Documentação pública do template
```

---

## Workflows de Desenvolvimento

### Quando trabalhar NESTE repositório

Este repo é o template — mudanças aqui propagam para **todos os projetos futuros** criados via `setup.sh`. Qualquer adição de agente, comando ou melhoria deve ser feita aqui primeiro.

### AgentSpec 4.2 (Spec-Driven Development)

```text
/brainstorm → /define → /design → /build → /ship
  (Opus)      (Opus)    (Opus)   (Sonnet)  (Haiku)
```

| Comando | Fase | Propósito |
|---------|------|-----------|
| `/brainstorm` | 0 | Explorar ideias (opcional) |
| `/define` | 1 | Capturar e validar requisitos |
| `/design` | 2 | Criar arquitetura e especificação |
| `/build` | 3 | Executar implementação |
| `/ship` | 4 | Arquivar com lições aprendidas |
| `/iterate` | Qualquer | Atualizar documentos mid-stream |

**Artefatos:** `.claude/sdd/features/` e `.claude/sdd/archive/`

### Dev Loop (Nível 2 Agentico)

```bash
/dev "Quero construir X"              # O crafter te guia
/dev tasks/PROMPT_FEATURE.md          # Executa PROMPT existente
/dev tasks/PROMPT_FEATURE.md --resume # Retoma sessão interrompida
```

---

## Diretrizes de Uso de Agentes

| Categoria | Agentes | Quando usar |
|-----------|---------|-------------|
| **Workflow** | brainstorm, define, design, build, ship, iterate | Construir melhorias no template com SDD |
| **Qualidade** | code-reviewer, code-cleaner, dual-reviewer | Revisar mudanças em agentes e comandos |
| **Exploração** | codebase-explorer, kb-architect | Explorar estrutura, criar novos domínios KB |
| **Comunicação** | the-planner | Planejar mudanças maiores no template |

---

## Padrões de Desenvolvimento do Template

### Formato de agentes (`.claude/agents/**/*.md`)

Todo agente deve seguir o formato definido em [.claude/agents/_template.md.example](.claude/agents/_template.md.example):
- Frontmatter com `name`, `description`, `tools`, `color`
- Seção de validação KB + MCP (Agreement Matrix)
- Thresholds de confiança por tipo de tarefa
- Exemplos concretos no `description`

### Formato de comandos (`.claude/commands/**/*.md`)

Comandos são instruções para o Claude seguir. Padrão:
- Frontmatter com `name` e `description`
- Seção `## Processo` com passos numerados e explícitos
- Gate de qualidade com checklist `[ ]` ao final
- Sem ambiguidade — Claude deve poder executar sem perguntar

### Adicionando um novo agente

```bash
# 1. Copiar o template
cp .claude/agents/_template.md.example .claude/agents/<categoria>/<nome>.md

# 2. Preencher todos os {placeholders}
# 3. Testar em um projeto filho antes de commitar aqui
```

### Adicionando um novo comando

```bash
# 1. Criar em .claude/commands/<categoria>/<nome>.md
# 2. Adicionar entrada na tabela de Comandos do CLAUDE.md
# 3. Adicionar entrada na tabela do README.md
# 4. Adicionar ao setup.sh se precisar de ajuste nos "próximos passos"
```

### Propagando mudanças para projetos existentes

O `setup.sh` só age em projetos **novos**. Para projetos existentes, copiar manualmente os arquivos alterados ou aguardar o mecanismo de update (a implementar).

---

## Comandos

| Comando | Propósito |
|---------|-----------|
| `/project-init` | **Primeiro comando em todo projeto** — instala KBs, cria agentes de domínio, preenche CLAUDE.md |
| `/brainstorm` | Explorar ideias em diálogo colaborativo |
| `/define` | Capturar e validar requisitos |
| `/design` | Criar arquitetura técnica |
| `/build` | Executar implementação |
| `/ship` | Arquivar feature concluída |
| `/iterate` | Atualizar documentos mid-stream |
| `/dev` | Dev Loop para iteração estruturada |
| `/create-kb` | Criar domínio de knowledge base |
| `/review` | Revisão de código |
| `/create-pr` | Criar pull request |
| `/memory` | Salvar insights da sessão |
| `/sync-context` | Atualizar CLAUDE.md com contexto do projeto |
| `/readme-maker` | Gerar README completo |

---

## Knowledge Base

O template inclui apenas os templates de estrutura KB. KBs reais são criadas nos projetos filhos via `/project-init` ou `/create-kb`.

| Domínio | Propósito | Ponto de entrada |
|---------|-----------|-----------------|
| *(vazio)* | KBs são criadas nos projetos filhos | `.claude/kb/_index.yaml` |

---

## Features Ativas

| Feature | Status | Descrição |
|---------|--------|-----------|
| `/project-init` | ✅ Concluído | Kickstart interativo com KBs + agentes + CLAUDE.md |
| Mecanismo de update | 🔜 Pendente | Notificar projetos existentes sobre updates do template |

---

## Ajuda

- **Workflow SDD:** [.claude/sdd/_index.md](.claude/sdd/_index.md)
- **Exemplos SDD:** [.claude/sdd/examples/](.claude/sdd/examples/)
- **Dev Loop:** [.claude/dev/_index.md](.claude/dev/_index.md)
- **Agentes:** [.claude/agents/](.claude/agents/)
- **KB Index:** [.claude/kb/_index.yaml](.claude/kb/_index.yaml)
