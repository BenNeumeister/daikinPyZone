import base64

from daikinPyZone.daikinConstants import *
from daikinPyZone.daikinClasses import (
    resolve_fan_speed_for_data_frame,
    resolve_sensor_name_to_index,
    get_zone_bit_mask_from_zone_state,
    UpdateRequest)


# calc_password_hi_byte
# Function calculates the high byte based on the local PIN/Password
def calc_password_hi_byte(password):
    return (int(int(password) / 1000) << 4) + int((int(password) % 1000) / 100)


# calc_password_low_byte
# Function calculates the Low byte based on the local PIN/Password
def calc_password_low_byte(password):
    return (int((int(password) % 100) / 10) << 4) + (int(password) % 10)


# calculate_daikin_checksum
# Function calculates the checksum for the frame
def calculate_daikin_checksum(header_bytes, data_bytes):
    # Add all values in Header/Data bytes. Checksum= total /256& 0xFF and total & 0xFF
    # Note: Android app doesn't appear to do checksum verification. Assuming SkyZone controller does.
    data_a = bytes(header_bytes)
    data_b = bytes(data_bytes)
    byte_sum = 0

    for d in data_a:
        byte_sum += d
    for e in data_b:
        byte_sum += e

    checksum = C_DaikinChecksum
    checksum[0] = int(byte_sum / 256) & 0xFF
    checksum[1] = byte_sum & 0xFF

    return checksum


# assemble_transmission_frame
# Function assembles the frame for transmission, merging together the header, data and checksum bytes
def assemble_transmission_frame(header_bytes, data_bytes, checksum_bytes):
    # Ensure all items are in byte format
    data_a = bytearray(header_bytes)
    data_b = bytearray(data_bytes)
    data_c = bytearray(checksum_bytes)

    assembled_array = data_a
    for a in data_b:
        assembled_array.append(a)
    for b in data_c:
        assembled_array.append(b)

    # Encode into base64
    encoded = base64.b64encode(assembled_array)
    return encoded


# create_data_request_frame
# Function creates a DataRequest array from the template and inserts PCD type.
def create_data_request_frame(pcd):
    data = C_DaikinDataRequest
    data[5] = pcd
    return data


# create_ac_state_data_frame
# Function creates a set AcState Data array from the template
#   and inserts current settings from PiZone instance for transmissions
def create_ac_state_data_frame(self):
    # reset UpdateRequestMask flags
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.AC_STATE)
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.POWER_STATE)
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.TARGET_TEMP)
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.FAN_STATE)
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.ZONE)

    data = C_DaikinDataAcState

    data[7] = self._DaikinClimateSettings_Object.AcStateModeValue +\
        (self._DaikinClimateSettings_Object.PowerOnState << 3)
    data[8] = self._DaikinClimateSettings_Object.CoolSetTemp
    data[10] = self._DaikinClimateSettings_Object.HeatSetTemp
    data[12] = (self._DaikinClimateSettings_Object.CoolFanState.FanMode.value << 4) + \
               (resolve_fan_speed_for_data_frame(self._DaikinClimateSettings_Object.CoolFanState.FanSpeed) & 0x0F)
    data[13] = (self._DaikinClimateSettings_Object.HeatFanState.FanMode << 4) + \
               (resolve_fan_speed_for_data_frame(self._DaikinClimateSettings_Object.HeatFanState.FanSpeed) & 0x0F)
    data[14] = get_zone_bit_mask_from_zone_state(self)

    return data


# create_internal_ac_state_data_frame
# Function creates a set AcMode Data array from the template and inserts the mode PiZone wants to switch to
def create_internal_ac_state_data_frame(self):
    data = C_DaikinDataInternalMode
    data[7] = self._DaikinClimateSettings_Object.InternalAcMode.value
    return data


# create_local_setting_data_frame
# Function creates a set LocalSettings Data array from the template and inserts the Sensor PiZone wants to switch to
def create_local_setting_data_frame(self):
    data = C_DaikinDataControlInfoTemp
    data[8] = self._DaikinClimateSettings_Object.ServiceModeSensor.value
    return data


# create_sensor_set_data_frame
# Function creates a set Sensor Data array from the template and inserts the Sensor PiZone wants to switch to
def create_sensor_set_data_frame(self):
    # Reset UpdateRequestMask flag
    self._DaikinClimateSettings_Object.UpdateRequestMask = \
        UpdateRequest.reset_flag(self._DaikinClimateSettings_Object.UpdateRequestMask, UpdateRequest.TEMP_SENSOR)
    
    data = C_DaikinDataSensorSelect
    data[7] = resolve_sensor_name_to_index(self,
                                           self._DaikinClimateInfo_Object.TempSensorName[
                                               self._DaikinClimateSettings_Object.SelectedSensor])
    return data


# create_request_frame
# Function creates the request frame based on given parameters
def create_request_frame(self, request_type, pcd):
    header = C_DaikinHeader
    header[3] = request_type

    # Only populate password if set. Otherwise default (0xFF, 0xFF) is ok.
    if self._Pwd != 0000:
        header[5] = calc_password_hi_byte(self._Pwd)
        header[6] = calc_password_low_byte(self._Pwd)

    data = ''

    # 0xA0 - Get all info from unit
    if pcd == C_PCD_BasicInfo:
        data = create_data_request_frame(C_PCD_BasicInfo)
    # 0xA1 - Get unit type and limits
    elif pcd == C_PCD_InitialInfo:
        data = create_data_request_frame(C_PCD_InitialInfo)
    # 0xB0 -  Get service info data
    elif pcd == C_PCD_ControlInfo:
        data = create_ac_state_data_frame(self)
    # 0xB2 -  Set InternalAcMode
    elif pcd == C_PCD_InternalAcMode:
        data = create_internal_ac_state_data_frame(self)
    # 0xB3 - Set ref sensor
    elif pcd == C_PCD_SelectSensor:
        data = create_sensor_set_data_frame(self)
    # 0xC0 - Request service mode
    elif pcd == C_PCD_GetLocalSetting:
        data = create_local_setting_data_frame(self)
    # 0xD0 - Request zone names
    elif pcd == C_PCD_GetZoneNames:
        data = create_data_request_frame(C_PCD_GetZoneNames)
    # 0xD2 - Get sensor names
    elif pcd == C_PCD_GetSensorNames:
        data = create_data_request_frame(C_PCD_GetSensorNames)
    else:
        pass
        # if(self._DebugModeLevel >= 1):
        #   print('Not supported')

    # if(self._DebugModeLevel >= 4):
    # for e in data : print ("%5x"%e," / " ,e, " / ", chr(int(e)) )

    checksum = calculate_daikin_checksum(header, data)

    frame = assemble_transmission_frame(header, data, checksum)

    return frame.decode('UTF-8')
