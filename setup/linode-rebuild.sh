#!/bin/bash

LINODE_USER_ARG=""

if [ -f ".deploy.env" ]; then
    source .deploy.env
fi
if [ -n "$LINODE_USER" ]; then
    LINODE_USER_ARG="-u $LINODE_USER"
fi

# Get latest commit to master
GITHUB_COMMIT_SHA=$( curl -s https://api.github.com/repos/MLTSHP/mltshp/commits/master | jq '.sha' | sed 's/"//g' );
#DOCKER_WEB_SHA=$( )
#DOCKER_WORKER_SHA=$( )

# Our NodeBalancer label
NODEBALANCER_NAME="mltshp-web-cluster"

# Docker image to deploy
DOCKER_IMAGE_NAME=${1:-mltshp/mltshp-web:latest}
WORKER_IMAGE_NAME=$( echo $DOCKER_IMAGE_NAME | sed "s/-web/-worker/" )

# The Linode instance size for our web nodes
NODE_PLAN="linode1024"

# A public key for assigning to each node we rebuild (root account)
PUBLIC_KEY="setup/production/mltshp-web-key.pub"

# Get a list of nodes from the cluster
nodes=$( linode nodebalancer $LINODE_USER_ARG --action node-list --label "$NODEBALANCER_NAME" --port 80 | grep -oE mltshp-web-\\d+ | tail -r )
node_list=$( echo $nodes | xargs -- printf "%s, " | sed "s/, $//" )

echo "This script will rebuild all active MLTSHP web nodes"
echo "using a Docker Cloud image."
echo
echo "GitHub master commit: $GITHUB_COMMIT_SHA"
echo "Web Docker image to deploy: $DOCKER_IMAGE_NAME"
echo "Web Nodes to rebuild: ${node_list}"
echo "Worker Docker image to deploy: $WORKER_IMAGE_NAME"
echo "Worker Node to rebuild: mltshp-worker-1"
echo
echo "Press Enter to continue or ^C to abort..."
read

function rebuild_node() {
    NODE_NAME=$1

    echo "Removing $NODE_NAME from rotation..."

    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "reject" > /dev/null

    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 443 \
        --name "$NODE_NAME" \
        --mode "reject" > /dev/null

    echo "Rebuilding $NODE_NAME..."

    # Switch status of node to 'drain' to re-enable availability checks...
    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "drain" > /dev/null

    # Switch status of node to 'drain' to re-enable availability checks...
    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 443 \
        --name "$NODE_NAME" \
        --mode "drain" > /dev/null

    linode --action rebuild \
        $LINODE_USER_ARG \
        --label "$NODE_NAME" \
        --plan "$NODE_PLAN" \
        --distribution "Ubuntu 16.04 LTS" \
        --pubkey-file $PUBLIC_KEY \
        --stackscript "MLTSHP Web Node" \
        --stackscriptjson "{\"docker_image_name\": \"$DOCKER_IMAGE_NAME\"}" \
        --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)" > /dev/null

    echo -n "Waiting for node availability..."
    sleep 60

    # Wait for availability of node on both port 80 and 443
    while true; do
        echo -n '.'
        status=$( linode nodebalancer $LINODE_USER_ARG --action node-list --port 80 --label "${NODEBALANCER_NAME}" --json | jq .\[\"${NODEBALANCER_NAME}\"\]\[\"80\"\]\[\"nodes\"\]\[\]\|select\(.name==\"$NODE_NAME\"\)\|select\(.status==\"UP\"\) )
        if [ -n "$status" ]; then
            while true; do
                echo -n '.'
                status=$( linode nodebalancer $LINODE_USER_ARG --action node-list --port 443 --label "${NODEBALANCER_NAME}" --json | jq .\[\"${NODEBALANCER_NAME}\"\]\[\"443\"\]\[\"nodes\"\]\[\]\|select\(.name==\"$NODE_NAME\"\)\|select\(.status==\"UP\"\) )
                if [ -n "$status" ]; then
                    echo 'UP'; break;
                fi
                sleep 10
            done
            break
        fi
        sleep 10
    done

    # Put the node back into rotation
    echo "Placing $NODE_NAME back in rotation..."
    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "accept" > /dev/null

    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 443 \
        --name "$NODE_NAME" \
        --mode "accept" > /dev/null

    slackpost "#operations" "✅️ $NODE_NAME rebuilt and live"

    echo "Node $NODE_NAME rebuilt!"
    echo
}

function rebuild_worker {
    NODE_NAME=$1

    echo "Rebuilding $NODE_NAME..."

    linode --action rebuild \
        $LINODE_USER_ARG \
        --label "$NODE_NAME" \
        --plan "linode1024" \
        --distribution "Ubuntu 16.04 LTS" \
        --pubkey-file $PUBLIC_KEY \
        --stackscript "MLTSHP Worker Node" \
        --stackscriptjson "{\"docker_image_name\": \"$WORKER_IMAGE_NAME\"}" \
        --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)" > /dev/null

    slackpost "#operations" "✅️ $NODE_NAME rebuilding..."
}

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

slackpost "#operations" "MLTSHP deployment starting for Docker image $DOCKER_IMAGE_NAME (Git master is: $GITHUB_COMMIT_SHA)..."

# Also rebuild the worker node with latest docker image...
rebuild_worker "mltshp-worker-1"

for node in $nodes;
do
    rebuild_node $node
done

slackpost "#operations" "Docker image $DOCKER_IMAGE_NAME deployed to production (Git master is: $GITHUB_COMMIT_SHA)."

echo "All nodes rebuilt!"
