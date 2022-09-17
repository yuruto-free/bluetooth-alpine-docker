# bluetooth speaker environment using alpine image in docker

## Preparation
### Required
* Should execute docker by root user because this container uses `/run/dbus/system_bus_socket`.
* Support 64 bit architecture only

### Build
Run the following command:

```sh
# optional: delete old image
docker images | grep none | awk '{print $3;}' | xargs -I{} docker rmi {}
# build
docker-compose build
```

### Check bluetooth connection
First, execute the following command in host environment.

```sh
# ===================
# In host environment
# ===================
docker-compose run --rm bluetooth-environment bash
```

Next, execute the following commands in docker container.

```sh
# ===================
# In docker container
# ===================
# Step1: execute this command
bluetoothctl
# Step2: agent on
[bluetooth]  agent on
# Step3: scan device (in real world, turn on bluetooth speaker)
[bluetooth]  scan on
# show mac addresses of several devices
# -> search own bluetooth device
# Step4: connect your bluetooth device
[bluetooth]  scan off
[bluetooth]  connect your-bluetooth-speaker-mac-address
# Step5: pair your bluetooth device
[bluetooth]  pair your-bluetooth-speaker-mac-address
# Step6: trust your bluetooth device
[bluetooth]  trust your-bluetooth-speaker-mac-address
# Step7: quit bluetoothctl
[bluetooth]  quit
# Step8: exit this container
exit
```

### Setup .env file
Create a `.env` file in host environment. A sample file is following below:

```sh
BLUETOOTH_SPEAKER=your-bluetooth-speaker-mac-addresses
BLUEALSA_PROFILE=a2dp   # a2dp or sco: depends on your environment
MAX_VOLUME=70%
```

## Start Container
Run the following command.

```sh
docker-compose up -d
```

## Usage
### GET Request
* In the host environment, when you execute the following command, you can get wav file list.

    ```sh
    curl -X GET -H "Content-Type: application/json; charset=utf-8" -d '{"command":"list"}' http://localhost:10650
    ```

* In the host environment, when you execute the following command, you can stop the playing music.

    ```sh
    curl -X GET -H "Content-Type: application/json; charset=utf-8" -d '{"command":"stop"}' http://localhost:10650
    ```

### POST Request
In the host environment, when you execute the following command, you can play the specified music.

    ```sh
    curl -X POST -H "Content-Type: application/json; charset=utf-8" -d '{"filename":"target-wav-filename.wav"}' http://localhost:10650
    # Required: exist file in `audiofiles` directory.
    ```
## Troubleshooting
* `bluealsa` does not work
    * In your host environment, create the following file in `/etc/dbus-1/system.d/bluealsa.conf`

        ```sh
        <!-- This configuration file specifies the required security policies
             for BlueALSA core daemon to work. -->

        <!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
         "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
        <busconfig>

          <!-- ../system.conf have denied everything, so we just punch some holes -->

          <policy user="root">
            <allow own_prefix="org.bluealsa"/>
            <allow send_destination="org.bluealsa"/>
          </policy>

          <policy group="audio">
            <allow send_destination="org.bluealsa"/>
          </policy>

        </busconfig>
        ```

## Test environment
```sh
# lsb_release -a
Distributor ID: Debian
Description:    Debian GNU/Linux 11 (bullseye)
Release:        11
Codename:       bullseye

# arch
aarch64
```
