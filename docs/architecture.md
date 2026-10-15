# Architecture

P01 exposes a small common contract (`Ticket`, `TriageDecision`, `TriageResult`, and `TriageRunner`) and a deterministic fake-mode supervisor-worker implementation. Each worker receives a snapshot of shared state. The runner counts every agent call and has three explicit stop outcomes: approved, escalated, and max_steps.

The core is independent of any provider SDK. P01 runtime contracts remain local compatibility doubles. The P00 1.0.1 wheel is installed in an isolated consumer environment only to export the 60-case golden fixture; wheel version, source commit, and SHA-256 are recorded. No relative sibling-source imports are used. The shared runtime environment cannot currently combine P00's Pydantic 2.14.1 pin with CrewAI's Pydantic `<2.13` requirement.

Six runners are executable: the core plus LangGraph, CrewAI Flow, AutoGen Core classic, Semantic Kernel classic, and LlamaIndex Workflows. The adapter registry exposes their stable identifiers. All six run the 60 P00 golden cases in fake mode. Per-case records label fields that the P01 contract cannot express. The original comparison targets remain separate from Microsoft Agent Framework; see [ADR-001](decisions/ADR-001-framework-scope.md).
