import re
import socket
import http.client
import time
import logging

from daikinPyZone.daikinCalculate import *

from daikinPyZone.daikinClasses import (
    determine_fan_information,
    InternalAcMode,
    AcStateMode,
    SensorSelect,
    SensorIndex,
    AcPowerState,
    convert_mode_flags_to_ac_state,
    FanSpeed,
    FanMode,
    sync_zone_state,
    get_zone_bit_mask_from_zone_state,
    ZoneState,
    UpdateRequest)

_LOGGER = logging.getLogger(__name__)


# process_basic_info
# Function processes the 'BasicInfo' from received from the SkyZone unit.
# C_PCD_BasicInfo =0xA0
def process_basic_info(self, incoming_info):
    # not needed:
    # onTimer = (incoming_info[6] >> 4);
    # offTimer = (incoming_info[6] & 0xF);
    # onTimerCount = (incoming_info[7] >> 4);
    # offTimerCount = (incoming_info[7] & 0xF);
    # mNowHour = ((incoming_info[23]) >> 4) * 10 + (incoming_info[23] & 0xF);
    # mNowMin = ((incoming_info[24]) >> 4) * 10 + (incoming_info[24] & 0xF);
    # airFlowVersion = (incoming_info[0] >> 1 & 0xF); Keeps track of last airflow change. Cant see it being required.
    # zikoku  = incoming_info[0]  & 0x20; AcUnit request sets time when !=0
    # acModeAuto = ((incoming_info[1]  >> 6) & 1) When unit is set to 'auto'. HA will control setting, not not required.
    # multiZoningCoefficient = ((incoming_info[2]) >> 3 & 0x1F) #Cant see use-case, maybe for advanced blending?
    # AirFlowRatio = incoming_info[5]
    # CommonZone = (incoming_info[8]  >> 7)

    # If UpdateRequest mask is set, ignore current response.
    
    if self._DaikinClimateSettings_Object.UpdateRequestMask:
        if self._DebugModeLevel >= 1:
            _LOGGER.debug('Skipping update message due to changed local variables')
        pass
    else:
        self._DaikinClimateSettings_Object.PowerOnState = AcPowerState(incoming_info[1] >> 7)
        self._DaikinClimateSettings_Object.SelectedSensor = SensorIndex(incoming_info[11] >> 4)
        self._DaikinClimateSettings_Object.CoolSetTemp = incoming_info[18]
        self._DaikinClimateSettings_Object.HeatSetTemp = incoming_info[20]

        self._DaikinClimateSettings_Object.TempSensorValues[self._DaikinClimateSettings_Object.SelectedSensor] = (
                    incoming_info[14] & 0x7F)
        self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Outdoor] = (incoming_info[16] & 0x7F)

        self._DaikinClimateSettings_Object.AcStateModeValue = convert_mode_flags_to_ac_state(incoming_info[1] & 0x7)
        self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode(incoming_info[2] & 0x7)

        cool_fan_mode = (incoming_info[3] >> 4 & 0x3)
        cool_fan_speed = (incoming_info[3] & 0xF)
        heat_fan_mode = (incoming_info[4] >> 4 & 0x3)
        heat_fan_speed = (incoming_info[4] & 0xF)
        cool_fan_state = determine_fan_information(cool_fan_mode, cool_fan_speed)
        heat_fan_state = determine_fan_information(heat_fan_mode, heat_fan_speed)

        self._DaikinClimateSettings_Object.CoolFanState.FanMode = cool_fan_state.FanMode
        self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = cool_fan_state.FanSpeed
        self._DaikinClimateSettings_Object.HeatFanState.FanMode = heat_fan_state.FanMode
        self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = heat_fan_state.FanSpeed

        self._DaikinClimateInfo_Object.NumberOfZones = (incoming_info[8] & 0xF)
        self._DaikinClimateInfo_Object.NumberOfSensors = (incoming_info[10] & 0xF)
        self._DaikinClimateInfo_Object.ErrorCodes = (incoming_info[12])
        self._DaikinClimateInfo_Object.HistoryErrorCodes = (incoming_info[13])
        self._DaikinClimateInfo_Object.ClearFilter = (incoming_info[0] & 1)

        sync_zone_state(self, incoming_info[9])

    if self._DebugModeLevel >= 1:
        _LOGGER.debug('-------------------------------------------------------------------------------')
        _LOGGER.debug('Power State: %s | Clean Filter: %s',
                      self._DaikinClimateSettings_Object.PowerOnState,
                      self._DaikinClimateInfo_Object.ClearFilter)
        _LOGGER.debug('Sensor Temp: %s | Outdoor Temp: %s',
                      self._DaikinClimateSettings_Object.TempSensorValues[
                          self._DaikinClimateSettings_Object.SelectedSensor],
                      self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Outdoor])
        _LOGGER.debug('AcMode: %s | Internal Ac Mode: %s',
                      self._DaikinClimateSettings_Object.AcStateModeValue,
                      self._DaikinClimateSettings_Object.InternalAcMode)
        _LOGGER.debug('Cool Set Temp: %s | Heat Set Temp: %s',
                      self._DaikinClimateSettings_Object.CoolSetTemp,
                      self._DaikinClimateSettings_Object.HeatSetTemp)
        _LOGGER.debug('CoolFanMode: %s | CoolFanSpeed: %s',
                      self._DaikinClimateSettings_Object.CoolFanState.FanMode,
                      self._DaikinClimateSettings_Object.CoolFanState.FanSpeed)
        _LOGGER.debug('HeatFanMode: %s | HeatFanSpeed: %s',
                      self._DaikinClimateSettings_Object.HeatFanState.FanMode,
                      self._DaikinClimateSettings_Object.HeatFanState.FanSpeed)
        _LOGGER.debug('Number Of Zones: %s | Selected Zones: %s',
                      self._DaikinClimateInfo_Object.NumberOfZones,
                      get_zone_bit_mask_from_zone_state(self))
        _LOGGER.debug('Number Of Sensors: %s | Selected Sensor: %s',
                      self._DaikinClimateInfo_Object.NumberOfSensors,
                      self._DaikinClimateSettings_Object.SelectedSensor)
        _LOGGER.debug('ErrorCode: %s | HistoryErrorCode: %s',
                      self._DaikinClimateInfo_Object.ErrorCodes,
                      self._DaikinClimateInfo_Object.HistoryErrorCodes)


