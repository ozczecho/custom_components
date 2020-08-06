# AirTouch 3 Integration

A Home Assistant custom climate component that lets you control and view data from your AirTouch 3 console locally. It depends on the [vzduch-dotek](https://github.com/ozczecho/vzduch-dotek) api being installed.

## Install

I assume you have `vzduch-dotek` up and running. Please refer to that projects documentation on steps to install.

* Copy the `airtouch3` directory into your `custom_components` folder.
* This integration uses config flow only, so add the integration using the Home Assistant UI.
* Please note there is a known bug that the config popup for `airtouch3` does not have any labels. The top row is for the host, the bottom row is for the port. The host and port are for the `vzduch-dotek` api and not the actual AirTouch 3 console.
* Click OK.
* You should now see:
  * A Climate component
  * A switch for each of your zones
  * A sensor if you have those `airtouch3` temperature sensors.

## Limitations

* The climate component currently works for HA version `0.108` and earlier. Thats because of a renaming exercise in HA post the `0.108` release between `ClimateEntity` and `ClimateDevice`. This will be fixed as soon as I update my system to latest HA version.
* Only a subset of `AirTouch 3` Api have been implemented via `vzduch-dotek`. The imlemented Api include:
    * Get current state of aircon
    * Switch aircon on / off
    * Set aircon mode
    * Set aircon fanmode
    * Set desired temperature
    * Toggle zone on / off
    * Switch zone on / off
  
## Warning
  
A certain level of technical experience is required to get this up and running successfully. Namely:
* Basic knowledge of Networking 
* Containerization
* Troubleshooting
  
## Lovelace

Here is what my setup looks like\
![AirTouch3 in Lovelave](https://github.com/ozczecho/custom_components/blob/master/airtouch3/at3.PNG?raw=true)
