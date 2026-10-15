# P01 package provenance: 0.1.1

- Source repository: `projects/p01`
- Source commit: `4c70b1ea3e23606dfe60ffae77567417de53a3f7` (`fix(p01): isolate run state and compare P00 golden cases`)
- Build command: `uv build --offline --out-dir artifacts/packages`
- Build exit code: `0`
- Artifact: `artifacts/packages/supportops_agents-0.1.1-py3-none-any.whl`
- Wheel SHA-256: `DD77E9B91F2D9BA7AC84178BBB557E0EA50BDE954554A528B4632DEC18DDB51F`

Consumer smoke command (isolated environment, no source-tree import):

```powershell
uv run --isolated --offline --with artifacts/packages/supportops_agents-0.1.1-py3-none-any.whl python -c "import importlib.metadata as m, pathlib, supportops_agents; from supportops_agents.contracts import Ticket; from supportops_agents.core import CoreTriageRunner; from supportops_agents.fakes import FakeLLMClient; module=pathlib.Path(supportops_agents.__file__).resolve(); result=CoreTriageRunner().run(Ticket('wheel-smoke','Invoice question','Synthetic check.'), llm=FakeLLMClient()); print('version='+m.version('supportops-agents')); print('module='+str(module)); print('result='+result.stop_reason); assert m.version('supportops-agents')=='0.1.1' and result.stop_reason=='approved' and not module.is_relative_to(pathlib.Path('src').resolve())"
```

- Consumer smoke exit code: `0`
- Output: package version `0.1.1`; module loaded from the isolated uv cache `site-packages`; synthetic ticket result `approved`.
- Publication status: local artifact only; not uploaded or published.