# process_initial_info
# Function processes the 'InitialInfo' from received from the SkyZone unit.
# C_PCD_InitialInfo = 0xA1                # Get unit type and limits
def process_initial_info(self, incoming_info):
    # Convert byteArray to string of characters
    incoming_string = ''.join(chr(x) for x in incoming_info[0:32])

    if self._DebugModeLevel >= 2:
        _LOGGER.debug('Indoor/Outdoor Unit: %s', incoming_string)

    self._DaikinClimateInfo_Object.IndoorUnitPartNumber = str(incoming_string[1:12]).rstrip('\x00 ')
    self._DaikinClimateInfo_Object.OutdoorUnitPartNumber = str(incoming_string[16:30]).rstrip('\x00 ')
    self._DaikinClimateInfo_Object.MaxCoolTemp = incoming_info[31]
    self._DaikinClimateInfo_Object.MinCoolTemp = incoming_info[32]
    self._DaikinClimateInfo_Object.MaxHeatTemp = incoming_info[33]
    self._DaikinClimateInfo_Object.MinHeatTemp = incoming_info[34]

    if self._DebugModeLevel >= 1:
        _LOGGER.debug('Indoor Unit#: %s | Outdoor Unit #: %s', self._DaikinClimateInfo_Object.IndoorUnitPartNumber,
                      self._DaikinClimateInfo_Object.OutdoorUnitPartNumber)
        _LOGGER.debug('Max Cool Temp: %s | Min Cool Temp: %s', self._DaikinClimateInfo_Object.MaxCoolTemp,
                      self._DaikinClimateInfo_Object.MinCoolTemp)
        _LOGGER.debug('Max Heat Temp: %s | Min Heat Temp: %s', self._DaikinClimateInfo_Object.MaxHeatTemp,
                      self._DaikinClimateInfo_Object.MinHeatTemp)


# process_control_info
# Function processes the 'ControlInfo' from received from the SkyZone unit.
# This should only be a 'positive response' from SkyZone.
# C_PCD_ControlInfo = 0xB0
def process_control_info(self, _):
    pass
    # nothing to process
    if self._DebugModeLevel >= 1:
        _LOGGER.debug('0xB0 (ControlInfo Accepted)')


# process_internal_ac_mode
# Function processes the 'InternalAcMode' request from received from the SkyZone unit.
# This should only be a 'positive response' from SkyZone.
# C_PCD_InternalAcMode = 0xB2        # Control Normal/Service mode
def process_internal_ac_mode(self, _):
    pass
    # nothing to process
    if self._DebugModeLevel >= 1:
        _LOGGER.debug('0xB2 (InternalAcMode Accepted)')


# process_select_sensor
# Function processes the 'SelectSensor' request from received from the SkyZone unit.
# This should only be a 'positive response' from SkyZone.
# C_PCD_SelectSensor = 0xB3            # Set selected temp sensor
def process_select_sensor(self, _):
    pass
    # nothing to process
    if self._DebugModeLevel >= 1:
        _LOGGER.debug('0xB3 (SelectSensor Accepted)')


# process_get_local_setting
# Function processes the 'GetLocalSetting' request from received from the SkyZone unit.
# C_PCD_GetLocalSetting = 0xC0        # Get 'service' info
def process_get_local_setting(self, incoming_info):
    if self._DebugModeLevel >= 1:
        _LOGGER.debug('0xC0 (GetLocalSetting Accepted)')
    # if(self._DebugModeLevel >= 3):
    # for e in incoming_info : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )

    # Get temp sensor info mask
    if incoming_info[1] == 0x41:
        if incoming_info[2] == 2:
            self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Refrigerant] = incoming_info[4]
            if self._DebugModeLevel >= 1:
                _LOGGER.debug('Refrigerant Sensor: %s',
                              self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Refrigerant])
        elif incoming_info[2] == 0:
            self._DaikinClimateSettings_Object.TempSensorValues[
                self._DaikinClimateSettings_Object.SelectedSensor] = incoming_info[4]
            if self._DebugModeLevel >= 1:
                _LOGGER.debug('Set Sensor (%s,):  %s', self._DaikinClimateSettings_Object.SelectedSensor,
                              self._DaikinClimateSettings_Object.TempSensorValues[
                                  self._DaikinClimateSettings_Object.SelectedSensor])
        else:
            self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Internal] = incoming_info[4]
            if self._DebugModeLevel >= 1:
                _LOGGER.debug('Internal Sensor: %s',
                              self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Internal])


