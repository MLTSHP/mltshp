#!/bin/bash

set -euo pipefail

docker build -t mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} -f Dockerfile.worker .
docker push mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}