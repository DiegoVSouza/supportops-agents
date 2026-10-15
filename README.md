# P01 — Multi-agent orchestration

This project implements SupportOps ticket triage with a deterministic supervisor-worker runner and a common `TriageRunner` contract. It keeps local domain doubles until P00 publishes an approved, versioned package. The current runnable path uses `LLM_MODE=fake` and Python's standard library; it does not call a model provider.

## Architecture

### Core supervisor-worker (implemented)

```mermaid
flowchart TD
  T[Ticket] --> S[Supervisor]
  S --> C[Classifier]
  C --> K[KB researcher]
  K --> B[Billing agent]
  B --> R[Responder]
  R -->|approved| D[Return response]
  R -->|needs review| R
  R -->|step limit| H[Escalate]
  C -->|risk flag| H
  B -->|approval required| H
```

### LangGraph (implemented)

```mermaid
flowchart LR
  C[Classifier] --> K[KB researcher]
  C --> B[Billing agent]
  K --> R[Responder]
  B --> R
  R -->|SQLite checkpoint and approval interrupt| H[Human review]
```

### CrewAI Flow (implemented)

```mermaid
flowchart TD
  F[Flow start: classifier] --> K[Flow listener: KB]
  K --> B[Flow listener: billing]
  B --> R[Flow listener: bounded responder]
  R --> O[Common triage result]
```

### AutoGen classic (implemented)

```mermaid
flowchart LR
  S[Supervisor] -->|WorkerRequest| A[AutoGen Core runtime]
  A --> C[Classifier worker]
  A --> K[KB worker]
  A --> B[Billing worker]
  A --> R[Responder worker]
  R --> O[Common triage result]
```

### Semantic Kernel classic (implemented)

```mermaid
flowchart LR
  S[Supervisor] --> K[Semantic Kernel]
  K --> P[Registered SupportOps plugin]
  P --> W[Injected worker client]
  W --> O[Common triage result]
```

### LlamaIndex Workflows (implemented)

```mermaid
flowchart LR
  S[StartEvent] --> C[Classifier step]
  C --> K[KB step]
  K --> B[Billing step]
  B --> R[Responder step loops to approval or limit]
  R --> E[StopEvent]
```

## Run

```powershell
uv sync --group frameworks
uv run --group frameworks python scripts/check_fast.py
$env:PYTHONPATH = "src"
uv run --group frameworks python -m supportops_agents.demo
uv run --group frameworks python -m supportops_agents.comparison --output artifacts/runs/latest
```

`uv run --group frameworks python scripts/check_full.py` runs fast tests, the synthetic comparison, the offline demo, and project structure checks. Checks save command, exit code, and output in `artifacts/evidence/`.

## Comparison status

| Runner | Status | Control-flow use case | Accuracy, tokens, cost, latency |
|---|---|---|---|
| Core | Executed | Small dependency-free supervisor loop | PENDING |
| LangGraph | Executed | Graph parallelism, retry, SQLite resume, HITL | PENDING |
| CrewAI Flow | Executed | Event-driven Flow listeners and bounded responder | PENDING |
| AutoGen classic | Executed | AutoGen Core runtime routed specialist worker messages | PENDING |
| Semantic Kernel classic | Executed | Registered kernel plugin for worker dispatch | PENDING |
| LlamaIndex Workflows | Executed | Typed workflow events and bounded responder loop | PENDING |

The generated `COMPARISON.md` reports a synthetic fake-mode contract smoke, not agent quality. All six control-flow runners execute their framework-native integration path with the same injected fake client. No model-quality accuracy, tokens, cost, or latency is claimed. See [ADR-001](docs/decisions/ADR-001-framework-scope.md) for why the Microsoft successor is not silently substituted for AutoGen/Semantic Kernel.

## Limitations and decisions

- P00's domain package is unavailable; local `Ticket` and `TriageDecision` doubles are project-owned and documented in `src/supportops_agents/contracts.py`.
- Comparison metrics for genuine model runs remain `PENDING`; all adapters have fake-mode contract coverage only.
- No live/replay provider mode, production traces, HTTP API, auth, queue, or formal agent evaluation is included.
- Python runtime observed: 3.13.12. Core has no third-party dependencies. Framework package versions are pinned in `uv.lock` and recorded in `docs/harness/sources.lock.json`.
