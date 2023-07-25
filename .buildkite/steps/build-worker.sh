#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

echo "--- Pulling base Docker image"
    docker pull mltshp/mltshp-worker:latest

echo "+++ Building Docker image for worker node"
    docker build -t mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} -f Dockerfile.worker .

echo "--- Pushing build Docker image to Docker Hub"
    docker push mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}