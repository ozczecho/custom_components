from nuheat import NuHeat

# Initalize an API session with your login credentials
api = NuHeat("AU", "email", "pwd")
api.authenticate()

thermostat = api.get_thermostat("device_id")

current = thermostat.celsius
target = thermostat.target_celsius

heating = thermostat.heating
online = thermostat.online
serial = thermostat.serial_number
