# Framework Smoke Completion

The v2 LangGraph workflow returned after four model calls, all recorded `ok` by the root usage ledger. The executor marked it incomplete because it expected a `status` property absent from the safe receipt schema. Fix validation to use the recorded attempt ID, safe reason, and usage. Exercise the four remaining runners in v3 under the original cumulative 20-call budget.
