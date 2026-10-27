# Phase 009 plan check

Method: manual review by the implementing agent against lab/P01 instructions, the original live-readiness protocol, phase 008, existing Core and direct SDK interfaces, and root transport protocol v1. This is not independent review and has no subprocess exit code.

Result: PASS for planning. Three tasks with concrete project-owned paths; zero provider/paid budget; unchanged dataset, rubric and Core/framework semantics; disabled owner manifest; no root/sibling source imports; and explicit stop/validation conditions. The old single-ticket smoke is not an allocation for new calls. Full durable campaign dispatch and independent verification remain INCOMPLETE/PENDING.

P01's initial status was clean and HEAD was `60be3e028cd39eb4314e4dcc4e46be018ec57a35`. No service change is planned. Existing Docker identities were inventoried in the preceding P00 handoff and are not operated by this phase.

Baseline command: `uv run --locked --group frameworks python scripts/check_fast.py`; exit 0; 40 tests passed. Complete command/subcommand output is saved in `baseline-fast.txt`. The existing transient-rotation test describes the old unrestricted client; phase 009 replaces that expected behavior with explicit no-retry/no-SDK tests under the current authorization, preserving its historical baseline evidence.
