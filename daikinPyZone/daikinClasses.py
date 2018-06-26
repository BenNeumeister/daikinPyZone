from enum import IntEnum, unique

@unique
class InternalAcMode(IntEnum):
        NORMAL = 0
        INSPECTION = 1
        TEST = 2
        LOCAL_SETTING = 3
        SERVICE = 4
        SERVICE2 = 5
        INITIALIZING =6 
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
        LOW = 0         #( FanMode = FAN)
        MED = 1         #( FanMode = FAN)
        HIGH =2         #( FanMode = FAN)
        AUTO_LOW = 3    #( FanMode = AUTO)
        AUTO_MED = 4    #( FanMode = AUTO)
        AUTO_HIGH =5    #( FanMode = AUTO)
        AUTO = 6        #( FanMode = MULTI_ZONING)
        NA = 7          #( N/A. Ac Off, Dry)
        
FAN_MODES = ['Low', 'Med', 'High', 'Auto - Low', 'Auto - Med', 'Auto - High', 'Auto', 'N/A']
FAN_MODE_MAP = {FAN_MODES[0]:FanSpeed.LOW, FAN_MODES[1]:FanSpeed.MED, FAN_MODES[2]:FanSpeed.HIGH, FAN_MODES[3]:FanSpeed.AUTO_LOW, FAN_MODES[4]:FanSpeed.AUTO_MED, FAN_MODES[5]:FanSpeed.AUTO_HIGH, FAN_MODES[6]:FanSpeed.AUTO, FAN_MODES[7]:FanSpeed.NA}
 
@unique 
class AcStateMode(IntEnum):
        MODE_FAN = 0
        MODE_DRY = 1
        MODE_AUTO = 2
        MODE_COOL = 3
        MODE_HEAT = 4
        MODE_OFF = 5

OPERATION_MODES = ['fan_only', 'dry', 'auto', 'cool', 'heat', 'off']
OPERATION_MODES_MAP = {OPERATION_MODES[0]:AcStateMode.MODE_FAN , OPERATION_MODES[1]:AcStateMode.MODE_DRY , OPERATION_MODES[2]:AcStateMode.MODE_AUTO , OPERATION_MODES[3]:AcStateMode.MODE_COOL , OPERATION_MODES[4]:AcStateMode.MODE_HEAT, OPERATION_MODES[5]:AcStateMode.MODE_OFF}
        
@unique        
class SensorSelect(IntEnum):
        CURRENTSETTING = 0
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
    __slots__ = ['FanMode','FanSpeed']
    
    def __init__(self, FanMode = FanMode.AUTO, FanSpeed = FanSpeed.AUTO):
        self.FanMode = FanMode
        self.FanSpeed = FanSpeed

class DaikinSensorNames(object):
    __slots__ = ['data']
    
    def __init__(self, sensor1name = 'Sensor1', sensor2name = 'Sensor2'):
        self.data = ['Internal Sensor', sensor1name, sensor2name, 'Outdoor Sensor', 'Refrigerant Sensor']
                        
    def __setitem__(self, idx, value):
        self.data[idx] = value
        
    def __getitem__(self,item):
        return self.data[item]
        
    @property
    def Internal(self):
        return self.data[SensorIndex.Internal]
        
    @property
    def Sensor1(self):
        return self.data[SensorIndex.Sensor1]
        
    @property
    def Sensor2(self):
        return self.data[SensorIndex.Sensor2]
        
    @property
    def Outdoor(self):
        return self.data[SensorIndex.Outdoor]
        
    @property
    def Refrigerant(self):
        return self.data[SensorIndex.Refrigerant]
            
class DaikinTempSensorValue(object):
    __slots__ = ['data']
    
    def __init__(self, internalSensorValue = 255, sensor1value = 255, sensor2value = 255, outdoorSensorValue = 255, coolantSensorValue = 255):
        self.data = [internalSensorValue, sensor1value, sensor2value, outdoorSensorValue, coolantSensorValue]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value
        
    def __getitem__(self,item):
        return self.data[item]
        
    @property
    def Internal(self):
        return self.data[SensorIndex.Internal]

    @property
    def Sensor1(self):
        return self.data[SensorIndex.Sensor1]
        
    @property
    def Sensor2(self):
        return self.data[SensorIndex.Sensor2]
                
    @property
    def Outdoor(self):
        return self.data[SensorIndex.Outdoor]

    @property
    def Refrigerant(self):
        return self.data[SensorIndex.Refrigerant] 

