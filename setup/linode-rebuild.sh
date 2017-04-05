#!/bin/bash

if [ ! -z "$(git status --untracked-files=no --porcelain)" ]; then
    echo "You have uncommitted changes in this branch."
    exit 1
fi

# StackScript for "MLTSHP Web Node" - 77953
STACKSCRIPT="MLTSHP Web Node"

# Our NodeBalancer label
NODEBALANCER_NAME="mltshp-web-cluster"

# Docker image to deploy
DOCKER_IMAGE_NAME=${1:-mltshp/mltshp-web:latest}

# Prefix for all nodes attached to the NodeBalancer
NODE_PREFIX="mltshp-web"

# A public key for assigning to each node we rebuild (root account)
PUBLIC_KEY="setup/mltshp-web-key.pub"

echo "This script will rebuild all active MLTSHP web nodes"
echo "using the latest Docker image."
echo
echo "Docker image to deploy: $DOCKER_IMAGE_NAME"
echo "Linode NodeBalancer: $NODEBALANCER_NAME"
echo "Web Nodes to rebuild: ${NODE_PREFIX}-*"
echo "StackScript to deploy: $STACKSCRIPT"
echo "Public key to assign: $PUBLIC_KEY"
echo
echo "Press Enter to continue or ^C to abort..."
read

function rebuild_node() {
    NODE_NAME=$1

    echo "Removing $NODE_NAME from rotation..."

    linode nodebalancer \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "reject"

    echo "Rebuilding $NODE_NAME..."

    # Switch status of node to 'drain' to re-enable availability checks...
    linode nodebalancer \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "drain"

    linode --action rebuild \
        --label "$NODE_NAME" \
        --plan linode2048 \
        --distribution "Ubuntu 16.04 LTS" \
        --pubkey-file $PUBLIC_KEY \
        --stackscript "$STACKSCRIPT" \
        --stackscriptjson '{"DOCKER_IMAGE_NAME": "$DOCKER_IMAGE_NAME"}' \
        --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)"

    echo -n "Waiting for node availability..."
    sleep 60

    while true; do
        echo -n '.'
        status=$( linode nodebalancer --action node-list --port 80 --label "${NODEBALANCER_NAME}" --json | jq .\[\"${NODEBALANCER_NAME}\"\]\[\"80\"\]\[\"nodes\"\]\[\]\|select\(.name==\"$NODE_NAME\"\)\|select\(.status==\"UP\"\) )
        if [ -n "$status" ]
            then echo 'UP'; break;
        fi
        sleep 10
    done

    # Put the node back into rotation
    echo "Placing $NODE_NAME back in rotation..."
    linode nodebalancer \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "accept"

    echo "Node $NODE_NAME rebuilt!"
    echo
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
        json="{\"channel\": \"#$channel\", \"icon_emoji\": \":mltshp:\", \"text\": \"$escapedText\"}"
        curl -s -d "payload=$json" "$SLACK_WEBHOOK_URL" > /dev/null
    fi
}

slackpost "technology" "MLTSHP deployment starting for Docker image $DOCKER_IMAGE_NAME..."

# Get a list of nodes from the cluster
nodes=$( linode nodebalancer --action node-list --label "$NODEBALANCER_NAME" --port 80 | grep -oE $NODE_PREFIX-\\d+ | tail -r )
for node in $nodes;
do
    rebuild_node $node
done

slackpost "technology" "Docker image $DOCKER_IMAGE_NAME deployed to production."

echo "All nodes rebuilt!"
