#!/bin/bash

set -euo pipefail

wait_for() {
    echo Waiting for $1 to listen on $2...
    while ! nc -z $1 $2; do echo sleeping; sleep 2; done
}

docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest

# launch fakes3/mysql/web app
docker compose -f .buildkite/docker-compose.yml up -d

# let's wait and allow mysql/fakes3 to spin up
#wait_for localhost 3306
#wait_for localhost 8000
sleep 10

# run our tests against it
docker exec -t buildkite_mltshp_1 ./run-tests.sh

# submit coverage data
docker exec -t -e BUILDKITE -e BUILDKITE_JOB_ID -e BUILDKITE_BRANCH -e COVERALLS_REPO_TOKEN buildkite_mltshp_1 ./coveralls-report.sh

# tear down containers
docker compose -f .buildkite/docker-compose.yml down

docker container prune -f
