# Phase 002 — Local package for P05 integration

## Goal
Build the P01 dependency-free public triage core as a versioned wheel so P05 can install and exercise it without sibling-repository imports or external publication.

## Acceptance criteria
- The wheel is named and versioned from project metadata and contains the documented public contracts, core runner, and fake client.
- The wheel has no third-party runtime dependencies; framework adapters remain optional extras from P01's comparison environment and are not falsely bundled as required dependencies.
- An isolated virtual environment installs the wheel from a local artifact and imports/runs the core contract without a source checkout or `PYTHONPATH`.
- Evidence records exact commands, exit codes, outputs, package version, source commit, and SHA-256 of the wheel.
- The local wheel and provenance are retained in P01 artifacts; nothing is published.

## Scope boundary
This package exports P01's SupportOps orchestration contracts and core runner. It does not replace the P00 domain package. P05 may consume it only as a separately installed versioned dependency and must retain source commit and artifact hash provenance.