class DaikinZoneNames(object):
    __slots__ = ['data']
    
    def __init__(self, zone1 = 'Zone1', zone2 = 'Zone1', zone3 = 'Zone3', zone4 = 'Zone4', zone5 = 'Zone5', zone6 = 'Zone6', zone7 = 'Zone7', zone8 = 'Zone8'):
        self.data = [zone1, zone2, zone3, zone4, zone5, zone6, zone7, zone8]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __getitem__(self,item):
        return self.data[item]
        
    @property
    def Zone1(self):
        return self.data[0]

    @property
    def Zone2(self):
        return self.data[1]
        
    @property
    def Zone3(self):
        return self.data[2]
        
    @property
    def Zone4(self):
        return self.data[3]
        
    @property
    def Zone5(self):
        return self.data[4]
        
    @property
    def Zone6(self):
        return self.data[5]
        
    @property
    def Zone7(self):
        return self.data[6]
        
    @property
    def Zone8(self):
        return self.data[7]      

class DaikinZoneState(object):
    __slots__ = ['data']
    
    def __init__(self):
        self.data = [ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE, ZoneState.INACTIVE]
        
    def __setitem__(self, idx, value):
        self.data[idx] = value

    def __getitem__(self,item):
        return self.data[item]
        
    @property
    def Zone1(self):
        return self.data[0]

    @property
    def Zone2(self):
        return self.data[1]
        
    @property
    def Zone3(self):
        return self.data[2]
        
    @property
    def Zone4(self):
        return self.data[3]
        
    @property
    def Zone5(self):
        return self.data[4]
        
    @property
    def Zone6(self):
        return self.data[5]
        
    @property
    def Zone7(self):
        return self.data[6]
        
    @property
    def Zone8(self):
        return self.data[7]

class DaikinClimateInformation(object):

    __slots__ = ['IndoorUnitPartNumber','OutdoorUnitPartNumber','MaxCoolTemp','MinCoolTemp','MaxHeatTemp','MinHeatTemp','NumberOfZones','ZoneName','NumberOfSensors','TempSensorName','ErrorCodes','HistoryErrorCodes','ClearFilter']

    def __init__(self, indoorUnit = 'Unknown', outdoorUnit = 'Unknown', maxCoolTemp = 23, minCoolTemp = 18, maxHeatTemp = 23, minHeatTemp = 18, numOfZones = 1, numOfSensors = 1, airFlowRatio =100,  isCommonZone = 1, errCodes = 0, hisErrCode = 0, cleanFilterFlag = 0):

        #Unit part numbers
        self.IndoorUnitPartNumber = indoorUnit
        self.OutdoorUnitPartNumber = outdoorUnit

        #Set range values
        self.MaxCoolTemp = maxCoolTemp
        self.MinCoolTemp = minCoolTemp
        self.MaxHeatTemp = maxHeatTemp
        self.MinHeatTemp = minHeatTemp
        self.NumberOfZones = numOfZones

        #Zone names
        self.ZoneName = DaikinZoneNames()

        #Optional temperature sensor names
        self.NumberOfSensors = numOfSensors
        self.TempSensorName = DaikinSensorNames()
                
        #Error code info
        self.ErrorCodes = errCodes
        self.HistoryErrorCodes = hisErrCode

        #Filter Clean Flag
        self.ClearFilter = cleanFilterFlag

class DaikinClimateSettings(object):

    __slots__ = ['PowerOnState','Zone','SelectedSensor','ServiceModeSensor','CoolSetTemp','HeatSetTemp','TempSensorValues','AcStateModeValue','InternalAcMode','CoolFanState','HeatFanState']

    def __init__(self, powerOnState = AcPowerState.OFF, acMode = 0, internalAcMode = 0, selectedSensor = 1, serviceModeSensor = 1, coolSetTemp = 21, heatSetTemp = 21, powerState = 0):
        #PowerState
        self.PowerOnState = powerOnState
        
        #Zone Config (bit encoded)
        self.Zone = DaikinZoneState()
        
        #Selected Temp sensor
        self.SelectedSensor = selectedSensor
        self.ServiceModeSensor = serviceModeSensor

        #SetTemp values
        self.CoolSetTemp = coolSetTemp
        self.HeatSetTemp = heatSetTemp

        #Temp sensor values
        self.TempSensorValues = DaikinTempSensorValue()       

        #AC mode
        self.AcStateModeValue = acMode

        #Internal Ac Mode
        self.InternalAcMode = internalAcMode
        
        #FanStates - Cool
        self.CoolFanState = FanInformation()
        
        #FanStates - Heat
        self.HeatFanState = FanInformation()
        
