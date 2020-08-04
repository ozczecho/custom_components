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
  
  ## Lovelace
  
  Here is what my setup looks like\
  ![AirTouch3 in Lovelave](https://github.com/ozczecho/custom_components/blob/master/airtouch3/at3.PNG?raw=true)
