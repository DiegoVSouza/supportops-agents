# Architecture

P01 exposes a small common contract (`Ticket`, `TriageDecision`, `TriageResult`, and `TriageRunner`) and a deterministic fake-mode supervisor-worker implementation. Each worker receives a snapshot of shared state. The runner counts every agent call and has three explicit stop outcomes: approved, escalated, and max_steps.

The core is independent of any provider SDK. Local compatibility doubles stand in for P00 until its package is approved and installed by version; there are no relative imports across repositories.

Six runners are executable: the core plus LangGraph, CrewAI Flow, AutoGen Core classic, Semantic Kernel classic, and LlamaIndex Workflows. The adapter registry exposes their stable identifiers. They run the same synthetic golden cases in fake mode. The original comparison targets remain separate from Microsoft Agent Framework; see [ADR-001](decisions/ADR-001-framework-scope.md).
