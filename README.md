# bluetooth speaker environment using alpine image in docker

## Preparation
### Build
Run the following command:

```sh
docker-compose build
```

### Check bluetooth connection
Enter the bluetooth-environment container, then execute `bluetoothctl` command, i.e. type this command in host environment, then execute the following commands in docker container.

```sh
# In host environment
docker-compose run --rm bluetooth-environment bash

# In docker container
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
BLUEALSA_PROFILE=a2dp   # a2dp or sco: depend on your environment
MAX_VOLUME=70%
```

## Start Container
Run the following command.

```sh
docker-compose up -d
```
