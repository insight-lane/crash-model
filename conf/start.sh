#!/bin/bash

# -e: exit immediately if a command exits with a non-zerio status
set -e
echo "starting supervisor in foreground"
supervisord -c /etc/supervisord.conf -n

# don't put anything else in this file, it won't run!
