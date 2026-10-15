# Phase 002 verification

## Package build
- `uv build --wheel --out-dir artifacts/packages` — produce the versioned local wheel.

## Isolated integration smoke
- Create a fresh venv under `artifacts/venvs/p01-wheel-smoke`, install the wheel with pip `--no-deps`, clear `PYTHONPATH`, and invoke the public `Ticket`, `FakeLLMClient`, and `get_runner("core")` API.
- Verify imported module path points inside the isolated venv's site-packages and result stop reason is `approved`.

## Gate
- Retain exact command, exit code, stdout/stderr, source commit, version, and wheel SHA-256 in `artifacts/evidence/package-wheel.md`.
- No package publication, push, or external registry use.

## Result
- P01 wheel build and isolated installation smoke: passed; see `artifacts/evidence/package-wheel.md`.
- P05 consumption of the installed wheel: pending consumer integration. P00's approved domain package is still required separately.
