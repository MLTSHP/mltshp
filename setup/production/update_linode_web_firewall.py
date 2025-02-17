#!/usr/bin/env python3

# This script makes dynamic updates to our Linode web firewall, allowing access
# from the published Fastly IP address list. It should be run as a cron job, updating
# on a regular basis. It only applies updates when changes are detected, comparing
# against the existing rules. Linode issues email notifications when the firewall rules
# change, so we shouldn't blindly make updates, but only when changes are required.

import os, requests

# Retrieve settings from the environment
linode_api_token = os.environ.get("LINODE_API_TOKEN")
if not linode_api_token:
    print("LINODE_API_TOKEN not set")
    exit(1)

linode_firewall_label = "mltshp-web-us-ord"
linode_inbound_rule_label = "Fastly"

all_firewalls = requests.get(
    "https://api.linode.com/v4/networking/firewalls",
    headers={
        "accept": "application/json",
        "authorization": f"Bearer { linode_api_token }",
    }).json()

web_firewall = next(iter([fw
    for fw in all_firewalls["data"]
    if fw["label"] == linode_firewall_label]), None)
if not web_firewall:
    print(f"No Linode firewall found with label '{ linode_firewall_label }'")
    exit(1)

# Look for an existing Fastly rule and gather the IP addresses for comparison
# with what is currently provided by Fastly.
fastly_inbound = next(iter([data
    for data in web_firewall["rules"]["inbound"]
    if data["label"] == linode_inbound_rule_label]), None)
other_inbound = [data
    for data in web_firewall["rules"]["inbound"]
    if data["label"] != linode_inbound_rule_label]
if fastly_inbound:
    existing_ipv4s = set(fastly_inbound["addresses"]["ipv4"])
    existing_ipv6s = set(fastly_inbound["addresses"]["ipv6"])
else:
    existing_ipv4s = set()
    existing_ipv6s = set()

fastly_ips = requests.get(
    "https://api.fastly.com/public-ip-list",
    headers={
        "accept": "application/json",
    }).json()
fastly_ipv4s = set(fastly_ips.get("addresses"))
fastly_ipv6s = set(fastly_ips.get("ipv6_addresses"))

# If no IP addresses have changed, we're done.
if existing_ipv4s == fastly_ipv4s and existing_ipv6s == fastly_ipv6s:
    print("Fastly IPs have not changed")
    exit(0)

print("Updating firewall with new Fastly IPs")

response = requests.put(
    f"https://api.linode.com/v4/networking/firewalls/{ web_firewall["id"] }/rules",
    json={
        "inbound": [
            {
                "label": "Fastly",
                "description": "DO NOT EDIT - Updated programmatically",
                "addresses": {
                    "ipv4": fastly_ips.get("addresses"),
                    "ipv6": fastly_ips.get("ipv6_addresses"),
                },
                "action": "ACCEPT",
                "ports": "80",
                "protocol": "TCP",
            },
        ] + other_inbound,
        "inbound_policy": "DROP",
        "outbound_policy": "ACCEPT",
    },
    headers={
        "accept": "application/json",
        "authorization": f"Bearer { linode_api_token }",
        "content-type": "application/json",
    }
)

if response.status_code == 200:
    print("Firewall updated successfully")
else:
    print(f"Failed to update firewall (status { response.status_code }): { response.text }")
    exit(1)