# process_set_local_setting
# Function processes the 'SetLocalSetting' request from received from the SkyZone unit.
# This should only be a 'positive response' from SkyZone.
# C_PCD_SetLocalSetting = 0xC3        # Set 'service' settings
def process_set_local_setting(self, _):
    pass
    # nothing to process
    if self._DebugModeLevel >= 1:
        _LOGGER.debug('0xC3 (SetLocalSetting Accepted)')


# process_get_zone_names
# Function processes the 'GetZoneNames' request from received from the SkyZone unit.
# C_PCD_GetZoneNames = 0xD0        # Get zone names
def process_get_zone_names(self, incoming_info):
    # Convert byteArray to string of characters
    incoming_string = ''.join(chr(x) for x in incoming_info)

    # delimit by ', '
    delimited_list = re.split(',', incoming_string)  # ,",")
    if self._DebugModeLevel >= 2:
        _LOGGER.debug(delimited_list)

    # Check delimited list for key items
    i = 0
    while i < len(delimited_list):
        # zone names
        if delimited_list[i].startswith('z' + str(i + 1)):
            self._DaikinClimateInfo_Object.ZoneName[i] = delimited_list[i][3:len(delimited_list[i])].rstrip('\x00')

        i = i + 1

    if self._DebugModeLevel >= 2:
        _LOGGER.debug('Zone Names: %s | %s | %s| %s| %s| %s| %s| %s',
                      self._DaikinClimateInfo_Object.ZoneName[0],
                      self._DaikinClimateInfo_Object.ZoneName[1],
                      self._DaikinClimateInfo_Object.ZoneName[2],
                      self._DaikinClimateInfo_Object.ZoneName[3],
                      self._DaikinClimateInfo_Object.ZoneName[4],
                      self._DaikinClimateInfo_Object.ZoneName[5],
                      self._DaikinClimateInfo_Object.ZoneName[6],
                      self._DaikinClimateInfo_Object.ZoneName[7])


# process_get_sensor_names
# Function processes the 'GetSensorNames' request from received from the SkyZone unit.
# C_PCD_GetSensorNames = 0xD2    # Get sensor names
def process_get_sensor_names(self, incoming_info):
    # Convert byteArray to string of characters
    incoming_string = ''.join(chr(x) for x in incoming_info)

    # delimit by ', '
    delimited_list = re.split(',', incoming_string)  # ,",")
    if self._DebugModeLevel >= 2:
        _LOGGER.debug(delimited_list)

    # Check delimited list for key items
    i = 0
    while i < len(delimited_list):
        if self._DebugModeLevel >= 2:
            _LOGGER.debug(delimited_list[i])
        # sensor names
        if delimited_list[i].startswith('s' + str(i + 1)):
            self._DaikinClimateInfo_Object.TempSensorName[i] =\
                delimited_list[i][3:len(delimited_list[i])].rstrip('\x00')

        i = i + 1

    if self._DebugModeLevel >= 2:
        _LOGGER.debug('Sensor Names: %s | %s | %s | %s', self._DaikinClimateInfo_Object.TempSensorName[0],
                      self._DaikinClimateInfo_Object.TempSensorName[1],
                      self._DaikinClimateInfo_Object.TempSensorName[2],
                      self._DaikinClimateInfo_Object.TempSensorName[3],
                      self._DaikinClimateInfo_Object.TempSensorName[4])


# C_DaikinIncomingResponse
# Defines the function pointer (function dictionary) making processing incoming frames really easy.
# Commented out items are not supported
C_DaikinIncomingResponse = {0xA0: process_basic_info,
                            0xA1: process_initial_info,
                            0xB0: process_control_info,
                            # 0xB1 : process_OnOffTimer,
                            0xB2: process_internal_ac_mode,
                            0xB3: process_select_sensor,
                            # 0xB4 : process_clear_filter,
                            # 0xB5 : process_clock,
                            # 0xB6 : process_set_7_days_counter,
                            # 0xBD : process_clear_error_code,
                            # 0xBE : process_set_air_flow,
                            0xC0: process_get_local_setting,
                            # 0xC1 : process_get_7_days_timer,
                            # 0xC2 : process_get_air_flow,
                            0xC3: process_set_local_setting,
                            0xD0: process_get_zone_names,
                            # 0xD1 : process_energy_saving,
                            0xD2: process_get_sensor_names
                            # 0xD3 : process_dealer_contact,
                            # 0xD5 : process_syu_info
                            }


