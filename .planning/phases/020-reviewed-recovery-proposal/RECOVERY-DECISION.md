# Disabled diagnostic recovery proposal

The original `local-operation-v1/fixture-local-01/1` remains INCOMPLETE. Its response and failure category cannot be reconstructed from the retained evidence. The original candidate `d17923e0c8fe5992ebac8e25b994e746e9f25ba2`, manifest and two successful provider receipts remain immutable. The logical four-call reservation (8192 input/1024 output) remains fully charged.

Proposed decision: accept the irrecoverable diagnostic gap and permit one separate diagnostic workflow after implementing a reviewed exception. This is not a repeat or replacement of the original case. It must use a new frozen corrected candidate and a distinct explicitly authorized diagnostic scope, preserve the original failure stop by default, and bind the exception to the exact original receipt/history digest and retained reserve. No generic bypass, original-ID change, counter reset or reserve release is permitted.

Finite arithmetic: original four logical calls retained plus at most four new diagnostic calls equals the already allocated eight. Original two actual provider calls plus at most four new calls equals at most six provider calls. No additional funding or holdout/confirmation use is required; paid authorization remains USD 0 and billed amount unknown.

Before dispatch: implement disabled-by-default exception controls; test wrong identity/history, original replay denial, single-use approval, crash/unknown stop, source/manifest binding and exact diagnostics without content; run the isolated full gate; freeze source/manifest; acquire the shared lease and reserve the full new workflow before startup. Stop after that one workflow, including on any error. Preserve every outcome and never replay semantics.

Current execution remains disabled. The requested user decision concerns only this separately reviewed diagnostic scope. Declining leaves the original live operation INCOMPLETE and does not block P00/P02–P05. Human quality, dataset/rubric/independent review, holdout and promotion remain pending regardless of this decision.

Evidence: `artifacts/evidence/recovery-proposal-020/proposal.json`, read-only exact SQLite audit and protected-output preservation hashes. The candidate for the proposed workflow is intentionally not invented before exception implementation and validation.
