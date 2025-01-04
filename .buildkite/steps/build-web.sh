#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

echo "--- Pulling base Docker image"
    docker pull mltshp/mltshp-web:latest

echo "+++ Building Docker image for web node"
    docker build -t mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} .

echo "--- Pushing build Docker image to Docker Hub"
    docker push mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
