#!/bin/bash

# exit if any command fails (e); strict variable substitution (u);
# set exit code to non-zero for any failed piped commands (o pipefail)
# See also: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

function slackpost {
    # Usage: slackpost <channel> <message>
    # Requires SLACK_WEBOOK_URL environment variable to be set
    # to a valid incoming webhook URL

    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        channel=$1
        shift
        text=$*

        escapedText=$(echo $text | sed 's/"/\"/g' | sed "s/'/\'/g" )
        json="{\"channel\": \"$channel\", \"icon_emoji\": \":mltshp:\", \"text\": \"$escapedText\"}"
        curl -s -d "payload=$json" "$SLACK_WEBHOOK_URL" > /dev/null
    fi
}

echo "--- Pulling Docker image for web node build ${BUILDKITE_BUILD_NUMBER}"
    docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}

echo "--- Tagging Docker image as latest and pushing to Docker Hub"
    docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest
    docker push mltshp/mltshp-web:latest

echo "--- Pulling Docker image for worker node build ${BUILDKITE_BUILD_NUMBER}"
    docker pull mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}

echo "--- Tagging Docker image as latest and pushing to Docker Hub"
    docker tag mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-worker:latest
    docker push mltshp/mltshp-worker:latest

echo "--- Posting Slack alert!"
    slackpost "#operations" "Build ${BUILDKITE_BUILD_NUMBER} has been pushed to Docker cloud by ${BUILDKITE_UNBLOCKER}: ${BUILDKITE_BUILD_URL}"