# is_temp_within_heat_range
# Quick check if requested temp is within the range defined by the AC.
def is_temp_within_heat_range(self, temp):
    if (temp >= self._DaikinClimateInfo_Object.MinHeatTemp) and (temp <= self._DaikinClimateInfo_Object.MaxHeatTemp):
        return 1
    else:
        return 0


# is_temp_within_cool_range
# Quick check if requested temp is within the range defined by the AC.
def is_temp_within_cool_range(self, temp):
    if (temp >= self._DaikinClimateInfo_Object.MinCoolTemp) and (temp <= self._DaikinClimateInfo_Object.MaxCoolTemp):
        return 1
    else:
        return 0


# is_unit_data_present
# Check to see if serial number shave been received, i.e. handshake between PyZone and Skyzone is functional.
def is_unit_data_present(self):
    if (self._DaikinClimateInfo_Object.IndoorUnitPartNumber == 'Unknown') or (
            self._DaikinClimateInfo_Object.OutdoorUnitPartNumber == 'Unknown'):
        return False
    else:
        return True


# retrieve_power_state
# Function is used to return the current PowerOn State of PiZone - class ac_power_state
def retrieve_power_state(self):
    return self._DaikinClimateSettings_Object.PowerOnState


# update_power_state
# Function is used to alter the current PowerOn state of PiZone - class ac_power_state
# Note: Once updated, sync_control_info frame needs to be sent to SkyZone,
#   otherwise value will be lost next poll to SkyZone (BasicInfo).
def update_power_state(self, ac_power_state):
    if self._DaikinClimateSettings_Object.PowerOnState != ac_power_state:
        self._DaikinClimateSettings_Object.PowerOnState = ac_power_state
        # Set mask that update has occurred and to ignore current update if in progress
        self._DaikinClimateSettings_Object.UpdateRequestMask = \
            UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.POWER_STATE)


# get_climate_mode
# Function is used to return the current Climate mode of PiZone - class AcStateMode
def get_climate_mode(self):
    if retrieve_power_state(self) != AcPowerState.ON:
        return AcStateMode.MODE_OFF
    else:
        return self._DaikinClimateSettings_Object.AcStateModeValue


# set_climate_mode
# Function is used to alter the current Climate mode state of PiZone - class AcStateMode
# Note: Once updated, sync_control_info frame needs to be sent to SkyZone,
#   otherwise value will be lost next poll to SkyZone (BasicInfo).
def set_climate_mode(self, ac_mode):

    if ac_mode == AcStateMode.MODE_OFF:
        # Turn off unit
        if self._DebugModeLevel >= 1:
            _LOGGER.debug('TurnOff AC')
        update_power_state(self, AcPowerState.OFF)
        # leave AcStateModeValue as previous
    else:
        # turn on unit and set mode
        if self._DaikinClimateSettings_Object.AcStateModeValue != ac_mode or \
                self._DaikinClimateSettings_Object.PowerOnState != AcPowerState.ON:
            self._DaikinClimateSettings_Object.AcStateModeValue = ac_mode
            # Set mask that update has occurred and to ignore current update if in progress
            self._DaikinClimateSettings_Object.UpdateRequestMask = \
                UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.AC_STATE)
            update_power_state(self, AcPowerState.ON)


# get_target_climate_temp
# Function is used to return the current Target temperature for the current climate mode.
def get_target_climate_temp(self):
    # get current selected mode from AC and select corresponding set temp.
    # heat
    if get_climate_mode(self) == AcStateMode.MODE_HEAT:
        return self._DaikinClimateSettings_Object.HeatSetTemp
    # fan/off - report no temp
    elif (get_climate_mode(self) == AcStateMode.MODE_FAN) or (get_climate_mode(self) == AcStateMode.MODE_OFF):
        return None
    # cool
    else:
        return self._DaikinClimateSettings_Object.CoolSetTemp


# set_target_climate_temp
# Function is used to alter the current Target temperature for the current mode  of PiZone
# Note: Once updated, sync_control_info frame needs to be sent to SkyZone,
#   otherwise value will be lost next poll to SkyZone (BasicInfo).
def set_target_climate_temp(self, temp):
    # HEAT
    if get_climate_mode(self) == AcStateMode.MODE_HEAT:
        # check temp is with heating range.
        if is_temp_within_heat_range(self, temp):
            # update 'heat' variables
            if self._DaikinClimateSettings_Object.HeatSetTemp != temp:
                self._DaikinClimateSettings_Object.HeatSetTemp = temp
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.TARGET_TEMP)
    # COOL
    elif get_climate_mode(self) == AcStateMode.MODE_COOL:
        # check temp is within cooling range
        if is_temp_within_cool_range(self, temp):
            # update 'cool' variables
            if self._DaikinClimateSettings_Object.CoolSetTemp != temp:
                self._DaikinClimateSettings_Object.CoolSetTemp = temp
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.TARGET_TEMP)
    # AUTO
    elif get_climate_mode(self) == AcStateMode.MODE_AUTO:
        # check temp is within heat/cool range.
        if is_temp_within_cool_range(self, temp) and is_temp_within_heat_range(self, temp):
            # update both
            if self._DaikinClimateSettings_Object.HeatSetTemp != temp or \
                    self._DaikinClimateSettings_Object.CoolSetTemp != temp:
                self._DaikinClimateSettings_Object.HeatSetTemp = temp
                self._DaikinClimateSettings_Object.CoolSetTemp = temp
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.TARGET_TEMP)
    # DRY/FAN/OFF
    else:
        # Temp setting ignored.
        pass


