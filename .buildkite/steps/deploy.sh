#!/bin/bash

set -eo pipefail

# Grab CI images
docker pull mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-web:latest
docker push mltshp/mltshp-web:latest

docker pull mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER}
docker tag mltshp/mltshp-worker:build-${BUILDKITE_BUILD_NUMBER} mltshp/mltshp-worker:latest
docker push mltshp/mltshp-worker:latest

# Rebuild Linode instances...
docker build -t linode .buildkite/linode-cli
export DEPLOY_PUBLIC_KEY="/tmp/setup/production/mltshp-web-key.pub"
alias linode="docker run -i --volume $PWD/setup/production:/tmp/setup/production --rm -e LINODE_API_KEY linode"

# Then deploy (rebuild script waits for user to press enter)
source ./setup/linode-rebuild.sh mltshp/mltshp-web:build-${BUILDKITE_BUILD_NUMBER}
