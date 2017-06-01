#!/bin/bash

LINODE_USER_ARG=""

if [ -f ".deploy.env" ]; then
    source .deploy.env
fi
if [ -n "$LINODE_USER" ]; then
    LINODE_USER_ARG="-u $LINODE_USER"
fi

# Our NodeBalancer label
NODEBALANCER_NAME="mltshp-web-cluster"

# The Linode instance size for our web nodes
NODE_PLAN="linode1024"

# Get latest commit to master... yields the first 8 characters of the sha1 hash of master
GITHUB_COMMIT_SHA=$( curl -s https://api.github.com/repos/MLTSHP/mltshp/commits/master | jq '.sha' | sed 's/"//g' | cut -c 1-8 );

# Docker image to deploy (defaults to "mltshp/mltshp-web:latest")
DOCKER_IMAGE_NAME=${1:-mltshp/mltshp-web:latest}
WORKER_IMAGE_NAME=$( echo $DOCKER_IMAGE_NAME | sed "s/-web/-worker/" )

# Get the Docker cloud sha1 for the "latest" build to compare with Github
#DOCKER_WEB_SHA=$( )
#DOCKER_WORKER_SHA=$( )

# A public key for assigning to each node we rebuild (root account)
PUBLIC_KEY="setup/production/mltshp-web-key.pub"

# Get a list of worker nodes from linode
worker_nodes=$( linode linode $LINODE_USER_ARG --action list | grep -oE mltshp-worker-\\d+ )

# convert newline string to a real array
worker_nodes=(${worker_nodes//$'\n'/ })

# Get a list of web nodes from the cluster
web_nodes=$( linode nodebalancer $LINODE_USER_ARG --action node-list --label "$NODEBALANCER_NAME" --port 80 | grep -oE mltshp-web-\\d+ | tail -r )

# convert newline string to a real array
web_nodes=(${web_nodes//$'\n'/ })

function echo_with_delimiter {
    local d=$1
    shift
    echo -n "$1"
    shift
    printf "%s" "${@/#/$d}"
    echo
}

function rebuild_web_node_step {
    for NODE_NAME in $@; do
        echo "Rebuilding $NODE_NAME..."

        # Switch status of node to 'drain' to re-enable availability checks...
        linode nodebalancer \
            $LINODE_USER_ARG \
            --action node-update \
            --label "$NODEBALANCER_NAME" \
            --port 80 \
            --name "$NODE_NAME" \
            --mode "drain" > /dev/null

        # run this command in the background; no need to wait for it
        # to completely finish here
        linode --action rebuild \
            $LINODE_USER_ARG \
            --label "$NODE_NAME" \
            --plan "$NODE_PLAN" \
            --distribution "Ubuntu 16.04 LTS" \
            --pubkey-file $PUBLIC_KEY \
            --stackscript "MLTSHP Web Node" \
            --stackscriptjson "{\"docker_image_name\": \"$DOCKER_IMAGE_NAME\"}" \
            --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)" > /dev/null &
    done
}

function wait_for_status {
    status_value=$1
    shift
    for NODE_NAME in $@; do
        echo -n "Waiting for node $NODE_NAME to report as $status_value..."

        # Wait for availability of node on port 80
        while true; do
            echo -n '.'
            status=$( linode nodebalancer $LINODE_USER_ARG --action node-list --port 80 --label "${NODEBALANCER_NAME}" --json | jq .\[\"${NODEBALANCER_NAME}\"\]\[\"80\"\]\[\"nodes\"\]\[\]\|select\(.name==\"$NODE_NAME\"\)\|select\(.status==\"$status_value\"\) )
            if [ -n "$status" ]; then
                echo "$status_value"; break;
            fi
            sleep 10
        done
    done
}

function update_node_status {
    node_status=$1
    shift
    for NODE_NAME in $@; do
        # Put the node back into rotation
        echo "Updating NodeBalancer for $NODE_NAME to $node_status..."
        linode nodebalancer \
            $LINODE_USER_ARG \
            --action node-update \
            --label "$NODEBALANCER_NAME" \
            --port 80 \
            --name "$NODE_NAME" \
            --mode "$node_status" > /dev/null

        if [ "accept" == "$node_status" ]; then
            slackpost "#operations" ":white_check_mark: $NODE_NAME rebuilt and live"

            echo "Node $NODE_NAME rebuilt!"
        fi
    done
}

function rebuild_worker {
    for NODE_NAME in $@; do
        echo "Rebuilding $NODE_NAME..."
        slackpost "#operations" ":white_check_mark: $NODE_NAME rebuilding..."
        linode --action rebuild \
            $LINODE_USER_ARG \
            --label "$NODE_NAME" \
            --plan "linode1024" \
            --distribution "Ubuntu 16.04 LTS" \
            --pubkey-file $PUBLIC_KEY \
            --stackscript "MLTSHP Worker Node" \
            --stackscriptjson "{\"docker_image_name\": \"$WORKER_IMAGE_NAME\"}" \
            --password "$(dd bs=32 count=1 if="/dev/urandom" 2>/dev/null | base64 | tr +/ _.)" > /dev/null &
    done
}

function rebuild_web_node {
    update_node_status "reject" $@
    rebuild_web_node_step $@
    wait_for_status "DOWN" $@
    wait_for_status "UP" $@
    update_node_status "accept" $@
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

echo "This script will rebuild all active MLTSHP web nodes"
echo "using a Docker Cloud image."
echo
echo "GitHub master commit: $GITHUB_COMMIT_SHA"
echo "Web Docker image to deploy: $DOCKER_IMAGE_NAME"
echo -n "Web Nodes to rebuild: "
echo_with_delimiter ", " ${web_nodes[@]}
echo "Worker Docker image to deploy: $WORKER_IMAGE_NAME"
echo -n "Worker Node to rebuild: "
echo_with_delimiter ", " ${worker_nodes[@]}
echo
echo "Press Enter to continue or ^C to abort..."
read

slackpost "#operations" "MLTSHP deployment starting for Docker image $DOCKER_IMAGE_NAME (Git master is: $GITHUB_COMMIT_SHA)..."

# Rebuild the worker node(s) with latest docker image...
rebuild_worker ${worker_nodes[@]}

# Fully rebuild one web node, then we'll rebuild the rest
rebuild_web_node ${web_nodes[0]}

# Now rebuild remaining web nodes, in parallel
rebuild_web_node ${web_nodes[@]:1}

slackpost "#operations" "Docker image $DOCKER_IMAGE_NAME deployed to production (Git master is: $GITHUB_COMMIT_SHA)."

echo "All nodes rebuilt!"