# get_climate_temp_sensor
# Function is used to return the current Climate temp sensor of PiZone - class SensorIndex
def get_climate_temp_sensor(self):
    return self._DaikinClimateSettings_Object.SelectedSensor


# get_climate_sensor_name
# Function is used to get sensor name as given by Daikin Skyzone
def get_climate_sensor_name(self, sensor_index):
    if isinstance(sensor_index, SensorIndex):
        return self._DaikinClimateInfo_Object.TempSensorName[sensor_index]


# get_climate_sensor_state
# Function is used to indicate if a given SensorIndex is currently set as the selected_sensor
def get_climate_sensor_state(self, sensor_index):
    if isinstance(sensor_index, SensorIndex):
        # return true if selected_sensor is the current sensor. Otherwise return false.
        if self._DaikinClimateSettings_Object.SelectedSensor == sensor_index:
            return True
        else:
            return False


# get_climate_sensor_temperature
# Function is used to get the temperature of a given SensorIndex.
def get_climate_sensor_temperature(self, sensor_index):
    if isinstance(sensor_index, SensorIndex):

        # if selected sensor is either ExternalSensor
        # AND it's not the current sensor
        # AND PiZone isn't polling for the value,
        #   return None
        if ((sensor_index == SensorIndex.Sensor1) or (sensor_index == SensorIndex.Sensor2)) and (
                self._DaikinClimateSettings_Object.SelectedSensor != sensor_index) and (
                self._PollExternalSensors == 0):
            return None
        else:
            sensor_value = self._DaikinClimateSettings_Object.TempSensorValues[sensor_index]
            # Don't report sensor value if it's value hasn't been received yet
            if sensor_value != 255:
                return sensor_value
            else:
                return None


# get_climate_external_sensor_count
# Function returns the number of configured external sensors on the Daikin Unit
def get_climate_external_sensor_count(self):
    # NumberOfSensors is for 'selectable' for unit so will be 1,2 or 3
    # Thus, External sensors are value - 1 for the always present internal sensor
    return self._DaikinClimateInfo_Object.NumberOfSensors - 1


# get_climate_current_temperature
# Function is used to return the current temp value of PiZone
def get_climate_current_temperature(self):
    # Check which is the select temp sensor and return value
    return self._DaikinClimateSettings_Object.TempSensorValues[
                              self._DaikinClimateSettings_Object.SelectedSensor]


# set_climate_temp_sensor
# Function is used to alter the current climate temp sensor of PiZone
# Note: Once updated, SetAcTempReadSensor frame needs to be sent to SkyZone,
#   otherwise value will be lost next poll to SkyZone (BasicInfo)
def set_climate_temp_sensor(self, sensor_index):
    if isinstance(sensor_index, SensorIndex):
        if self._DaikinClimateSettings_Object.SelectedSensor != sensor_index:
            # limit value to Sensor2, as Outdoor/Refrigerant are not part of frame
            # and only used for internal indexing of temperatures.
            if sensor_index <= SensorIndex.Sensor2:
                self._DaikinClimateSettings_Object.SelectedSensor = sensor_index
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.TEMP_SENSOR)


# get_climate_fan_speed
# Function is used to return the current fan speed for the current mode of PiZone - class FanSpeed
def get_climate_fan_speed(self):
    # get current selected mode from AC and select corresponding set temp.
    # off
    if get_climate_mode(self) == AcStateMode.MODE_OFF:
        return FanSpeed.NA
    # heat
    if get_climate_mode(self) == AcStateMode.MODE_HEAT:
        return self._DaikinClimateSettings_Object.HeatFanState.FanSpeed
    # dry
    if get_climate_mode(self) == AcStateMode.MODE_DRY:
        # always set to low.
        return FanSpeed.LOW
    # cool/fan/auto
    else:
        return self._DaikinClimateSettings_Object.CoolFanState.FanSpeed


