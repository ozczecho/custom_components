# OJ Electronics / Warmup

Home assistant integration for the `WarmTech` floor heating thermostat. I believe they were sold in Australia / New Zealand. This integration is tightly coupled to the following model numbers:

* `W3ADG4`
* `W3AWG4`

This integration is basically a copy of the [python-nuheat api](https://github.com/broox/python-nuheat) and the official Home Assistant [nuheat integration](https://www.home-assistant.io/integrations/nuheat/). A massive thank you to the developers of both projects. The reason for copying the project and not simply forking and maybe adding a `pr` is that the thermostat I have is "crippled" for the Australian market. Some differences

* Uses `mythermostat.info` as the api end point. This is not the deal breaker as the [python-nuheat api](https://github.com/broox/python-nuheat) supports different brands, so its not too hard to add an additional brand.
* Subbtle differences how you can set the temperature for `PRESET_HOLD`.

This integration is customized for my use case, so I would definetely recommend to use the official library. But if you have the above thermostats maybe this integration can help. Your mileage may vary. Good Luck.

## Using

* This is designed to "override" the offical integration.
* Copy the `nuheat` directory into your `custom_components` folder.
* Restart Home Assistant.
* Goto `Settings->Devices & Services` and search for `nuheat`
* Should see `Brand` as an option on the setup screen.
* Enter the `username`, `password`, `serialnumber` and `brand`. The brand should be `OJ`
* Hit Enter and if all goes well a new `climate` entity is setup.
