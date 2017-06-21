#!/bin/bash

set -euo pipefail

# pull prior image to populate layer cache
docker pull mltshp/mltshp-web:latest

docker build -t mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} .
docker push mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}