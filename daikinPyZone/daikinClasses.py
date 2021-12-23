from enum import IntEnum, IntFlag, unique, auto


@unique
class InternalAcMode(IntEnum):
    NORMAL = 0
    INSPECTION = 1
    TEST = 2
    LOCAL_SETTING = 3
    SERVICE = 4
    SERVICE2 = 5
    INITIALIZING = 6
    OTHER_ACING = 7


@unique
class AcPowerState(IntEnum):
    OFF = 0
    ON = 1


@unique
class FanMode(IntEnum):
    FAN = 0
    AUTO = 1
    MULTI_ZONING = 2
    OFF = 3


@unique
class FanSpeed(IntEnum):
    LOW = 0         # ( FanMode = FAN)
    MED = 1         # ( FanMode = FAN)
    HIGH = 2        # ( FanMode = FAN)
    AUTO_LOW = 3    # ( FanMode = AUTO)
    AUTO_MED = 4    # ( FanMode = AUTO)
    AUTO_HIGH = 5   # ( FanMode = AUTO)
    AUTO = 6        # ( FanMode = MULTI_ZONING)
    NA = 7          # ( N/A. Ac Off, Dry)


@unique
class UpdateRequest(IntFlag):
    POWER_STATE = auto()     # Power State update (Off)
    AC_STATE = auto()        # AC State update (Heat/Cool/Fan)
    TARGET_TEMP = auto()     # Temperature update
    TEMP_SENSOR = auto()     # Sensor update
    FAN_STATE = auto()       # Fan speed/mode update
    ZONE = auto()            # Zone update

    @classmethod
    def reset_flag(cls, flags, flag_to_remove):
        if isinstance(flags, UpdateRequest):
            if flags | flag_to_remove:
                flags &= ~flag_to_remove
        return flags

    @classmethod
    def set_flag(cls, flags, flag_to_set):
        if flags is None or flags == 0:
            flags = flag_to_set
        elif isinstance(flags, UpdateRequest):
            if flags | flag_to_set:
                flags |= flag_to_set
        return flags


FAN_MODES = ['Low', 'Med', 'High', 'Auto - Low', 'Auto - Med', 'Auto - High', 'Auto', 'N/A']
FAN_MODE_MAP = {
    FAN_MODES[0]: FanSpeed.LOW,
    FAN_MODES[1]: FanSpeed.MED,
    FAN_MODES[2]: FanSpeed.HIGH,
    FAN_MODES[3]: FanSpeed.AUTO_LOW,
    FAN_MODES[4]: FanSpeed.AUTO_MED,
    FAN_MODES[5]: FanSpeed.AUTO_HIGH,
    FAN_MODES[6]: FanSpeed.AUTO,
    FAN_MODES[7]: FanSpeed.NA}


@unique
class AcStateMode(IntEnum):
    MODE_FAN = 0
    MODE_DRY = 1
    MODE_AUTO = 2
    MODE_COOL = 3
    MODE_HEAT = 4
    MODE_OFF = 5


OPERATION_MODES = ['fan_only', 'dry', 'auto', 'cool', 'heat', 'off']
OPERATION_MODES_MAP = {
    OPERATION_MODES[0]: AcStateMode.MODE_FAN,
    OPERATION_MODES[1]: AcStateMode.MODE_DRY,
    OPERATION_MODES[2]: AcStateMode.MODE_AUTO,
    OPERATION_MODES[3]: AcStateMode.MODE_COOL,
    OPERATION_MODES[4]: AcStateMode.MODE_HEAT,
    OPERATION_MODES[5]: AcStateMode.MODE_OFF}


@unique
class SensorSelect(IntEnum):
    CURRENT_SETTING = 0
    INTERNAL = 1
    REFRIGERANT = 2


@unique
class ZoneState(IntEnum):
    INACTIVE = 0
    ACTIVE = 1


@unique
class SensorIndex(IntEnum):
    Internal = 0
    Sensor1 = 1
    Sensor2 = 2
    Outdoor = 3         # Not part of incoming info, but used for temp information
    Refrigerant = 4     # Not part of incoming info, but used for temp information


class FanInformation(object):
    __slots__ = ['FanMode', 'FanSpeed']
    
    def __init__(self,
                 fan_mode=FanMode.AUTO,
                 fan_speed=FanSpeed.AUTO):
        self.FanMode = fan_mode
        self.FanSpeed = fan_speed


class DaikinSensorNames(object):
    __slots__ = ['data']
    
    def __init__(self, sensor_1_name='Sensor1', sensor_2_name='Sensor2'):
        self.data = ['Internal Sensor', sensor_1_name, sensor_2_name, 'Outdoor Sensor', 'Refrigerant Sensor']
                        
    def __setitem__(self, idx, value):
        self.data[idx] = value
        
    def __getitem__(self, item):
        return self.data[item]
        
    @property
    def internal(self):
        return self.data[SensorIndex.Internal]
        
    @property
    def sensor1(self):
        return self.data[SensorIndex.Sensor1]
        
    @property
    def sensor2(self):
        return self.data[SensorIndex.Sensor2]
        
    @property
    def outdoor(self):
        return self.data[SensorIndex.Outdoor]
        
    @property
    def refrigerant(self):
        return self.data[SensorIndex.Refrigerant]