# set_climate_fan_speed
# Function is used to alter the current fan speed  for the current mode of PiZone
# Note: Once updated, sync_control_info frame needs to be sent to SkyZone,
#   otherwise value will be lost next poll to SkyZone (BasicInfo).
def set_climate_fan_speed(self, fan_speed):
    # Check FanSpeed is valid
    if isinstance(fan_speed, FanSpeed) and (fan_speed != FanSpeed.NA):
        # Check for current mode (cool/heat). Default (0) is FAN, so no need to check for 'init' value.
        # Check FanMode based on FanSpeed
        if (fan_speed == FanSpeed.LOW) or (fan_speed == FanSpeed.MED) or (fan_speed == FanSpeed.HIGH):
            fan_mode = FanMode.FAN
        elif (fan_speed == FanSpeed.AUTO_LOW) or (fan_speed == FanSpeed.AUTO_MED) or (fan_speed == FanSpeed.AUTO_HIGH):
            fan_mode = FanMode.AUTO
        else:
            fan_mode = FanMode.MULTI_ZONING

        # HEAT
        if get_climate_mode(self) == AcStateMode.MODE_HEAT:
            # Update 'heat' variables
            if self._DaikinClimateSettings_Object.HeatFanState.FanSpeed != fan_speed or \
                    self._DaikinClimateSettings_Object.HeatFanState.FanMode != fan_mode:
                self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = fan_speed
                self._DaikinClimateSettings_Object.HeatFanState.FanMode = fan_mode
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.FAN_STATE)
        # COOL / FAN
        elif get_climate_mode(self) == AcStateMode.MODE_COOL or get_climate_mode(self) == AcStateMode.MODE_FAN:
            # Update 'cool' variables
            if self._DaikinClimateSettings_Object.CoolFanState.FanSpeed != fan_speed or \
                    self._DaikinClimateSettings_Object.CoolFanState.FanMode != fan_mode:
                self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = fan_speed
                self._DaikinClimateSettings_Object.CoolFanState.FanMode = fan_mode
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.FAN_STATE)
        # AUTO/FAN
        elif get_climate_mode(self) == AcStateMode.MODE_AUTO:
            # Update both (as per app)
            if self._DaikinClimateSettings_Object.CoolFanState.FanSpeed != fan_speed or \
                    self._DaikinClimateSettings_Object.CoolFanState.FanMode != fan_mode or \
                    self._DaikinClimateSettings_Object.HeatFanState.FanSpeed != fan_speed or \
                    self._DaikinClimateSettings_Object.HeatFanState.FanMode != fan_mode:
                self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = fan_speed
                self._DaikinClimateSettings_Object.CoolFanState.FanMode = fan_mode
                self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = fan_speed
                self._DaikinClimateSettings_Object.HeatFanState.FanMode = fan_mode
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask,
                                           UpdateRequest.FAN_STATE)
        # DRY/OFF
        else:
            # Speed/Fan settings ignored.
            pass


# get_climate_zone_state
# Function returns True if the zone_index is currently Active
def get_climate_zone_state(self, zone_index):
    return self._DaikinClimateSettings_Object.Zone[zone_index] == ZoneState.ACTIVE


# get_climate_number_of_zones
# Function is used to return the number of configured zones on the Daikin Unit
def get_climate_number_of_zones(self):
    return self._DaikinClimateInfo_Object.NumberOfZones


# get_climate_zone_name
# Function is used to get the name of the zone as given from the Daikin Unit
def get_climate_zone_name(self, zone_index):
    return self._DaikinClimateInfo_Object.ZoneName[zone_index]


# UpdateZoneState
# Function updates the zone
def update_zone_state(self, zone_index, zone_state):
    # Check each bit and set corresponding zone. Check for 'max' zones supported
    if isinstance(zone_state, ZoneState):
        if zone_index < self._DaikinClimateInfo_Object.NumberOfZones:
            if self._DaikinClimateSettings_Object.Zone[zone_index] != zone_state:
                self._DaikinClimateSettings_Object.Zone[zone_index] = zone_state
                # Set mask that update has occurred and to ignore current update if in progress
                self._DaikinClimateSettings_Object.UpdateRequestMask = \
                    UpdateRequest.set_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.ZONE)

    # Check to make sure all zones are not switched off
    any_zone_active = False
    for x in range(0, self._DaikinClimateInfo_Object.NumberOfZones):
        if self._DaikinClimateSettings_Object.Zone[x] == ZoneState.ACTIVE:
            any_zone_active = True

    if not any_zone_active:
        _LOGGER.error('No Zone selected. This may cause permanent damage to your AC system!')


# set_climate_zone_active/set_climate_zone_inactive
# Functions are used to set a zone (zone_index) to Active/Inactive
def set_climate_zone_active(self, zone_index):
    update_zone_state(self, zone_index, ZoneState.ACTIVE)


def set_climate_zone_inactive(self, zone_index):
    update_zone_state(self, zone_index, ZoneState.INACTIVE)


# Other Functions
def get_indoor_part_number(self):
    return self._DaikinClimateInfo_Object.IndoorUnitPartNumber


def get_outdoor_part_number(self):
    return self._DaikinClimateInfo_Object.OutdoorUnitPartNumber


def get_climate_error_codes(self):
    return self._DaikinClimateInfo_Object.ErrorCodes


def get_climate_history_error_codes(self):
    return self._DaikinClimateInfo_Object.HistoryErrorCodes


def get_climate_clear_filter_flag(self):
    return self._DaikinClimateInfo_Object.ClearFilter


def get_climate_min_supported_temp(self):
    return min(self._DaikinClimateInfo_Object.MinCoolTemp, self._DaikinClimateInfo_Object.MinHeatTemp)


def get_climate_max_supported_temp(self):
    return max(self._DaikinClimateInfo_Object.MaxCoolTemp, self._DaikinClimateInfo_Object.MaxHeatTemp)


