#!/bin/sh

export PYTHONUNBUFFERED=1

# These commands expect to be run in a Docker container
pip3 install --break-system-packages -r test/requirements.txt
coverage run --source=handlers,models,tasks,lib test/test.py
coverage xml
