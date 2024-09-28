# Telegram bot

## Table of Contents
- [Overview](#overview)
- [Features](#communication-protocol)
- [Installation](#installation)
- [Usage](#main-functions)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
Telegram Bot is a service that connects the proposed infrastructure to the cloud-based instant messaging platform Telegram. It makes use of the REST Web Services offered by the Raspberry Pi connector to retrieve measurements from the devices of the platform. Additionally, again exploiting REST, it enables users to retrieve historical and real-time data from the Thingspeak platform and the Thingspeak adaptor, respectively. Moreover, it works both as an MQTT publisher and an MQTT subscriber to let the user send actuation commands and retrieve alerts.
You will find it at t.me/GeniusGymBot.

## Communication Protocol
- **MQTT**: Subscribes some topics like warning(crowdy and overtemp) and publish with topic for instruction.
- **REST**: : HTTP with JSON to get info about occupancy, availability and forecast. 

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `cherrypy` library
- `requests` library
- `telepot` library
- `threading` library


## Main functions:
> **initial functions**:
- /knowus - GymGenius for IoT program
+ /login - client or administrator
* /suggestion - Everyone can give any suggestions

> **roles**:
- Client: Suggestions, Occupancy, Availability, Forecast
+ Admin: Env data, Suggestions checking, Operation:AC, entrance, machines...

> **functions**:
1. Environment data in ThingSpeak
2. Occupancy situation
3. Available machine: choose a machine to check available number
4. Predict the future using: Choose day or timeslot way to see the forecast
5. Suggest us for a better performance and admin can check it
6. Operate AC,Entrance,Machines by administrator
7. Service registration

## Shutdown and Cleanup
When the service is stopped, the signal handler will ensure that the MQTT client disconnects cleanly and the service is properly stopped.
enter 'q' to stop script

