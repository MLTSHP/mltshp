#!/bin/bash

set -euo pipefail

# pull prior image to populate layer cache
docker pull mltshp/mltshp-worker:latest

docker build -t mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} -f Dockerfile.worker .
docker push mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}