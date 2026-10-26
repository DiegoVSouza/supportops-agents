# Plan check — P01 phase 004

- Selected P01 because multi-agent orchestration is its product behavior and its six runners currently use only deterministic fakes.
- The live evaluation is deliberately restricted to one serial Core flow and one synthetic ticket; framework comparison remains offline.
- SDK calls are bounded by four worker steps, 256 output tokens each, 20s timeout, one configured key pass, and USD 0.01 estimated exposure.
- Path ownership is P01-local; no kit, sibling project, secret file, or golden fixture changes are permitted.
- Offline mocked tests precede the live preflight and run.

**Plan check: PASS.** The implementation may begin after this review.
