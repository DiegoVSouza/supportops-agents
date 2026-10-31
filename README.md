# P01 — Multi-agent orchestration

<!-- case:start -->
## The case

- **Problem.** Multi-agent triage needs a bounded loop, and framework demos rarely compare on one contract.
- **Decision.** A supervisor delegates to specialist workers with shared state and hard step limits. Every framework adapter sits behind one `TriageRunner` contract, so the choice is measured.
- **Measured.** 119 offline tests pass in a clean clone (`LLM_MODE=fake`, one test skipped with a stated reason outside the lab). One live synthetic workflow: four provider attempts, 1274 input and 261 output tokens (`docs/harness/progress.md`, phase 027). No model-quality claim.
- **Run it.** `uv sync --locked --all-groups && uv run --locked python scripts/check_fast.py`
- **Limits.** Live operation evidence is transport and accounting only. Quality, human review and promotion are pending.
- **Docs.** [Architecture](docs/architecture.md), [decisions](docs/decisions).
<!-- case:end -->

<!-- flow:start -->
## How it works

Generated from the same data as the diagram on the portfolio site (`projects/agents/`), so the two cannot drift.

```mermaid
flowchart LR
  contract["TriageRunner contract"]
  supervisor["Supervisor"]
  classifier["Classifier"]
  researcher["Researcher"]
  billing["Billing agent"]
  responder["Responder"]
  stop["Stop condition"]
  contract --> supervisor
  supervisor --> classifier
  classifier --> researcher
  researcher --> billing
  billing --> responder
  responder --> stop
```
<!-- flow:end -->

This project implements SupportOps ticket triage with a deterministic supervisor-worker runner and a common `TriageRunner` contract. Runtime `Ticket` and `TriageDecision` remain P01-local compatibility doubles. P01 consumes the approved P00 1.0.1 wheel in an isolated environment to export its versioned golden set; version, source commit, SHA-256, and consumer command are in `docs/harness/sources.lock.json`. The P01 runtime uses `LLM_MODE=fake` and makes no model-provider calls.

## Problem

Support triage often needs several bounded steps, but framework examples rarely show how to keep contracts, retries, approval pauses, and termination behavior comparable.

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

## Quickstart

```powershell
uv sync --group frameworks
uv run --group frameworks python scripts/check_fast.py
$env:PYTHONPATH = "src"
uv run --group frameworks python -m supportops_agents.demo
uv run --group frameworks python -m supportops_agents.comparison --output artifacts/runs/latest
```

`uv run --group frameworks python scripts/check_full.py` runs fast tests, the synthetic comparison, the offline demo, and project structure checks. Checks save command, exit code, and output in `artifacts/evidence/`.

## Results

| Runner | Status | Control-flow use case | Accuracy, tokens, cost, latency |
|---|---|---|---|
| Core | Executed | Small dependency-free supervisor loop | PENDING |
| LangGraph | Executed | Graph parallelism, retry, SQLite resume, HITL | PENDING |
| CrewAI Flow | Executed | Event-driven Flow listeners and bounded responder | PENDING |
| AutoGen classic | Executed | AutoGen Core runtime routed specialist worker messages | PENDING |
| Semantic Kernel classic | Executed | Registered kernel plugin for worker dispatch | PENDING |
| LlamaIndex Workflows | Executed | Typed workflow events and bounded responder loop | PENDING |

The generated `COMPARISON.md` exercises all 60 versioned P00 cases in fake mode and reports per-case action/category behavior and unsupported P00 semantics. It distinguishes framework-native features from orchestration supplied by P01 wrappers. This is a deterministic control-flow comparison, not agent quality. Accuracy, tokens, cost, and model latency remain `PENDING`. See [ADR-001](docs/decisions/ADR-001-framework-scope.md) for why the Microsoft successor is not silently substituted for AutoGen/Semantic Kernel.

## Design decisions

- P01 runtime uses local `Ticket` and `TriageDecision` doubles documented in `src/supportops_agents/contracts.py`; only comparison fixture export uses the installed P00 wheel. A shared runtime install is blocked by P00's Pydantic 2.14.1 pin and CrewAI's `<2.13` constraint.
- Comparison metrics for genuine model runs remain `PENDING`; all adapters have fake-mode contract coverage only.
- A guarded Core provider boundary is implemented and tested offline. Its execution manifest is disabled pending durable campaign dispatch, allocation and candidate freeze. The legacy direct-SDK smoke now fails before credentials/SDK access. No replay provider mode, production traces, HTTP API, auth, queue or completed formal live evaluation is included.
- Python runtime observed: 3.13.12. Core has no third-party dependencies. Framework package versions are pinned in `uv.lock` and recorded in `docs/harness/sources.lock.json`.

## Testing

`uv run --group frameworks python scripts/check_full.py` runs the deterministic suite, synthetic comparison, local demo, and structure checks. The current fast suite covers 20 contract and recovery tests.

## Limitations

The comparison measures deterministic control flow. Accuracy, tokens, cost, and model latency remain `PENDING` until a traceable model run is authorized.
