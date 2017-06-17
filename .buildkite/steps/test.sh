#!/bin/bash

set -euo pipefail

docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest

cp .buildkite/settings.py .

mkdir -p /tmp/buildkite-mltshp-mysql
docker-compose -f .buildkite/docker-compose.yml up -d
docker exec -t buildkite_mltshp_1 ./run-tests.sh
rm -rf /tmp/buildkite-mltshp-mysql

# submit coverage data
docker exec -t -e BUILDKITE -e BUILDKITE_JOB_ID -e BUILDKITE_BRANCH -e COVERALLS_REPO_TOKEN buildkite_mltshp_1 ./coveralls-report.sh

docker-compose -f .buildkite/docker-compose.yml down
