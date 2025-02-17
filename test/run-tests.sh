#!/bin/bash

export PYTHONUNBUFFERED=1

# These commands expect to be run in a Docker container
pip3 install --break-system-packages -r requirements-test.txt;
coverage run --source=handlers,models,tasks,lib test.py
coverage xml
