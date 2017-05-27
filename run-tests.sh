#!/bin/sh
pip install -r requirements-test.txt
coverage run --source=handlers,models,tasks,lib test.py
coverage xml
