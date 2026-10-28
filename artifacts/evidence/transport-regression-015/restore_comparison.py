"""Restore only the gate-generated LOC change in an initially clean artifact."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
relative = 'artifacts/runs/latest/COMPARISON.md'
path = root / relative
current = path.read_bytes()
command = ['git', 'show', '7ef72ab:' + relative]
result = subprocess.run(command, cwd=root, capture_output=True, check=True)
original = result.stdout
assert current == original.replace(b'| 99 | 60/60', b'| 118 | 60/60'), 'unexpected independent modification'
path.write_bytes(original)
report = {'command': command, 'cwd': str(root), 'exit_code': result.returncode,
          'reason': 'initial Git status clean; only runner-generated Core LOC changed',
          'original_sha256': hashlib.sha256(original).hexdigest(),
          'generated_sha256': hashlib.sha256(current).hexdigest(),
          'restored_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(Path(__file__).parent / 'comparison-restoration.json').write_text(json.dumps(report, indent=2))
assert report['original_sha256'] == report['restored_sha256']
