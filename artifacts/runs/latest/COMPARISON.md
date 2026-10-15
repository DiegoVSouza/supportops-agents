# Framework comparison

Run kind: synthetic fake-mode contract smoke. This is not a model-quality evaluation.
Qualitative fit columns describe this implementation and current official framework docs; they are not measured user-study results.

| Runner | Status | Ease (qualitative) | Control flow | State | Maturity | Observability | Source LOC | Cases matched | Fake steps | Accuracy | Tokens | Cost | Model latency |
|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|---|
| core | EXECUTED | Low setup; manual loop | Custom generic supervisor loop | In-memory typed state | Project-owned core | Common per-step trace | 99 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |
| langgraph | EXECUTED | Graph concepts required | Native graph fan-out, conditional edges, node retry | SQLite checkpoint and resumable interrupt | LangGraph 1.1.10 pinned | Graph checkpoints plus common trace | 214 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |
| crewai | EXECUTED | Flow decorator API | Native Flow events; worker orchestration is custom Python | Per-run Flow object | CrewAI 1.15.28 pinned | Common trace; Flow events not exported | 106 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |
| autogen | EXECUTED | Runtime registration and message types | Native Core runtime/messages; supervisor sequencing is custom | Runtime-local; no durable checkpoint | AutoGen 0.7.5 classic; successor noted in ADR-001 | Common trace; framework event logs not exported | 94 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |
| semantic_kernel | EXECUTED | Kernel and plugin registration | Native Kernel/plugin invocation around a generic sequential supervisor | Per-run Kernel | Semantic Kernel 1.45.0 classic; successor noted in ADR-001 | Common trace; no telemetry exporter configured | 80 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |
| llamaindex | EXECUTED | Typed event workflow API | Native typed Workflow steps; sequencing and responder loop are custom | Event-carried state | LlamaIndex 0.14.25 Workflows; QueryPipeline deprecated | Workflow events plus common trace | 130 | 60/60 eligible (60 cases) | 3.6 | PENDING | PENDING | PENDING | PENDING |

## Coverage and implementation boundaries

This run covers 60 P00 cases from installed wheel 1.0.1 (source commit 607b7603bd40728ffa58745badac0ffd10c70090, SHA-256 DF4292756676D02490A908B609B8F9474F35F3C5F56131809F3E4A83659B4795). P00 decision fields that P01 cannot represent are listed under `unsupported_semantics`; eligible action/category behavior is checked per case. Case outcomes are control-flow checks, not a representative benchmark.

The adapters do not delegate every orchestration concern to their framework. LangGraph uses native graph nodes, conditional edges, retries, checkpointing, and interrupts. CrewAI uses native Flow start/listener events but custom Python workers and supervisor logic. AutoGen uses its native Core runtime and routed messages while the supervisor sequences worker calls. Semantic Kernel supplies native Kernel/plugin invocation around a custom sequential supervisor. LlamaIndex uses native typed Workflow steps and events while the ordering and responder loop remain custom. Only the framework-specific capabilities listed in each row were exercised; other behavior is supplied by the shared adapter code.

## Selection notes

- `core`: use for minimal dependency footprint and explicit deterministic stop conditions.
- `langgraph`: choose when graph retries, SQLite checkpoint recovery, and HITL interrupts are the main requirements.
- `crewai`: choose role/task organization with structured Flow control.
- `autogen`: use the classic runtime for compatibility with existing AutoGen Core applications; see ADR-001.
- `semantic_kernel`: use the classic plugin/kernel model when integrating with existing Semantic Kernel code; see ADR-001.
- `llamaindex`: use Workflows when orchestration centers on retrieval and data components.

Fake step counts are observed worker calls from this synthetic run. Accuracy, tokens, cost, and model latency remain `PENDING`; fake mode does not measure model quality.
