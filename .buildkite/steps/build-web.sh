#!/bin/bash

set -euo pipefail

docker build -t mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} .
docker push mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}