class DaikinTempSensorValue(object):
    __slots__ = ['data']
    
    def __init__(self,
                 internal_sensor=255,
                 sensor1=255,
                 sensor2=255,
                 outdoor_sensor=255,
                 coolant_sensor=255):
        self.data = [internal_sensor,
                     sensor1,
                     sensor2,
                     outdoor_sensor,
                     coolant_sensor]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value
        
    def __getitem__(self, item):
        return self.data[item]
        
    @property
    def internal(self):
        return self.data[SensorIndex.Internal]

    @property
    def sensor1(self):
        return self.data[SensorIndex.Sensor1]
        
    @property
    def sensor2(self):
        return self.data[SensorIndex.Sensor2]
                
    @property
    def outdoor(self):
        return self.data[SensorIndex.Outdoor]

    @property
    def refrigerant(self):
        return self.data[SensorIndex.Refrigerant] 


class DaikinZoneNames(object):
    __slots__ = ['data']
    
    def __init__(self,
                 zone1='Zone1',
                 zone2='Zone2',
                 zone3='Zone3',
                 zone4='Zone4',
                 zone5='Zone5',
                 zone6='Zone6',
                 zone7='Zone7',
                 zone8='Zone8'):
        self.data = [zone1, zone2, zone3, zone4, zone5, zone6, zone7, zone8]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __getitem__(self, item):
        return self.data[item]
        
    @property
    def zone1(self):
        return self.data[0]

    @property
    def zone2(self):
        return self.data[1]
        
    @property
    def zone3(self):
        return self.data[2]
        
    @property
    def zone4(self):
        return self.data[3]
        
    @property
    def zone5(self):
        return self.data[4]
        
    @property
    def zone6(self):
        return self.data[5]
        
    @property
    def zone7(self):
        return self.data[6]
        
    @property
    def zone8(self):
        return self.data[7]


class DaikinZoneState(object):
    __slots__ = ['data']
    
    def __init__(self):
        self.data = [ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE,
                     ZoneState.INACTIVE]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __getitem__(self, item):
        return self.data[item]
        
    @property
    def zone1(self):
        return self.data[0]

    @property
    def zone2(self):
        return self.data[1]
        
    @property
    def zone3(self):
        return self.data[2]
        
    @property
    def zone4(self):
        return self.data[3]
        
    @property
    def zone5(self):
        return self.data[4]
        
    @property
    def zone6(self):
        return self.data[5]
        
    @property
    def zone7(self):
        return self.data[6]
        
    @property
    def zone8(self):
        return self.data[7]


class DaikinClimateInformation(object):

    __slots__ = ['IndoorUnitPartNumber',
                 'OutdoorUnitPartNumber',
                 'MaxCoolTemp',
                 'MinCoolTemp',
                 'MaxHeatTemp',
                 'MinHeatTemp',
                 'NumberOfZones',
                 'ZoneName',
                 'NumberOfSensors',
                 'TempSensorName',
                 'ErrorCodes',
                 'HistoryErrorCodes',
                 'ClearFilter']

    def __init__(self,
                 indoor_unit='Unknown',
                 outdoor_unit='Unknown',
                 max_cool_temp=23,
                 min_cool_temp=18,
                 max_heat_temp=23,
                 min_heat_temp=18,
                 num_of_zones=1,
                 num_of_sensors=1,
                 # air_flow_ratio=100,
                 # is_common_zone=1,
                 error_codes=0,
                 history_error_codes=0,
                 clean_filter_flag=0):

        # Unit part numbers
        self.IndoorUnitPartNumber = indoor_unit
        self.OutdoorUnitPartNumber = outdoor_unit

        # Set range values
        self.MaxCoolTemp = max_cool_temp
        self.MinCoolTemp = min_cool_temp
        self.MaxHeatTemp = max_heat_temp
        self.MinHeatTemp = min_heat_temp
        self.NumberOfZones = num_of_zones

        # Zone names
        self.ZoneName = DaikinZoneNames()

        # Optional temperature sensor names
        self.NumberOfSensors = num_of_sensors
        self.TempSensorName = DaikinSensorNames()
                
        # Error code info
        self.ErrorCodes = error_codes
        self.HistoryErrorCodes = history_error_codes

        # Filter Clean Flag
        self.ClearFilter = clean_filter_flag