# update_temp_sensor_data_process
# Function to cycle though the internal and refrigerant temp sensors.
def update_temp_sensor_data_process(self):
    # Update using 'service' mode (prevent changing AC unit 'guide' temp)
    # Enter service mode (b2)
    self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.SERVICE
    send_receive_frame(self, "SetInternalAcMode")

    # Now cycle through all Internal and Refrigerant sensors (CurrentSelected is updated via BasicInfo request)

    # Refrigerant
    self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT

    # Poll unit switch and wait for 1.5 to get updated temp value.
    for x in range(0, C_DaikinDelay_ServiceModeInfoUpdate):
        send_receive_frame(self, "GetServiceRequestData")
        time.sleep(C_DaikinDelay_ServiceRequest)

    # Check CurrentSelected is not Internal.
    if self._DaikinClimateSettings_Object.SelectedSensor != SensorIndex.Internal:
        # Internal
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.INTERNAL

        # Poll unit switch and wait for 1.5 to get updated temp value.
        send_receive_frame(self, "GetServiceRequestData")
        time.sleep(C_DaikinDelay_ServiceRequest)

        # Set service back to internal mode for next call
        # Refrigerant
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT
        send_receive_frame(self, "GetServiceRequestData")

    # Exit service mode
    self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.NORMAL
    send_receive_frame(self, "SetInternalAcMode")


# update_external_temp_sensor_data_process
# Function to cycle though the external temp sensors.
# Function should not be used if either sensor can have wildly different values.
# Even though the sensor is selected for a brief time,
#   the Daikin AC unit will 'keep' the value for ~3minutes before releasing it.
# This means if you have warm and cool 'zone', the unit will constantly start/stop whenever the logic is run.
# Not recommended  to be used unless you 'alter' the target temp to keep the unit functional across all zones.
def update_external_temp_sensor_data_process(self):
    # Lockout SyncClimateInfo whilst checking temp sensors.
    self._SyncClimateInfoLockout = 1

    # Store current_sensor in-case external temp sensors are fitted to AC.
    current_sensor = self._DaikinClimateSettings_Object.SelectedSensor

    # Update 'external sensors'
    # Only method is to change selected sensor and wait for updated temp.
    # Side affect is that if other external sensor is higher/lower than current heating/cooling temp,
    # AC unit may switch modes briefly whilst the sensors are switched
    # Full process takes ~20s to switch.
    if (self._PollExternalSensors == 1) and (self._DaikinClimateInfo_Object.NumberOfSensors > 1):

        # Enter service mode (b2) and set read to CURRENT_SETTING (room temp sensors)
        self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.SERVICE
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.CURRENT_SETTING
        send_receive_frame(self, "SetInternalAcMode")
        send_receive_frame(self, "GetServiceRequestData")

        # Check for sensor 1 (ext1) and 2 (ext2)
        for x in range(1, self._DaikinClimateInfo_Object.NumberOfSensors):

            # Skip 'current_sensor' if PowerOn, otherwise read during PowerOff, CurrentTemp value isn't updated.
            if (x == 1) and ((current_sensor != SensorIndex.Sensor1) or (
                    self._DaikinClimateSettings_Object.PowerOnState != AcPowerState.ON)):
                if self._DebugModeLevel >= 1:
                    _LOGGER.debug('Sensor to int. Sensor1: %s', SensorIndex.Sensor1)
                self._DaikinClimateSettings_Object.SelectedSensor = SensorIndex.Sensor1
                send_receive_frame(self, "SetAcTempReadSensor")
                time.sleep(C_DaikinDelay_TempSensorChange)

                # Poll unit switch and wait for 1.5 to get updated temp value.
                for y in range(0, C_DaikinDelay_ServiceModeInfoUpdate):
                    send_receive_frame(self, "GetServiceRequestData")
                    time.sleep(C_DaikinDelay_ServiceRequest)

            if (x == 2) and ((current_sensor != SensorIndex.Sensor2) or (
                    self._DaikinClimateSettings_Object.PowerOnState != AcPowerState.ON)):
                if self._DebugModeLevel >= 1:
                    _LOGGER.debug('Sensor to int. Sensor2: %s', SensorIndex.Sensor2)
                self._DaikinClimateSettings_Object.SelectedSensor = SensorIndex.Sensor2
                send_receive_frame(self, "SetAcTempReadSensor")
                time.sleep(C_DaikinDelay_TempSensorChange)

                # Poll unit switch and wait for 1.5 to get updated temp value.
                for y in range(0, C_DaikinDelay_ServiceModeInfoUpdate):
                    send_receive_frame(self, "GetServiceRequestData")
                    time.sleep(C_DaikinDelay_ServiceRequest)

        # Reset back to refrigerant for other sensor read
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT
        # Set sensor back to original value if External sensors present
        while self._DaikinClimateSettings_Object.SelectedSensor != current_sensor:
            _LOGGER.debug('Reset sensor back to: %s', current_sensor)
            self._DaikinClimateSettings_Object.SelectedSensor = current_sensor
            send_receive_frame(self, "SetAcTempReadSensor")
            time.sleep(C_DaikinDelay_TempSensorChange)
            send_receive_frame(self, "BasicInfoServiceMode")

    # Release lock
    self._SyncClimateInfoLockout = 0


