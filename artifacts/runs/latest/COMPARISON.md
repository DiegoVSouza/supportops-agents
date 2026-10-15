# Framework comparison

Run kind: synthetic fake-mode contract smoke. This is not a model-quality evaluation.
Qualitative fit columns describe this implementation and current official framework docs; they are not measured user-study results.

| Runner | Status | Ease (qualitative) | Control flow | State | Maturity | Observability | Source LOC | Cases matched | Fake steps | Accuracy | Tokens | Cost | Model latency |
|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|---|
| core | EXECUTED | Low setup; manual loop | Explicit bounded supervisor loop | In-memory typed state | Project-owned core | Common per-step trace | 99 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |
| langgraph | EXECUTED | Graph concepts required | Parallel fan-out, conditional edges, node retry | SQLite checkpoint and resumable interrupt | LangGraph 1.1.10 pinned | Graph checkpoints plus common trace | 196 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |
| crewai | EXECUTED | Flow decorator API | Start/listener Flow methods | Per-run Flow object | CrewAI 1.15.28 pinned | Common trace; Flow events not exported | 106 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |
| autogen | EXECUTED | Runtime registration and message types | Routed AutoGen Core messages | Runtime-local; no durable checkpoint | AutoGen 0.7.5 classic; successor noted in ADR-001 | Common trace; framework event logs not exported | 94 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |
| semantic_kernel | EXECUTED | Kernel and plugin registration | Sequential plugin invocation | Per-run Kernel | Semantic Kernel 1.45.0 classic; successor noted in ADR-001 | Common trace; no telemetry exporter configured | 80 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |
| llamaindex | EXECUTED | Typed event workflow API | Workflow steps and responder loop | Event-carried state | LlamaIndex 0.14.25 Workflows; QueryPipeline deprecated | Workflow events plus common trace | 130 | 3/3 | 2.7 | PENDING | PENDING | PENDING | PENDING |

## Selection notes

- `core`: use for minimal dependency footprint and explicit deterministic stop conditions.
- `langgraph`: choose when graph retries, SQLite checkpoint recovery, and HITL interrupts are the main requirements.
- `crewai`: choose role/task organization with structured Flow control.
- `autogen`: use the classic runtime for compatibility with existing AutoGen Core applications; see ADR-001.
- `semantic_kernel`: use the classic plugin/kernel model when integrating with existing Semantic Kernel code; see ADR-001.
- `llamaindex`: use Workflows when orchestration centers on retrieval and data components.

Fake step counts are observed worker calls from this synthetic run. Accuracy, tokens, cost, and model latency remain `PENDING`; fake mode does not measure model quality.
