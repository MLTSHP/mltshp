#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

wait_for() {
    echo Waiting for $1 to listen on $2...
    while ! nc -z $1 $2; do echo sleeping; sleep 2; done
}

echo "--- Pulling base Docker image"
    docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
    docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest

echo "--- Launching Docker containers"
    docker compose -f .buildkite/docker-compose.yml up -d --build

echo "~~~ Waiting for containers to start"
    #wait_for localhost 3306
    #wait_for localhost 8000
    sleep 10

echo "+++ Running unit tests"
    docker exec -t buildkite-mltshp-1 ./run-tests.sh

echo "--- Submitting coverage data"
    docker exec -t -e BUILDKITE -e BUILDKITE_JOB_ID -e BUILDKITE_BRANCH -e COVERALLS_REPO_TOKEN buildkite-mltshp-1 ./coveralls-report.sh

echo "~~~ Stopping containers; cleanup"
    docker compose -f .buildkite/docker-compose.yml down
    docker container prune -f
