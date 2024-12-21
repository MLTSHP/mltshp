#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

export PYTHONUNBUFFERED=1

# This expects to be run in a Docker container
/srv/venv/bin/pip install -r requirements-test.txt;

coverage run --source=handlers,models,tasks,lib test.py
coverage xml
