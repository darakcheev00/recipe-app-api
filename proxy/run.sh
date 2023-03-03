#!/bin/sh

set -e

# environment substitute
# insert conf.tpl, and output the latter
# to replace env var ${} with actual variable
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

# run nginx in the foreground
nginx -g 'daemon off;'