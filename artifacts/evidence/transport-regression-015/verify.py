"""Run existing local checks while restoring prior standard outputs exactly."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
paths = [root / p for p in (
    'artifacts/evidence/check-fast.txt', 'artifacts/evidence/check-full.txt',
    'artifacts/runs/latest/results.json', 'artifacts/runs/latest/summary.md',
)]
original = {p: p.read_bytes() if p.exists() else None for p in paths}
results = []
try:
    env = os.environ | {'LLM_MODE': 'fake'}
    for script in ('scripts/check_fast.py', 'scripts/check_full.py'):
        command = [sys.executable, script]
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=300)
        name = Path(script).stem
        (evidence / (name + '.txt')).write_bytes(result.stdout + result.stderr)
        results.append({'command': command, 'cwd': str(root), 'exit_code': result.returncode})
        if result.returncode:
            break
finally:
    for path, content in original.items():
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.write_bytes(content)
    preservation = {str(p.relative_to(root)): {
        'before': hashlib.sha256(content).hexdigest() if content is not None else None,
        'after': hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,
    } for p, content in original.items()}
    (evidence / 'commands.json').write_text(json.dumps(results, indent=2))
    (evidence / 'preservation.json').write_text(json.dumps(preservation, indent=2))
assert all(v['before'] == v['after'] for v in preservation.values())
sys.exit(next((r['exit_code'] for r in results if r['exit_code']), 0))
