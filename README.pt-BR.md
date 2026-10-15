# P01 — Orquestração multiagente

Este projeto implementa triagem de tickets de SupportOps com um supervisor-worker determinístico e o contrato comum `TriageRunner`. Os doubles locais de domínio permanecem até que P00 publique um pacote versionado e aprovado. A demonstração disponível usa `LLM_MODE=fake`, a biblioteca padrão do Python e não chama provedores de modelos.

## Arquitetura

O fluxo executável classifica o ticket, busca contexto de conhecimento, verifica cobrança e prepara uma resposta. O supervisor encerra com resposta aprovada, escalonamento ou limite de passos. Os seis runners têm integrações fake-mode executáveis; LangGraph também usa branches paralelos, retries, checkpoint SQLite e interrupção de aprovação humana. Consulte os detalhes em [README.md](README.md).

## Como executar

```powershell
uv sync --group frameworks
uv run --group frameworks python scripts/check_fast.py
$env:PYTHONPATH = "src"
uv run --group frameworks python -m supportops_agents.demo
uv run --group frameworks python -m supportops_agents.comparison --output artifacts/runs/latest
```

O check completo executa testes unitários, comparação sintética, demonstração local e checagens estruturais:

```powershell
uv run --group frameworks python scripts/check_full.py
```

Cada validação grava comando, código de saída e saída em `artifacts/evidence/`.

## Resultados e limitações

O resultado fake verifica apenas o fluxo de controle determinístico; não mede qualidade de modelo. Precisão, tokens, custo e latência de modelo ficam `PENDING`. Os seis runners estão implementados e passam os contratos sintéticos; a avaliação de qualidade com modelo real não foi executada.

Os contratos `Ticket` e `TriageDecision` são doubles locais e não importam código de repositórios irmãos. A integração P00 depende de pacote instalado por versão, commit de origem e hash do artefato. Consulte [ADR-001](docs/decisions/ADR-001-framework-scope.md) para a decisão sobre os frameworks Microsoft.

## Resposta de entrevista

**PT:** Como evitar que um supervisor multiagente entre em loop? Cada chamada conta como passo, o limite é validado como inteiro positivo e a execução só termina quando há resposta aprovada, escalonamento ou limite atingido. O teste usa um fake que nunca aprova.

**EN:** How do you prevent a multi-agent supervisor from looping forever? Every worker call counts as a step, the limit must be a positive integer, and execution stops on approval, escalation, or the limit. A fake that never approves covers the boundary.
