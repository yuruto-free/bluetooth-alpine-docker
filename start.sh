#!/bin/bash

function handler(){
    kill ${pid_bluealsa}
    kill ${pid_aplay}
    kill ${pid_server}
    wait ${pid_bluealsa}
    wait ${pid_aplay}
    wait ${pid_server}
}


# ============
# main routine
# ============
# setup handler
trap handler SIGTERM

# create asoundrc.conf file
cat <<- _EOF_ > /etc/asound.conf
defaults.bluealsa.device "${BLUETOOTH_SPEAKER}"
defaults.bluealsa.profile "${BLUEALSA_PROFILE}"
defaults.bluealsa.delay 10000

pcm.!default {
    type plug
    slave.pcm {
        type bluealsa
        device "${BLUETOOTH_SPEAKER}"
        profile "${BLUEALSA_PROFILE}"
    }
}
_EOF_

# run pulseaudio
pulseaudio -D --exit-idle-time=-1 -v --log-target=stderr --log-level=4
# run bluealsa
bluealsa -p a2dp-sink -p a2dp-source -p hsp-ag &
pid_bluealsa="$!"
sleep 2
# run bluealsa-aplay
bluealsa-aplay ${BLUETOOTH_SPEAKER} &
pid_aplay="$!"
sleep 2
bluetoothctl connect ${BLUETOOTH_SPEAKER}
# setup volume
amixer -D bluealsa | grep Simple | grep -oP "'(?<=').*(?=')'" | xargs -I{} amixer -D bluealsa sset {} ${MAX_VOLUME}
# run server
python -u ${APP_ROOT_PATH}/server.py &
pid_server="$!"

wait ${pid_bluealsa}
wait ${pid_aplay}
wait ${pid_server}
