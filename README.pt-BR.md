# P01 — Orquestração multiagente

Este projeto trata tickets de SupportOps com um supervisor determinístico e o contrato comum `TriageRunner`. `Ticket` e `TriageDecision` continuam doubles locais do P01. O wheel P00 1.0.1 é instalado isoladamente para exportar o conjunto dourado; versão, commit de origem, SHA-256 e comando consumidor ficam em `docs/harness/sources.lock.json`. O runtime roda em `LLM_MODE=fake` e não chama provedores.

## Arquitetura

O fluxo classifica o ticket, busca contexto, verifica cobrança e prepara a resposta. Ele termina com aprovação, escalonamento ou limite de passos. Os seis runners funcionam em fake mode; LangGraph também cobre paralelismo, retries, checkpoint SQLite e pausa para aprovação humana. Os diagramas e detalhes ficam no [README.md](README.md).

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

O resultado fake cobre fluxo de controle, não qualidade de modelo. Os seis runners passam os contratos sintéticos. Há smokes históricos de um ticket Core com Groq; eles não completam a campanha de 60 casos com três trials. Métricas da campanha ampla continuam `PENDING`.

A fronteira contabilizada do Core foi implementada e testada offline. Ela usa índices estáveis por chamada, limite de quatro workers e transporte compartilhado sem SDK ou chaves no processo pai. O manifesto de execução permanece desabilitado até o dispatcher durável, a alocação e o congelamento do candidato estarem concluídos. O comando live antigo agora retorna `INCOMPLETE` antes de credenciais/SDK. Os frameworks ficam restritos a fake/replay, com telemetria desabilitada antes da importação. Não há executor de ferramentas externas ou efeitos financeiros no Core atual.

Os contratos `Ticket` e `TriageDecision` são doubles locais e não importam código de repositórios irmãos. O relatório exercita os 60 casos do wheel P00 instalado, mas os campos de decisão sem equivalente no contrato P01 são marcados caso a caso. O uso do wheel junto com CrewAI no mesmo ambiente está bloqueado pelas versões incompatíveis de Pydantic; o exportador roda isoladamente. Consulte [ADR-001](docs/decisions/ADR-001-framework-scope.md) para a decisão sobre os frameworks Microsoft.

## Resposta de entrevista

**PT:** Como evitar que um supervisor multiagente entre em loop? Cada chamada conta como passo, o limite é validado como inteiro positivo e a execução só termina quando há resposta aprovada, escalonamento ou limite atingido. O teste usa um fake que nunca aprova.

**EN:** How do you prevent a multi-agent supervisor from looping forever? Every worker call counts as a step, the limit must be a positive integer, and execution stops on approval, escalation, or the limit. A fake that never approves covers the boundary.
