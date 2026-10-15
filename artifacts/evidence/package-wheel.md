# P01 local wheel provenance and smoke evidence

## Provenance
- Package: `supportops-agents==0.1.0`
- Source commit: `af06f4c564d2e601ac8009ecb32ae7e529b72c83` (`build(package): prepare local triage wheel`); package source was clean at this commit.
- Artifact: `artifacts/packages/supportops_agents-0.1.0-py3-none-any.whl`
- SHA-256: `9f360e98fc1df9d9d10ccdab51f0af0cc5f1a17cd49cefec9e2e3a8a4bed8b`
- Runtime requirements: none; the P01 framework adapters remain opt-in and are not needed by the core wheel.
- Distribution: local file only; no registry or publication.

## Commands and results
- `uv build --wheel --out-dir artifacts/packages` — exit 0; output: `Building wheel...` and `Successfully built artifacts\packages\supportops_agents-0.1.0-py3-none-any.whl`.
- `uv venv --python 3.13 .venv-wheel-smoke-af06f4c` — exit 0; created isolated Python 3.13.12 environment.
- `\.venv-wheel-smoke-af06f4c\Scripts\python.exe -m pip install --no-deps --no-index artifacts\packages\supportops_agents-0.1.0-py3-none-any.whl` — exit 1; the fresh environment has no pip module. No network access was attempted.
- `uv pip install --python .venv-wheel-smoke-af06f4c\Scripts\python.exe --no-deps --no-index artifacts\packages\supportops_agents-0.1.0-py3-none-any.whl` — exit 0; installed `supportops-agents==0.1.0` from the local wheel.
- `Push-Location artifacts/evidence; $env:PYTHONPATH = $null; ..\..\.venv-wheel-smoke-af06f4c\Scripts\python.exe -c 'import pathlib, supportops_agents; from supportops_agents import Ticket, get_runner; from supportops_agents.fakes import FakeLLMClient; module=pathlib.Path(supportops_agents.__file__).resolve(); assert "site-packages" in str(module); result=get_runner("core").run(Ticket("wheel-smoke", "Duplicate", "Charged twice"), llm=FakeLLMClient()); assert result.stop_reason == "approved"; print(f"module={module}"); print("version=0.1.0"); print("runner=core"); print(f"stop_reason={result.stop_reason}"); print(f"steps={len(result.trace)}")'; Pop-Location` — exit 0; run outside the source tree with `PYTHONPATH` cleared. It asserts the module path is in the isolated environment's `site-packages` and result stop reason is `approved`; output:

```text
module=C:\estudo\Golpe\lab\projects\p01\.venv-wheel-smoke-af06f4c\Lib\site-packages\supportops_agents\__init__.py
version=0.1.0
runner=core
stop_reason=approved
steps=4
```

- `uv lock --check` — exit 0; output: `Resolved 220 packages in 0.88ms`.
- `Get-FileHash artifacts/packages/supportops_agents-0.1.0-py3-none-any.whl -Algorithm SHA256` — exit 0; hash matches the provenance above.
- `python -m zipfile -l artifacts/packages/supportops_agents-0.1.0-py3-none-any.whl` — exit 0; contains the contracts, core runner, fake client, registry, and optional framework adapter modules.

## P05 integration boundary
P05 can install and use the core wheel for orchestration. It still must obtain P00's approved domain package independently; this wheel does not replace that package. P05 must record the version, source commit, and artifact hash when installing this wheel.
