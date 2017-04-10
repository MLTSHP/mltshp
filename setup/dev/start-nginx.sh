#!/bin/sh
echo resolver $(awk 'BEGIN{ORS=" "} $1=="nameserver" {print $2}' /etc/resolv.conf) ";" > /etc/nginx/resolvers.conf
exec /usr/sbin/nginx -g 'daemon off;'