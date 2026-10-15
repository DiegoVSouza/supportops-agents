command=git rev-parse --show-toplevel
output=C:/estudo/Golpe/lab/projects/p01
exit_code=0

command=git branch --show-current
output=main
exit_code=0

command=git rev-list --max-parents=0 HEAD
output=58990090469a6147e36a788ddcff61cfc4d3a5cd
exit_code=0

command=git hook run commit-msg -- <invalid message>
exit_code=1

command=git hook run commit-msg -- <valid Conventional Commit>
exit_code=0

command=git check-ignore --no-index sensitive/venv/cache fixtures
output:
.env
.env.local
.venv/pyvenv.cfg
__pycache__/x.pyc
.pytest_cache/x
.ruff_cache/x
exit_code=0
