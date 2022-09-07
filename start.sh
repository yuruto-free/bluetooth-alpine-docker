#!/bin/bash

function handler(){
    kill ${pid}
    wait ${pid}
}

trap handler SIGTERM

# ============
# main routine
# ============
mkdir -p /run/openrc
touch /run/openrc/softlevel
rc-status
sleep 2
rc-service bluetooth start
pulseaudio -D --exit-idle-time=-1 -v --log-target=stderr --log-level=4
/usr/bin/python -u ${APP_ROOT_PATH}/server.py &
pid="$!"

wait ${pid}