# Interfaces used to generate frames to get/set SkyZone unit via network interface
def create_initial_info_frame(self):
    return create_request_frame(self, C_REQUEST_GETUP, C_PCD_InitialInfo)


def create_basic_info_frame(self):
    return create_request_frame(self, C_REQUEST_GETUP, C_PCD_BasicInfo)


def create_sync_control_info_frame(self):
    return create_request_frame(self, C_REQUEST_SET, C_PCD_ControlInfo)


def create_get_service_request_data_frame(self):
    return create_request_frame(self, C_REQUEST_GET, C_PCD_GetLocalSetting)


def create_set_internal_ac_mode_frame(self):
    return create_request_frame(self, C_REQUEST_SET, C_PCD_InternalAcMode)


def create_set_ac_temp_read_sensor_frame(self):
    return create_request_frame(self, C_REQUEST_SET, C_PCD_SelectSensor)


def create_get_zone_names_frame(self):
    return create_request_frame(self, C_REQUEST_GETUP, C_PCD_GetZoneNames)


def create_get_sensor_zone_names_frame(self):
    return create_request_frame(self, C_REQUEST_GETUP, C_PCD_GetSensorNames)


C_DaikinRequest = {
    'InitialInfo': create_initial_info_frame,
    'BasicInfo': create_basic_info_frame,
    'BasicInfoServiceMode': create_basic_info_frame,
    'SyncControlInfo': create_sync_control_info_frame,
    'GetServiceRequestData': create_get_service_request_data_frame,
    'SetInternalAcMode': create_set_internal_ac_mode_frame,
    'SetAcTempReadSensor': create_set_ac_temp_read_sensor_frame,
    'GetZoneNames': create_get_zone_names_frame,
    'GetSensorZoneNames': create_get_sensor_zone_names_frame
}


# send_receive_frame
# Function to send frame onto Network and wait for response from SkyZone.
def send_receive_frame(self, frame_index):
    # perform TCP SYN
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.settimeout(5.0)
    port_number = 80
    if self._IpAdd != '0.0.0.0':
        try:
            tcp_socket.connect((self._IpAdd, port_number))

            # Get initial info to create instance.
            conn = http.client.HTTPConnection(self._IpAdd, port_number)
            # Generate Init request and process response
            # lock out basic info
            if (frame_index == "BasicInfo") and (self._SyncClimateInfoLockout == 1):
                # skip generating frame as lockout is in progress
                pass
            else:
                request_frame = C_DaikinRequest[frame_index](self)
                conn.request("GET", "/node/object?frame={}".format(request_frame))
                resp = conn.getresponse()
                data = resp.read().decode()
                conn.close()
                tcp_socket.close()
                process_received_packet(self, data)

        except OSError as error:
            _LOGGER.error("Could not send TCP Request: %s", error)
            tcp_socket.close()


# process_received_packet
# Function to process incoming response from SkyZone.
def process_received_packet(self, incoming_packet):
    # trim start, parse to decoder
    if incoming_packet[0:13] == 'ret=OK,frame=':
        decode_frame(self, incoming_packet[13: len(incoming_packet)])
    else:
        if self._DebugModeLevel >= 1:
            _LOGGER.debug('Error: %s', incoming_packet[0:13])


# decode_frame
# Function decodes incoming string from SkyZone and calls required sub-service to process information returned.
def decode_frame(self, incoming_string):
    incoming_info = bytearray()
    # get frame=xxx values
    decoded_message = base64.b64decode(incoming_string)

    if decoded_message[4] != 0:
        # Pw not correct
        _LOGGER.error('Password is not correct(%s). Please check and re-enter!', self._Pwd)
        self._IpAdd = '0.0.0.0'
        return
    elif len(decoded_message) == 17:
        # set request response level message
        incoming_info = decoded_message
    else:
        # get request response level message
        # read byte 14 to get response info
        info_size = int(decoded_message[14])
        # add response code for case selection.
        incoming_info.append(decoded_message[13])
        if info_size > 0:
            for d in decoded_message[15:(15 + info_size)]:
                incoming_info.append(d)

    if self._DebugModeLevel >= 3:
        _LOGGER.debug('Incoming Type  : %s', (decoded_message[13]))
        # for e in incoming_info : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )

    process_incoming_get_response(self, incoming_info)

    return incoming_info


# process_incoming_get_response
# Determines which AC frame has been transmitted and calls according function to process information.
# Unused/invalid frames are ignored.
def process_incoming_get_response(self, incoming_info):
    if incoming_info[0] in C_DaikinIncomingResponse:
        C_DaikinIncomingResponse[incoming_info[0]](self, incoming_info[1:len(incoming_info)])
    elif len(incoming_info) == 17:
        # Confirmation response from unit
        if incoming_info[13] in C_DaikinIncomingResponse:
            C_DaikinIncomingResponse[incoming_info[13]](self, incoming_info)

        # for e in incoming_info : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )
        # else:
        if self._DebugModeLevel >= 3:
            _LOGGER.debug('Not Supported: %s', "%5x" % incoming_info[0])
    return
