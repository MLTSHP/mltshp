#!/bin/bash

set -euo pipefail

docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest

# launch fakes3/mysql/web app
docker-compose -f .buildkite/docker-compose.yml up -d

# let's wait a few seconds to allow mysql/fakes3 to spin up
sleep 5

# run our tests against it
docker exec -t buildkite_mltshp_1 ./run-tests.sh

# submit coverage data
docker exec -t -e BUILDKITE -e BUILDKITE_JOB_ID -e BUILDKITE_BRANCH -e COVERALLS_REPO_TOKEN buildkite_mltshp_1 ./coveralls-report.sh

# tear down containers
docker-compose -f .buildkite/docker-compose.yml down
