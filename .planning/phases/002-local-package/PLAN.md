# Phase 002 plan

## Task 1 — Package boundary and metadata
- Enable the standard `src/supportops_agents` package with the bundled uv build backend pinned to the installed uv version.
- Preserve package version `0.1.0`; no public contract changes.
- Review: import path and metadata align with the existing module layout; no framework adapter is imported eagerly by package initialization.

## Task 2 — Build and isolated installation
- Build a local wheel, create a clean venv, install the wheel without network resolution, and exercise the public fake-mode core runner.
- Stop if build requires unapproved network access or the isolated import resolves to the source checkout.

## Task 3 — Provenance and verification
- Save command/exit/output, package version, source commit and artifact SHA-256.
- Run the isolated smoke and relevant P01 checks, inspect staged files, and commit the artifact/provenance locally.

## Ownership
- `allowed_write_paths`: `projects/p01/**`
- `forbidden_changes`: root, harness kit, shared/global files, sibling projects, public contracts, external registries.
- Dependencies: Python 3.13, uv 0.12.7; package runtime is standard library only. Framework comparison dependencies are not required for P05 core integration.
