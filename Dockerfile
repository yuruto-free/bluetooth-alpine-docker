FROM alpine:3.11

ENV PYTHONUNBUFFERED=1 \
    APP_ROOT_PATH=/code \
    AUDIO_ROOT_PATH=/audiofiles

RUN    apk update \
    && apk add --no-cache bash tzdata python3 \
    && apk add --no-cache pulseaudio pulseaudio-utils alsa-utils alsa-lib-dev udev \
                          bluez dbus dbus-dev pulseaudio-bluez libpulse openrc \
    && apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing bluez-alsa \
    && cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime \
    && ln -sf python3 /usr/bin/python \
    && python3 -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip \
    && pip3 install --no-cache --upgrade pip setuptools wheel \
    && apk add --no-cache --virtual .build-deps \
               gcc musl-dev libffi-dev g++ libgcc libstdc++ libxslt-dev python3-dev \
               libc-dev linux-headers openssl-dev \
    && pip3 install simpleaudio \
    && ln -sf pip3 /usr/bin/pip \
    && apk --purge del .build-deps \
    && mkdir -p ${AUDIO_ROOT_PATH} \
    && mkdir -p ${APP_ROOT_PATH} \
    && mkdir -p /etc/dbus-1/system.d \
    && rm -rf /root/.cache /var/cache/apk/*

COPY start.sh /start.sh
RUN  chmod +x /start.sh

WORKDIR ${APP_ROOT_PATH}

CMD ["/start.sh"]
