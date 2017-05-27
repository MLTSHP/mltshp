#!/bin/sh
coverage run --source=handlers,models,tasks,lib test.py
coverage xml
