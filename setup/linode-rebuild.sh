#!/bin/bash

LINODE_USER_ARG=""

if [ -f ".deploy.env" ]; then
    source .deploy.env
fi
if [ -n "$LINODE_USER" ]; then
    LINODE_USER_ARG="-u $LINODE_USER"
fi

# StackScript for "MLTSHP Web Node" - 77953
STACKSCRIPT="MLTSHP Web Node"

# Our NodeBalancer label
NODEBALANCER_NAME="mltshp-web-cluster"

# Docker image to deploy
DOCKER_IMAGE_NAME=${1:-mltshp/mltshp-web:latest}

# Prefix for all nodes attached to the NodeBalancer
NODE_PREFIX="mltshp-web"

# The Linode instance size for our web nodes
NODE_PLAN="linode1024"

# A public key for assigning to each node we rebuild (root account)
PUBLIC_KEY="setup/production/mltshp-web-key.pub"

# Get a list of nodes from the cluster
nodes=$( linode nodebalancer $LINODE_USER_ARG --action node-list --label "$NODEBALANCER_NAME" --port 80 | grep -oE $NODE_PREFIX-\\d+ | tail -r )
node_list=$( echo $nodes | xargs -- printf "%s, " | sed "s/, $//" )

echo "This script will rebuild all active MLTSHP web nodes"
echo "using a Docker Cloud image."
echo
echo "Docker image to deploy: $DOCKER_IMAGE_NAME"
echo "Linode NodeBalancer: $NODEBALANCER_NAME"
echo "Web Nodes to rebuild: ${node_list}"
echo "StackScript to deploy: $STACKSCRIPT"
echo "Public key to assign: $PUBLIC_KEY"
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

    echo "Rebuilding $NODE_NAME..."

    # Switch status of node to 'drain' to re-enable availability checks...
    linode nodebalancer \
        $LINODE_USER_ARG \
        --action node-update \
        --label "$NODEBALANCER_NAME" \
        --port 80 \
        --name "$NODE_NAME" \
        --mode "drain" > /dev/null

    linode --action rebuild \
        $LINODE_USER_ARG \
        --label "$NODE_NAME" \
        --plan "$NODE_PLAN" \
        --distribution "Ubuntu 16.04 LTS" \
        --pubkey-file $PUBLIC_KEY \
        --stackscript "$STACKSCRIPT" \
        --stackscriptjson "{\"docker_image_name\": \"$DOCKER_IMAGE_NAME\"}" \
        --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)" > /dev/null

    echo -n "Waiting for node availability..."
    sleep 60

    while true; do
        echo -n '.'
        status=$( linode nodebalancer $LINODE_USER_ARG --action node-list --port 80 --label "${NODEBALANCER_NAME}" --json | jq .\[\"${NODEBALANCER_NAME}\"\]\[\"80\"\]\[\"nodes\"\]\[\]\|select\(.name==\"$NODE_NAME\"\)\|select\(.status==\"UP\"\) )
        if [ -n "$status" ]; then
            echo 'UP'; break;
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
        json="{\"channel\": \"$channel\", \"icon_emoji\": \":mltshp:\", \"text\": \"$escapedText\"}"
        curl -s -d "payload=$json" "$SLACK_WEBHOOK_URL" > /dev/null
    fi
}

slackpost "#operations" "MLTSHP deployment starting for Docker image $DOCKER_IMAGE_NAME..."

for node in $nodes;
do
    rebuild_node $node
done

slackpost "#operations" "Docker image $DOCKER_IMAGE_NAME deployed to production."

echo "All nodes rebuilt!"
