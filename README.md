# PyZone API
This project enables you to control any Daikin Skyzone reverse cycle ducted split unit without being restricted by the somewhat limited functionality provided by Daikin via their APP.
I've attempted to provide as much flexibility as possible for interfacing to the API.
The API works by creating a virtual Daikin structure with all the current settings of the AC unit. Changes are made via API calls to the structure variables which are then transmitted to the Daikin Unit via a encoded string. A call is then made back to the Daikin Unit to confirm the updated settings.

I've created a Home Assistant Component which uses this API and integrates it nicely into that. Please check it out if you want to use the API on it's own to see what it can do.

If required I can link a quick GUI for the API to control the AC from any system which can run a python shell (i.e. Windows, MacOS, etc.).

## Supported Features

 - Set/Get heating/cooling temperature
 - Set/Get AC mode (heat/cool/fan/dry/off)
 - Set/Get AC FAN setting (Auto/Low/Med/Hi/Auto-Low/Auto-Med/Auto-High)
 - Get current temperatures from internal, outdoor and refrigerant sensors.
 - Support for external sensors connected to Daikin Unit including names. (Current temp for external sensors will only be shown if an external sensor is set as the 'selected sensor').
 - Set/View current zones (As setup by the Daikin Tablet).
 - Set/View current selected sensor (Reference temperature used by Daikin to start/stop climate control)
 - View setup info from Daikin AC (Number of Zones/Sensors, Internal/External Part Numbers, Current and History Error codes and clean filter warning flag).

## Supported Units

Support Skyzone controllers: BRC230TZ4, BRC230TZ8, BRC24TZ4 and BRC24TZ8

Support Daikin Models: Any FDYQ & FDYQN unit fitted with a Skyzone controller (Single or 3 phase).

In theory, this API should support **ANY** Daikin Skyzone unit.

### How to use
Create an instance of the API using;

    daikinSkyZoneAPI = DaikinSkyZone()

Tell the API to discover Skyzone;

    daikinSkyZoneAPI.discover_skyzone_controller()

To determine if the API found anything, you can simply check;

    if(daikinSkyZone.is_unit_connected()):
	    return True #Found Daikin Skyzone
	else:
		return False #Troubles

You could also check;

    if(daikinSkyZone._IpAdd != '0.0.0.0')

#### Great, so what next?
Here is a quick rundown on the interfaces to the API.
If you plan on using the API, hit up the source. Hopefully comments in there are abit more useful ;p

|API Function | Parameters/Return and Purpose
|-------|--------|
|discover_skyzone_controller()|Tells the API to search for any Skyzone unit on the current network
|update()| Gets the current selected sensor temp, outdoor temp, AC Mode, Fan Mode and zone settings.
|update_temperate_sensor() | Uses a hidden service mode to get the Internal temperature (if not selected current sensor) and the refrigerant sensor. The refrigerant value is handy to work out if the unit is currently active, doing a coolant cycle, de-ice, etc.
|update_additional_temperature_sensors() | This function has two stage. The first stage will update the internal and refrigerant sensors whene called. The second stage will cycle through all external sensors to attempt to provide an up-to date temperature. This only occurs when pollExterbalSensorFlag is enabled. The function works, however even though the sensor is selected for a brief time (~8s), the Daikin AC unit will 'keep' the value for ~3mins before releasing it. This means if you have warm and cool zone, the unit will constantly start/stop whenever the logic is run. **It's not recommended to be used unless you 'alter' the target temperature to keep the unit functional across all zones.**
|sync_climate_request()| Used to transmit a change of data back to the Daikin Unit. Used for: Mode, Fan Speed, Target Temperature and Zone.
|update_temperate_sensor()| Used to transmit a change of selected sensor back to the Daikin Unit.
|is_unit_connected()| Indicates if valid data was received from the Daikin Unit to initialisation.
|get_indoor_unit_part_number() | Returns the indoor unit part number
|get_outdoor_unit_part_number() | Returns the outdoor unit part number
|get_current_mode() | Returns the current mode of the Daikin Unit in text. Setup for Home Assistant Climate integration.
|set_current_mode() | Set the current mode of the Daikin Unit. *Parameter: **class AcStateMode***
|get_target_temp()| Get the target temperature for the current selected mode. NOTE: Heating/Cooling modes each have their own.
|set_target_temp()| Set the target temperature for the current mode. *Parameter*: ***interger***
|get_current_temp()| Get the current temperature for the selected sensor (Internal or External 1 or 2).
|get_selected_temp_sensor() | Get the sensor which is currently set as the selected sensor. *Return Type: **class SensorIndex***
|set_selected_temp_sensor() | Set the sensor which is to be set as the selected sensor. (Sensor used for reference temperature for climate control). *Parameter: **integer 0-2 (index of class SensorIndex)***
|get_number_of_external_sensors()| Gets the number of external sensors configured to the Daikin Unit. Max of 2 supported.
|get_sensor_state() | Gets the name of the Sensor as setup in the Daikin Skyzone Tablet. **Parameter:* **integer 0-2 (index of class SensorIndex)***
|get_sensor_state() | Returns True if the given index corresponds to the sensor set as the selected sensor. Otherwise returns false. Implemented for Home Assistant. **Parameter* **integer 0-2 (index of class SensorIndex)***
|get_sensor_temperature()| Returns the temperature of the sensor for the given index. *Parameter: **integer 0-4 (index of class SensorIndex)***
|get_number_of_zones() | Returns the number of Zones as setup in the Daikin Skyzone Tablet. 
|get_zone_name()| Returns the Zone Name as setup in the Daikin Skyzone Tablet. *Parameter: **integer zone Index (0-> Number of zones - 1)***
|get_zone_state() | Gets if the given Zone (zone Index ) is currently active. *Parameter: **integer zone Index (0-> Number of zones - 1)***
|set_zone_active() | Set the given Zone as active. *Parameter: **integer zone Index (0-> Number of zones - 1)***
|set_zone_inactive() | Set the given Zone as inactive. *Parameter: **integer zone Index (0-> Number of zones - 1)***
|get_fan_speed() | Gets the current fan speed of the Daikin Unit in text. Setup for Home Assistant Climate integration.
|set_fan_speed() | Sets the fan speed of the Daikin Unit. *Parameter: **class FanSpeed*** 
|get_min_supported_temp()| Gets the minimum temperature supported by the Daikin Unit for cooling.
|get_max_supported_temp()| Gets the maximm temperature supported by the Daikin Unit for heating.
|get_error_codes()| Get the current error codes being reported by the Daikin Unit.
|get_history_error_codes()| Get the history error codes being reported by the Daikin Unit
|get_clear_filter_flag()| Get the status of clear filter flag from the Daikin Unit.



### Advanced Usage
For the init for the API, there are a few parameters that can be set in order to get abit more from the interface.

    DaikinSkyZone(password, name, ipAddress, debugLevel, pollExterbalSensorFlag)

**password** - Set the 4 digit Adapter password set in the Daikin Tablet.
    
**name** - Gives the name used for display purposes for Home Assistant.

**ipAddress** - Bypass discovery and give an the API an IP Address to attempt communication to. 

**debugLevel** - Enable developer debug code and control how much 'spam' is given to a _Logger instance. It's useful for developer debugging or if you want to see how much data flows around.
	*0 - Disabled
	1 - Basic Info. Received frames and data.
	2 - More Info. Strings for names
	3 - See raw frame data received.*
    
**pollExternalSensorsFlag** - Enable logic to poll ALL connected sensors. VERY EXPERIMENTAL

