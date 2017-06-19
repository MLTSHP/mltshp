#!/bin/bash

set -euo pipefail

docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest

# create a place to hold the mysql data
mkdir -p /tmp/buildkite-mltshp-mysql

# launch fakes3/mysql/web app
docker-compose -f .buildkite/docker-compose.yml up -d

# run our tests against it
docker exec -t buildkite_mltshp_1 ./run-tests.sh

# submit coverage data
docker exec -t -e BUILDKITE -e BUILDKITE_JOB_ID -e BUILDKITE_BRANCH -e COVERALLS_REPO_TOKEN buildkite_mltshp_1 ./coveralls-report.sh

# tear down containers
docker-compose -f .buildkite/docker-compose.yml down

# remove mysql data
sudo rm -rf /tmp/buildkite-mltshp-mysql
