#!/bin/bash

set -eo pipefail

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

# Grab CI images
docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest
docker push mltshp/mltshp-web:latest

docker pull mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-worker:latest
docker push mltshp/mltshp-worker:latest

slackpost "#operations" "Build ${BUILDKITE_BUILD_NUMBER} has been pushed to Docker cloud: ${BUILDKITE_BUILD_URL}"