#ConvertModeFlagToAcState
#Function converts ModeFlag to actual mode 
def ConvertModeFlagToAcState( int):
    if(int == 0): return AcStateMode.MODE_FAN
    elif(int == 1): return AcStateMode.MODE_HEAT
    elif(int == 2): return AcStateMode.MODE_COOL
    elif(int == 3): return AcStateMode.MODE_AUTO
    elif(int == 4): return AcStateMode.MODE_AUTO
    elif(int == 5): return AcStateMode.MODE_AUTO
    elif(int == 6): return AcStateMode.MODE_AUTO
    elif(int == 7): return AcStateMode.MODE_DRY
    else: return AcStateMode.MODE_NONE    
    
#DetermineFanInformation
#Function determines fanspeed type from 'value' and FanMode
def DetermineFanInformation(FanModeValue, FanSpeedValue):
    #Depending on FanMode, FanSpeed has different ENUM value (raw value is the same)
    
    l_FanMode = FanMode(FanModeValue)
    
    #Need to check if speed 1-> 5 are in steps or only 1/3/5 are valid.
    if(l_FanMode == FanMode.FAN):
        if(FanSpeedValue == 1):     l_FanSpeed = FanSpeed.LOW
        elif(FanSpeedValue == 3):   l_FanSpeed = FanSpeed.MED
        else:                       l_FanSpeed = FanSpeed.HIGH
        #FanSpeedValue == 5

    elif(l_FanMode == FanMode.AUTO):
        if(FanSpeedValue == 1):     l_FanSpeed = FanSpeed.AUTO_LOW
        elif(FanSpeedValue == 3):   l_FanSpeed = FanSpeed.AUTO_MED
        else:                       l_FanSpeed = FanSpeed.AUTO_HIGH
        #FanSpeedValue == 5
    
    else:
        #(l_FanMode == FanMode.MULTI_ZONING/OFF):
        l_FanSpeed = FanSpeed.AUTO
        
    return FanInformation(l_FanMode, l_FanSpeed)

#ResolveFanSpeedForDataFrame
#Function resolves FanSpeed enum into fan speed value 
def ResolveFanSpeedForDataFrame(FanSpeedEnum):
    if((FanSpeedEnum == FanSpeed.LOW) or (FanSpeedEnum == FanSpeed.AUTO_LOW) or (FanSpeedEnum == FanSpeed.AUTO)):
        return 1
    elif((FanSpeedEnum == FanSpeed.MED) or (FanSpeedEnum == FanSpeed.AUTO_MED)):                                                        
        return 3
    else: return 5    
    
#ResolveSensorNameToIndex
#Function resolves SensorName to sensor index
def ResolveSensorNameToIndex(self, SensorName):
    i= 0
    while i<self._DaikinClimateInfo_Object.NumberOfSensors:
        if(self._DaikinClimateInfo_Object.TempSensorName[i] == SensorName): return i
        i +=1
    return -1    

#UpdateZoneState
#Function updates the zone mask states based on the bit encoded parameter value (1 == Active)
def SyncZoneState(self, ZoneBitValue):
    #check each bit and set corresponding zone. Check for 'max' zones supported
    #check if 'ignore 0' is supported
    for x in range (0, self._DaikinClimateInfo_Object.NumberOfZones):
        if( ZoneBitValue & (1<<x)):
            self._DaikinClimateSettings_Object.Zone[x] = ZoneState.ACTIVE
        else: 
            self._DaikinClimateSettings_Object.Zone[x] = ZoneState.INACTIVE
            
#GetZoneBitMaskFromZoneState
#Function generates a bit encoded parameter value based on which zones are active
def GetZoneBitMaskFromZoneState(self):
    #check each bit and get corresponding zone. Check for 'max' zones supported
    ZoneMaskSum = 0
    
    for x in range (0, self._DaikinClimateInfo_Object.NumberOfZones):
        if( self._DaikinClimateSettings_Object.Zone[x] == ZoneState.ACTIVE):
            ZoneMaskSum += (1 << x)

    return ZoneMaskSum        