class DaikinClimateSettings(object):

    __slots__ = ['UpdateRequestMask',
                 'PowerOnState',
                 'Zone',
                 'SelectedSensor',
                 'ServiceModeSensor',
                 'CoolSetTemp',
                 'HeatSetTemp',
                 'TempSensorValues',
                 'AcStateModeValue',
                 'InternalAcMode',
                 'CoolFanState',
                 'HeatFanState']

    def __init__(self,
                 power_on_state=AcPowerState.OFF,
                 ac_mode=0,
                 internal_ac_mode=0,
                 selected_sensor=1,
                 service_mode_sensor=1,
                 cool_set_temp=21,
                 heat_set_temp=21,
                 update_mask=0):

        # UpdateFlag
        self.UpdateRequestMask = update_mask

        # PowerState
        self.PowerOnState = power_on_state
        
        # Zone Config (bit encoded)
        self.Zone = DaikinZoneState()
        
        # Selected Temp sensor
        self.SelectedSensor = selected_sensor
        self.ServiceModeSensor = service_mode_sensor

        # SetTemp values
        self.CoolSetTemp = cool_set_temp
        self.HeatSetTemp = heat_set_temp

        # Temp sensor values
        self.TempSensorValues = DaikinTempSensorValue()       

        # AC mode
        self.AcStateModeValue = ac_mode

        # Internal Ac Mode
        self.InternalAcMode = internal_ac_mode
        
        # FanStates - Cool
        self.CoolFanState = FanInformation()
        
        # FanStates - Heat
        self.HeatFanState = FanInformation()

        
# convert_mode_flags_to_ac_state
# Function converts ModeFlag to actual mode 
def convert_mode_flags_to_ac_state(mode_flag):
    if mode_flag == 0:
        return AcStateMode.MODE_FAN
    elif mode_flag == 1:
        return AcStateMode.MODE_HEAT
    elif mode_flag == 2:
        return AcStateMode.MODE_COOL
    elif mode_flag == 3:
        return AcStateMode.MODE_AUTO
    elif mode_flag == 4:
        return AcStateMode.MODE_AUTO
    elif mode_flag == 5:
        return AcStateMode.MODE_AUTO
    elif mode_flag == 6:
        return AcStateMode.MODE_AUTO
    elif mode_flag == 7:
        return AcStateMode.MODE_DRY
    else:
        return AcStateMode.MODE_NONE
    
    
# determine_fan_information
# Function determines fan_speed type from 'value' and fan_mode
def determine_fan_information(fan_mode_value, fan_speed_value):
    # Depending on FanMode, FanSpeed has different ENUM value (raw value is the same)
    
    fan_mode = FanMode(fan_mode_value)
    fan_speed = FanSpeed.AUTO
    
    # Need to check if speed 1-> 5 are in steps or only 1/3/5 are valid.
    if fan_mode == FanMode.FAN:
        if fan_speed_value == 1:
            fan_speed = FanSpeed.LOW
        elif fan_speed_value == 3:
            fan_speed = FanSpeed.MED
        else:
            fan_speed = FanSpeed.HIGH
            # fan_speed_value == 5

    elif fan_mode == FanMode.AUTO:
        if fan_speed_value == 1:
            fan_speed = FanSpeed.AUTO_LOW
        elif fan_speed_value == 3:
            fan_speed = FanSpeed.AUTO_MED
        else:
            fan_speed = FanSpeed.AUTO_HIGH
            # fan_speed_value == 5
    else:
        pass
        # (fan_mode == FanMode.MULTI_ZONING/OFF):

    return FanInformation(fan_mode, fan_speed)


# resolve_fan_speed_for_data_frame
# Function resolves FanSpeed enum into fan speed value 
def resolve_fan_speed_for_data_frame(fan_speed):
    if(fan_speed == FanSpeed.LOW) or (fan_speed == FanSpeed.AUTO_LOW) or (fan_speed == FanSpeed.AUTO):
        return 1
    elif(fan_speed == FanSpeed.MED) or (fan_speed == FanSpeed.AUTO_MED):
        return 3
    else:
        return 5
    
    
# resolve_sensor_name_to_index
# Function resolves SensorName to sensor index
def resolve_sensor_name_to_index(self, sensor_name):
    i = 0
    while i < self._DaikinClimateInfo_Object.NumberOfSensors:
        if self._DaikinClimateInfo_Object.TempSensorName[i] == sensor_name:
            return i
        i += 1
    return 255


# sync_zone_state
# Function updates the zone mask states based on the bit encoded parameter value (1 == Active)
def sync_zone_state(self, zone_bit_value):
    # Check each bit and set corresponding zone. Check for 'max' zones supported
    # Check if 'ignore 0' is supported
    for x in range(0, self._DaikinClimateInfo_Object.NumberOfZones):
        if zone_bit_value & (1 << x):
            self._DaikinClimateSettings_Object.Zone[x] = ZoneState.ACTIVE
        else: 
            self._DaikinClimateSettings_Object.Zone[x] = ZoneState.INACTIVE


# get_zone_bit_mask_from_zone_state
# Function generates a bit encoded parameter value based on which zones are active
def get_zone_bit_mask_from_zone_state(self):
    # Check each bit and get corresponding zone. Check for 'max' zones supported
    zone_mask_sum = 0
    
    for x in range(0, self._DaikinClimateInfo_Object.NumberOfZones):
        if self._DaikinClimateSettings_Object.Zone[x] == ZoneState.ACTIVE:
            zone_mask_sum += (1 << x)

    return zone_mask_sum
