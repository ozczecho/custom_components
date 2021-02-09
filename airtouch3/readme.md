# AirTouch 3 Integration (Last update: 6th Feb 2021)

A Home Assistant custom climate component that lets you control your AirTouch 3 console locally. It has a dependancy on the [vzduch-dotek](https://github.com/ozczecho/vzduch-dotek) api.

## Install

I assume you have `vzduch-dotek` up and running. Please refer to that projects documentation on steps to install.

* Copy the `airtouch3` directory into your `custom_components` folder.
* This integration uses config flow only, so add the integration using the Home Assistant UI. No need to add anything to your `configuration.yaml`
* In config flow please enter in the host and port number. The host and port are for the `vzduch-dotek` api and not the actual AirTouch 3 console.
* Click OK.
* You should now see:
  * A Climate component
  * A switch for each of your zones
  * A sensor if you have those `airtouch3` temperature sensors.
  
## Thermostat Mode

A little note about the thermostat mode. AirTouch 3 supports the following modes:
 * AC = 0
 * Average = Zones + 1
 * Auto = Zones + 2
 * Zone = Zones - 1
 
So if `thermostatMode` is set to `0` the temperature is read from AC. If you have 4 zones and `thermostatMode` is set to `3` the temperature is read from one zone. This is important for how the climate component sets and controls the desired temperature. At the moment the logic is:

 * For `Zone` mode set the desired temperature for the zone
 * For any other mode set the desired temperature at the AC. 

## Setting a Zones desired temperature

If your `thermostatMode` is not Zone, you can still set a zones desired temperature - using a service call. In your Home Assistant instance, go to `developer-tools/service` and find `airtouch3.set_zone_temperature` service. There you enter in the `entity_id` for the zone you want to control as well as the desired temperature.
```
  airtouch3.set_zone_temperature
    entity_id: switch.zone_bedroom
    temperature: 25
```

## Limitations

* The climate component tested against Home Assistant version `2021.1.5`.
* Only a subset of `AirTouch 3` Api have been implemented via `vzduch-dotek`. The imlemented Api include:
    * Get current state of aircon
    * Switch aircon on / off
    * Set aircon mode
    * Set aircon fanmode
    * Set desired temperature
    * Toggle zone on / off
    * Switch zone on / off
    * Set zones desired temperature
  
## Warning
  
A certain level of technical experience is required to get this up and running successfully. Namely:
* Basic knowledge of Networking 
* Containerization
* Troubleshooting
  
## Lovelace

Here is what my setup looks like\
![AirTouch3 in Lovelave](https://github.com/ozczecho/custom_components/blob/master/airtouch3/at3.PNG?raw=true)
