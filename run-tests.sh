#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

export PYTHONUNBUFFERED=1

# These commands expect to be run in a Docker container (virtual env installed to /srv/venv)
/srv/venv/bin/pip install -r requirements-test.txt;
/srv/venv/bin/coverage run --source=handlers,models,tasks,lib test.py
/srv/venv/bin/coverage xml
