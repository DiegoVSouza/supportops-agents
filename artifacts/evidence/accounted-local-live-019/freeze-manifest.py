import hashlib
import json
import subprocess
from pathlib import Path

project = Path(__file__).resolve().parents[3]
root = project.parents[1]
source = list((project / "src/supportops_agents").rglob("*.py"))
source += [project / name for name in ("scripts/campaign_ledger.py", "scripts/run_live_campaign.py", "scripts/run_live_groq_eval.py", "scripts/local_operation.py", "agent/prompts/live-core.md", "evals/live-execution.json", "evals/live-campaign.json", "evals/datasets/live-v1/cases.jsonl", "evals/datasets/live-v1/manifest.json", "evals/rubrics/live-v1/rubric.md", "pyproject.toml", "uv.lock")]
source += [root / name for name in ("scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py", "shared/policies/groq-free-campaign.json")]
for repository, paths in ((project, [p for p in source if p.is_relative_to(project)]), (root, [p for p in source if not p.is_relative_to(project)])):
    names = [p.relative_to(repository).as_posix() for p in paths]
    for command in (["git", "ls-files", "--error-unmatch", "--", *names], ["git", "diff", "--quiet", "HEAD", "--", *names]):
        subprocess.run(command, cwd=repository, capture_output=True, check=True, timeout=15)
candidate = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip()
manifest = {"candidate_commit": candidate, "campaign_id": "local-operation-v1", "stage": "operation", "sampling_order": ["fixture-local-01", "fixture-local-02"], "trials_per_case": 1, "files_sha256": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in source}}
path = project / "artifacts/evals/live/local-operation-v1/manifest.json"
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("x", encoding="utf-8", newline="\n") as output:
    json.dump(manifest, output, indent=2, sort_keys=True)
    output.write("\n")
print(json.dumps({"status": "PASS", "candidate_commit": candidate, "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "files": len(source), "provider_accessed": False}))
