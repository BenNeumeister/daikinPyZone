import re
import base64
import socket
import http.client
import time
import logging

from daikinPyZone.daikinConstants import *
from daikinPyZone.daikinCalculate import *

from daikinPyZone.daikinClasses import ( DaikinClimateInformation, DaikinClimateSettings, DetermineFanInformation,
    InternalAcMode, AcStateMode, SensorSelect, SensorIndex, AcPowerState, ConvertModeFlagToAcState,
    FanSpeed, FanSpeed, FanMode,  SyncZoneState, GetZoneBitMaskFromZoneState, ZoneState)

_LOGGER = logging.getLogger(__name__)

#ProcessBasicInfo
#Function processes the 'BasicInfo' from received from the SkyZone unit.
#C_PCD_BasicInfo =0xA0  
def ProcessBasicInfo(self, incomingInfo):
  
    #not needed:
    #onTimer = (incomingInfo[6] >> 4);
    #offTimer = (incomingInfo[6] & 0xF);
    #onTimerCount = (incomingInfo[7] >> 4);
    #offTimerCount = (incomingInfo[7] & 0xF);
    #mNowHour = ((incomingInfo[23]) >> 4) * 10 + (incomingInfo[23] & 0xF);
    #mNowMin = ((incomingInfo[24]) >> 4) * 10 + (incomingInfo[24] & 0xF);
    #airFlowVersion = (incomingInfo[0] >> 1 & 0xF); Keeps track of last airflow change. Cant see it being required.
    #zikoku  = incomingInfo[0]  & 0x20; AcUnit request sets time when !=0
    #acModeAuto = ((incomingInfo[1]  >> 6) & 1); When unit is set to 'auto'. HA will manually control setting, not not required.
    #multiZoningCoefficient = ((incomingInfo[2]) >> 3 & 0x1F) #Cant see usecase, maybe for advanced blending?
    #AirFlowRatio = incomingInfo[5]
    #CommonZone = (incomingInfo[8]  >> 7)
    
    self._DaikinClimateSettings_Object.PowerOnState = (AcPowerState)(incomingInfo[1]  >> 7)  
    self._DaikinClimateSettings_Object.SelectedSensor = (SensorIndex)(incomingInfo[11] >> 4)
    self._DaikinClimateSettings_Object.CoolSetTemp = incomingInfo[18]
    self._DaikinClimateSettings_Object.HeatSetTemp = incomingInfo[20]
    
    self._DaikinClimateSettings_Object.TempSensorValues[self._DaikinClimateSettings_Object.SelectedSensor] = (incomingInfo[14] & 0x7F) 
    self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Outdoor] = (incomingInfo[16] & 0x7F) 

    self._DaikinClimateSettings_Object.AcStateModeValue = ConvertModeFlagToAcState(incomingInfo[1] & 0x7)
    self._DaikinClimateSettings_Object.InternalAcMode = (InternalAcMode)(incomingInfo[2] & 0x7)
    
    l_CoolFanMode = (incomingInfo[3] >> 4 & 0x3)
    l_CoolFanSpeed = (incomingInfo[3] & 0xF)
    l_HeatFanMode = (incomingInfo[4] >> 4 & 0x3)
    l_HeatFanSpeed = (incomingInfo[4] & 0xF)
    l_CoolFanState = DetermineFanInformation(l_CoolFanMode,l_CoolFanSpeed)
    l_HeatFanState = DetermineFanInformation(l_HeatFanMode,l_HeatFanSpeed)
    
    self._DaikinClimateSettings_Object.CoolFanState.FanMode = l_CoolFanState.FanMode
    self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = l_CoolFanState.FanSpeed
    self._DaikinClimateSettings_Object.HeatFanState.FanMode =  l_HeatFanState.FanMode
    self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = l_HeatFanState.FanSpeed
    
    self._DaikinClimateInfo_Object.NumberOfZones = (incomingInfo[8] & 0xF)
    self._DaikinClimateInfo_Object.NumberOfSensors = (incomingInfo[10] & 0xF)
    self._DaikinClimateInfo_Object.ErrorCodes = (incomingInfo[12])
    self._DaikinClimateInfo_Object.HistoryErrorCodes = (incomingInfo[13])
    self._DaikinClimateInfo_Object.ClearFilter = (incomingInfo[0]  & 1)    
    
    SyncZoneState(self, incomingInfo[9])
   
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('-------------------------------------------------------------------------------')
        _LOGGER.debug('Power State: %s | Clean Filter: %s', self._DaikinClimateSettings_Object.PowerOnState, self._DaikinClimateInfo_Object.ClearFilter)
        _LOGGER.debug('Sensor Temp: %s | Outdoor Temp: %s',self._DaikinClimateSettings_Object.TempSensorValues[self._DaikinClimateSettings_Object.SelectedSensor] ,self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Outdoor])
        _LOGGER.debug('AcMode: %s | Internal Ac Mode: %s',self._DaikinClimateSettings_Object.AcStateModeValue , self._DaikinClimateSettings_Object.InternalAcMode)
        _LOGGER.debug('Cool Set Temp: %s | Heat Set Temp: %s',self._DaikinClimateSettings_Object.CoolSetTemp,self._DaikinClimateSettings_Object.HeatSetTemp)
        _LOGGER.debug('CoolFanMode: %s | CoolFanSpeed: %s',self._DaikinClimateSettings_Object.CoolFanState.FanMode,self._DaikinClimateSettings_Object.CoolFanState.FanSpeed)
        _LOGGER.debug('HeatFanMode: %s | HeatFanSpeed: %s',self._DaikinClimateSettings_Object.HeatFanState.FanMode,self._DaikinClimateSettings_Object.HeatFanState.FanSpeed)
        _LOGGER.debug('Number Of Zones: %s | Selected Zones: %s',self._DaikinClimateInfo_Object.NumberOfZones, GetZoneBitMaskFromZoneState(self) )
        _LOGGER.debug('Number Of Sensors: %s | Selected Sensor: %s',self._DaikinClimateInfo_Object.NumberOfSensors,  self._DaikinClimateSettings_Object.SelectedSensor)
        _LOGGER.debug('ErrorCode: %s | HistoryErrorCode: %s',self._DaikinClimateInfo_Object.ErrorCodes,self._DaikinClimateInfo_Object.HistoryErrorCodes)

#ProcessInitialInfo
#Function processes the 'InitialInfo' from received from the SkyZone unit. 
#C_PCD_InitialInfo = 0xA1                # Get unit type and limits
def ProcessInitialInfo(self, incomingInfo):

    #Convert byteArray to string of characters
    IncomingString = ''.join(chr(x) for x in incomingInfo[0:32])
    
    if(self._DebugModeLevel >= 2):
        _LOGGER.debug('Indoor/Outdoor Unit: %s',IncomingString)
    
    self._DaikinClimateInfo_Object.IndoorUnitPartNumber = str(IncomingString[1:12]).rstrip('\x00 ')
    self._DaikinClimateInfo_Object.OutdoorUnitPartNumber = str(IncomingString[16:30]).rstrip('\x00 ')
    self._DaikinClimateInfo_Object.MaxCoolTemp = incomingInfo[31]
    self._DaikinClimateInfo_Object.MinCoolTemp = incomingInfo[32]
    self._DaikinClimateInfo_Object.MaxHeatTemp = incomingInfo[33]
    self._DaikinClimateInfo_Object.MinHeatTemp = incomingInfo[34]
    
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('Indoor Unit#: %s | Outdoor Unit #: %s', self._DaikinClimateInfo_Object.IndoorUnitPartNumber,self._DaikinClimateInfo_Object.OutdoorUnitPartNumber)
        _LOGGER.debug('Max Cool Temp: %s | Min Cool Temp: %s', self._DaikinClimateInfo_Object.MaxCoolTemp,self._DaikinClimateInfo_Object.MinCoolTemp)
        _LOGGER.debug('Max Heat Temp: %s | Min Heat Temp: %s', self._DaikinClimateInfo_Object.MaxHeatTemp,self._DaikinClimateInfo_Object.MinHeatTemp)

        
#ProcessControlInfo
#Function processes the 'ControlInfo' from received from the SkyZone unit.
#This should only be a 'positive response' from SkyZone.
#C_PCD_ControlInfo = 0xB0
def ProcessControlInfo(self, incomingInfo):
    pass
    #nothing to process
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('0xB0 (ControlInfo Accepted)')

#ProcessControlInfo
#Function processes the 'InternalAcMode' request from received from the SkyZone unit.
#This should only be a 'positive response' from SkyZone.        
#C_PCD_InternalAcMode = 0xB2        # Control Normal/Service mode
def ProcessInternalAcMode(self, incomingInfo):
    pass
    #nothing to process
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('0xB2 (InternalAcMode Accepted)')


#ProcessSelectSensor
#Function processes the 'SelectSensor' request from received from the SkyZone unit.
#This should only be a 'positive response' from SkyZone.
#C_PCD_SelectSensor = 0xB3            # Set selected temp sensor
def ProcessSelectSensor(self, incomingInfo):
    pass
    #nothing to process
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('0xB3 (SelectSensor Accepted)')


#ProcessGetLocalSetting
#Function processes the 'GetLocalSetting' request from received from the SkyZone unit.
#C_PCD_GetLocalSetting = 0xC0        # Get 'service' info
def ProcessGetLocalSetting(self, incomingInfo):

    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('0xC0 (GetLocalSetting Accepted)')
    #if(self._DebugModeLevel >= 3):
        #for e in incomingInfo : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )

    #Get temp sensor info mask
    if(incomingInfo[1] == 0x41):
        if(incomingInfo[2] == 2):
            self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Refrigerant] = incomingInfo[4]
            if(self._DebugModeLevel >= 1):
                _LOGGER.debug('Refrig Sensor: %s', self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Refrigerant] )
        elif(incomingInfo[2] == 0):
            self._DaikinClimateSettings_Object.TempSensorValues[self._DaikinClimateSettings_Object.SelectedSensor] = incomingInfo[4]
            if(self._DebugModeLevel >= 1):
                _LOGGER.debug('Set Sensor (%s,):  %s' , self._DaikinClimateSettings_Object.SelectedSensor , self._DaikinClimateSettings_Object.TempSensorValues[self._DaikinClimateSettings_Object.SelectedSensor] )
        else:
            self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Internal] = incomingInfo[4]
            if(self._DebugModeLevel >= 1):
                _LOGGER.debug('Internal Sensor: %s', self._DaikinClimateSettings_Object.TempSensorValues[SensorIndex.Internal] )

                
#ProcessSetLocalSetting
#Function processes the 'SetLocalSetting' request from received from the SkyZone unit.
#This should only be a 'positive response' from SkyZone.
#C_PCD_SetLocalSetting = 0xC3        # Set 'service' settings         
def ProcessSetLocalSetting(self, incomingInfo):
    pass
    #nothing to process
    if(self._DebugModeLevel >= 1):
        _LOGGER.debug('0xC3 (SetLocalSetting Accepted)')

#ProcessGetZoneNames
#Function processes the 'GetZoneNames' request from received from the SkyZone unit.
#C_PCD_GetZoneNames = 0xD0        # Get zone names
def ProcessGetZoneNames(self, incomingInfo):

    #Convert byteArray to string of characters
    IncomingString = ''.join(chr(x) for x in incomingInfo)

    #delimit by ', '
    DelimList = re.split(',', IncomingString) #,",")
    if(self._DebugModeLevel >= 2):
        _LOGGER.debug(DelimList)
    
    #Check delim list for key items

    i =0
    while i< len(DelimList):
        #zone names           
        if DelimList[i].startswith('z'+str(i+1)): self._DaikinClimateInfo_Object.ZoneName[i] = DelimList[i][3:len(DelimList[i])].rstrip('\x00 ')
        i= i+1

    if(self._DebugModeLevel >= 2):
        _LOGGER.debug('Zone Names: %s | %s | %s| %s| %s| %s| %s| %s', self._DaikinClimateInfo_Object.ZoneName[0],self._DaikinClimateInfo_Object.ZoneName[1], self._DaikinClimateInfo_Object.ZoneName[2],self._DaikinClimateInfo_Object.ZoneName[3],self._DaikinClimateInfo_Object.ZoneName[4],self._DaikinClimateInfo_Object.ZoneName[5], self._DaikinClimateInfo_Object.ZoneName[6], self._DaikinClimateInfo_Object.ZoneName[7])

#ProcessGetSensorNames
#Function processes the 'GetSensorNames' request from received from the SkyZone unit.
#C_PCD_GetSensorNames = 0xD2    # Get sensor names        
def ProcessGetSensorNames(self, incomingInfo):
    #Convert byteArray to string of characters
    IncomingString = ''.join(chr(x) for x in incomingInfo)

    #delimit by ', '
    DelimList = re.split(',', IncomingString) #,",")
    if(self._DebugModeLevel  >= 2):
        _LOGGER.debug(DelimList)
    
    #Check delim list for key items

    i =0
    while i< len(DelimList):
        if(self._DebugModeLevel >= 2):
            _LOGGER.debug(DelimList[i])
        #sensor names           
        if DelimList[i].startswith('s'+str(i+1)): self._DaikinClimateInfo_Object.TempSensorName[i]  = DelimList[i][3:len(DelimList[i])].rstrip('\x00 ')
        i= i+1
        
    if(self._DebugModeLevel  >= 2):
        _LOGGER.debug('Sensor Names: %s | %s | %s | %s' ,self._DaikinClimateInfo_Object.TempSensorName[0], self._DaikinClimateInfo_Object.TempSensorName[1], self._DaikinClimateInfo_Object.TempSensorName[2], self._DaikinClimateInfo_Object.TempSensorName[3], self._DaikinClimateInfo_Object.TempSensorName[4])
        
#C_DaikinIncomingResonse
#Defines the function pointer (function dictionary) making processing incoming frames really easy.
#Commented out items are not supported
C_DaikinIncomingResonse = { 0xA0 : ProcessBasicInfo,
                            0xA1 : ProcessInitialInfo,
                            0xB0 : ProcessControlInfo,
                            #0xB1 : ProcessOnOffTimer,
                            0xB2 : ProcessInternalAcMode,
                            0xB3 : ProcessSelectSensor,
                            #0xB4 : ProcessClearFilter,
                            #0xB5 : ProcessClock,
                            #0xB6 : ProcessSet7DaysCounter,
                            #0xBD : ProcessClearErrorCode,
                            #0xBE : ProcessSetAirFlow,
                            0xC0 : ProcessGetLocalSetting,
                            #0xC1 : ProcessGet7DaysTimer,
                            #0xC2 : ProcessGetAirFlow,
                            0xC3 : ProcessSetLocalSetting,
                            0xD0 : ProcessGetZoneNames,
                            #0xD1 : ProcessEnergySaving,
                            0xD2 : ProcessGetSensorNames
                            #0xD3 : ProcessDealerContact,
                            #0xD5 : ProcessSYUInfo
}


#IsTempWithinHeatRange
#Quick check if requested temp is within the range defined by the AC.
def IsTempWithinHeatRange(self, SetTemp):
    if((SetTemp >= self._DaikinClimateInfo_Object.MinHeatTemp) and (SetTemp <= self._DaikinClimateInfo_Object.MaxHeatTemp) ): return 1
    else: return 0
    
    
#IsTempWithinCoolRange
#Quick check if requested temp is within the range defined by the AC.
def IsTempWithinCoolRange(self, SetTemp):
    if((SetTemp >= self._DaikinClimateInfo_Object.MinCoolTemp) and (SetTemp <= self._DaikinClimateInfo_Object.MaxCoolTemp) ): return 1
    else: return 0

#IsUnitDataPresent
#Check to see if serial number shave been received, i.e. handshake between PyZone and Skyzone is functional.
def IsUnitDataPresent(self):
    if((self._DaikinClimateInfo_Object.IndoorUnitPartNumber == 'Unknown') or (self._DaikinClimateInfo_Object.OutdoorUnitPartNumber == 'Unkown')): return 0
    else: return 1
    
#RetrievePowerState
#Function is used to return the current PowerOn State of PiZone - class AcPowerState
def RetrievePowerState(self):
    return self._DaikinClimateSettings_Object.PowerOnState

#UpdatePowerState
#Function is used to alter the current PowerOn state of PiZone - class AcPowerState
#Note: Once updated, SyncControInfo frame needs to be sent to SkyZone, otherwise value will be lost next poll to SkyZone (BasicInfo).
def UpdatePowerState(self, AcPowerState):
    #whilst lockout is present delay for 5s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
        
    self._DaikinClimateSettings_Object.PowerOnState = AcPowerState

#GetClimateMode
#Function is used to return the current Climate mode of PiZone - class AcStateMode
def GetClimateMode(self):
    if(RetrievePowerState(self) != AcPowerState.ON):
        return AcStateMode.MODE_OFF
    else:
        return self._DaikinClimateSettings_Object.AcStateModeValue

#SetClimateMode
#Function is used to alter the current Climate mode state of PiZone - class AcStateMode
#Note: Once updated, SyncControInfo frame needs to be sent to SkyZone, otherwise value will be lost next poll to SkyZone (BasicInfo).
def SetClimateMode(self, SetAcMode):
    #whilst lockout is present delay for 5s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
    
    if(SetAcMode == AcStateMode.MODE_OFF):
        #Turn off unit
        if(self._DebugModeLevel >= 1):
            _LOGGER.debug('TurnOff AC')
        UpdatePowerState(self, AcPowerState.OFF)
        #leave AcStateModeValue as previous
    else:
        #turn on unit and set mode
        UpdatePowerState(self, AcPowerState.ON)
        self._DaikinClimateSettings_Object.AcStateModeValue = SetAcMode

#GetTargetClimateTemp
#Function is used to return the current Target temperature for the current climate mode.
def GetTargetClimateTemp(self):
    #get current selected mode from AC and select corresponding set temp.
    #heat
     if(GetClimateMode(self) == AcStateMode.MODE_HEAT):
        return self._DaikinClimateSettings_Object.HeatSetTemp
     #fan/off - report no temp
     elif((GetClimateMode(self) == AcStateMode.MODE_FAN) or (GetClimateMode(self) == AcStateMode.MODE_OFF)):
        return None
     #cool
     else:
        return self._DaikinClimateSettings_Object.CoolSetTemp

#SetTargetClimateTemp
#Function is used to alter the current Target temperature for the current mode  of PiZone 
#Note: Once updated, SyncControInfo frame needs to be sent to SkyZone, otherwise value will be lost next poll to SkyZone (BasicInfo).
def SetTargetClimateTemp(self, SetTemp):
    #whilst lockout is present delay for 5s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
    
    #HEAT
    if(GetClimateMode(self)  == AcStateMode.MODE_HEAT):
        #check temp is with heating range.
        if(IsTempWithinHeatRange(self, SetTemp)):
            #update 'heat' variables
            self._DaikinClimateSettings_Object.HeatSetTemp = SetTemp;
    #COOL
    elif(GetClimateMode(self)  == AcStateMode.MODE_COOL):
        #check temp is within cooling range
         if(IsTempWithinCoolRange(self, SetTemp)):
            #update 'cool' variables
            self._DaikinClimateSettings_Object.CoolSetTemp = SetTemp;
    #AUTO
    elif(GetClimateMode(self)  == AcStateMode.MODE_AUTO):
        #check temp is within heat/cool range.
        if(IsTempWithinCoolRange(self, SetTemp) and IsTempWithinHeatRange(self, SetTemp)):
            #update both
            self._DaikinClimateSettings_Object.HeatSetTemp = SetTemp;
            self._DaikinClimateSettings_Object.CoolSetTemp = SetTemp;
    #DRY/FAN/OFF
    else:
        #Temp setting ignored.
        pass

#GetClimateTempSensor
#Function is used to return the current Climate temp sensor of PiZone - class SensorIndex
def GetClimateTempSensor(self):
    return self._DaikinClimateSettings_Object.SelectedSensor

#GetClimateSensorName
#Function is used to get sensor name as given by Daikin Skyzone
def GetClimateSensorName(self, SelectedSensor):
    if isinstance(SelectedSensor, SensorIndex):
        return self._DaikinClimateInfo_Object.TempSensorName[SelectedSensor]

 #GetClimateSensorState
 #Function is used to indicate if a given SensorIndex is currently set as the SelectedSensor
def GetClimateSensorState(self, SelectedSensor):
    if isinstance(SelectedSensor, SensorIndex):
        #return true if selectedSensor is the current sensor. Otherwise return false.
        if(self._DaikinClimateSettings_Object.SelectedSensor == SelectedSensor):
            return True
        else:
            return False

#GetClimateSensorValue
#Function is used to get the temperature of a given SensorIndex.
def GetClimateSensorValue(self, SelectedSensor):
    if isinstance(SelectedSensor, SensorIndex):
    
        #if selected sensor is either ExternalSensor AND it's not the current sensor AND PiZone isnt polling for the value, return None
        if( ((SelectedSensor == SensorIndex.Sensor1) or (SelectedSensor == SensorIndex.Sensor2)) and (self._DaikinClimateSettings_Object.SelectedSensor != SelectedSensor) and (self._PollExternalSensors == 0)):
            return None
        else:
            SensorValue = self._DaikinClimateSettings_Object.TempSensorValues[SelectedSensor]
            #dont report sensor value if it's value hasnt been received yet
            if(SensorValue != 255):
                return SensorValue
            else:
                return None

#GetClimateExternalSensorCount
#Fucntion returns the number of configured external sensors on the Daikin Unit
def GetClimateExternalSensorCount(self):
    # NumberOfSensors is for 'selectable' for unit so will be 1,2 or 3 
    # Thus, External sensors are value - 1 for the always present internal sensor
    return (self._DaikinClimateInfo_Object.NumberOfSensors - 1)

#GetClimateCurrentTempValue
#Function is used to return the current temp value of PiZone
def GetClimateCurrentTempValue(self):
    #Check which is the select temp sensor and return value
    if(self._DaikinClimateSettings_Object.SelectedSensor == SensorIndex.Internal):
        return self._DaikinClimateSettings_Object.TempSensorValues.Internal
    elif(self._DaikinClimateSettings_Object.SelectedSensor == SensorIndex.Sensor1):
        return self._DaikinClimateSettings_Object.TempSensorValues.Sensor1
    else:
        #Sensor2
        return self._DaikinClimateSettings_Object.TempSensorValues.Sensor2

#SetClimateTempSensor
#Function is used to alter the current climate temp sensor of PiZone 
#Note: Once updated, SetAcTempReadSensor frame needs to be sent to SkyZone, otherwise value will be lost next poll to SkyZone (BasicInfo)
def SetClimateTempSensor(self, SetSensorIndex):
    if isinstance(SetSensorIndex, SensorIndex):  
        #whilst lockout is present delay for 5s and check again
        while((self._SyncLockout == 1) or (self._SyncClimateInfoLockout == 1)):
            time.sleep(1)
        
        #limit value to Sensor2, as Outdoor/Refrigerant are not part of frame and only used for internal indexing of temperatures.
        if(SetSensorIndex <= SensorIndex.Sensor2):
            self._DaikinClimateSettings_Object.SelectedSensor = SetSensorIndex  

#GetClimateFanSpeed
#Function is used to return the current fan speed for the current mode of PiZone - class FanSpeed
def GetClimateFanSpeed(self):
    #get current selected mode from AC and select corresponding set temp.
    #off
    if(GetClimateMode(self) == AcStateMode.MODE_OFF):
        return FanSpeed.NA
    #heat
    if(GetClimateMode(self) == AcStateMode.MODE_HEAT):
        return self._DaikinClimateSettings_Object.HeatFanState.FanSpeed
    #dry
    if(GetClimateMode(self)  == AcStateMode.MODE_DRY):
        #always set to low.
        return FanSpeed.LOW
    #cool/fan/auto
    else:
        return self._DaikinClimateSettings_Object.CoolFanState.FanSpeed

#SetSelectedFanSpeed
#Function is used to alter the current fan speed  for the current mode of PiZone 
#Note: Once updated, SyncControInfo frame needs to be sent to SkyZone, otherwise value will be lost next poll to SkyZone (BasicInfo).
def SetSelectedFanSpeed(self, SetFanSpeed):
    #whilst lockout is present delay for 5s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
    
    #check FanSpeed is valid
    if (isinstance(SetFanSpeed, FanSpeed) and (SetFanSpeed != FanSpeed.NA)):
    #check for current mode (cool/heat). Default (0) is FAN, so no need to check for 'init' value.
        #check FanMode based on FanSpeed
        if((SetFanSpeed == FanSpeed.LOW) or (SetFanSpeed == FanSpeed.MED) or (SetFanSpeed == FanSpeed.HIGH) ):
            SetFanMode =FanMode.FAN
        elif((SetFanSpeed == FanSpeed.AUTO_LOW) or (SetFanSpeed == FanSpeed.AUTO_MED) or ( SetFanSpeed == FanSpeed.AUTO_HIGH) ):
            SetFanMode =FanMode.AUTO
        else:
            SetFanMode = FanMode.MULTI_ZONING
            
        #HEAT
        if(GetClimateMode(self)  == AcStateMode.MODE_HEAT):
            #update 'heat' variables
            self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = SetFanSpeed;
            self._DaikinClimateSettings_Object.HeatFanState.FanMode = SetFanMode;
        #COOL
        elif(GetClimateMode(self)  == AcStateMode.MODE_COOL):
            #update 'cool' variables
            self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = SetFanSpeed;
            self._DaikinClimateSettings_Object.CoolFanState.FanMode = SetFanMode;
        #FAN
        elif (GetClimateMode(self)  == AcStateMode.MODE_FAN):
            #update 'cool' variables
            self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = SetFanSpeed;
            self._DaikinClimateSettings_Object.CoolFanState.FanMode = SetFanMode;
        #AUTO/FAN
        elif(GetClimateMode(self)  == AcStateMode.MODE_AUTO) :
            #update both (as per app)
            self._DaikinClimateSettings_Object.CoolFanState.FanSpeed = SetFanSpeed;
            self._DaikinClimateSettings_Object.CoolFanState.FanMode = SetFanMode;
            self._DaikinClimateSettings_Object.HeatFanState.FanSpeed = SetFanSpeed;
            self._DaikinClimateSettings_Object.HeatFanState.FanMode = SetFanMode;
        #DRY/OFF
        else:
            #Speed/Fan settings ignored.
            pass

#GetClimateZoneState
#Function returns True if the zoneIndex is currently Active
def GetClimateZoneState(self, zoneIndex):
    return (self._DaikinClimateSettings_Object.Zone[zoneIndex] == ZoneState.ACTIVE)
#GetClimateNumberOfZones
#Function is used to return the number of configured zones on the Daikin Unit
def GetClimateNumberOfZones(self):
    return self._DaikinClimateInfo_Object.NumberOfZones

#GetClimateZoneName
#Function is used to get the name of the zone as given from the Daikin Unit
def GetClimateZoneName (self, zoneIndex):
    return self._DaikinClimateInfo_Object.ZoneName[zoneIndex]

 #UpdateZoneState
# Function updates the zone 
def UpdateZoneState(self, zoneIndex, zoneSetting):
    #whilst lockout is present delay for 5s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
        
    #check each bit and set corresponding zone. Check for 'max' zones supported
    if (isinstance(zoneSetting, ZoneState)):
        if(zoneIndex < self._DaikinClimateInfo_Object.NumberOfZones):
            self._DaikinClimateSettings_Object.Zone[zoneIndex] = zoneSetting 
            
    #check to make sure all zones are not switched off
    anyZoneActive = False
    for x in range (0, self._DaikinClimateInfo_Object.NumberOfZones):
        if (self._DaikinClimateSettings_Object.Zone[x] == ZoneState.ACTIVE):
            anyZoneActive = True
       
    if(anyZoneActive == False):
        _LOGGER.error('No Zone selected. This may cause permanent damage to your AC system!')

#SetClimateZoneActive/SetClimateZoneInactive
#Functions are used to set a zone (zoneIndex) to Active/Inactive
def SetClimateZoneActive(self, zoneIndex): UpdateZoneState(self, zoneIndex, ZoneState.ACTIVE)
def SetClimateZoneInactive(self, zoneIndex): UpdateZoneState(self, zoneIndex, ZoneState.INACTIVE)

#Other Functions
def GetIndoorPartNumber(self):          return self._DaikinClimateInfo_Object.IndoorUnitPartNumber
def GetOutdoorPartNumber(self):         return self._DaikinClimateInfo_Object.OutdoorUnitPartNumber
def GetClimateErrorCodes(self):         return self._DaikinClimateInfo_Object.ErrorCodes
def GetClimateHistoryErrorCodes(self):  return self._DaikinClimateInfo_Object.HistoryErrorCodes
def GetClimateClearFilterFlag(self):    return self._DaikinClimateInfo_Object.ClearFilter
def GetClimiateMinSupportedTemp(self):  return min(self._DaikinClimateInfo_Object.MinCoolTemp, self._DaikinClimateInfo_Object.MinHeatTemp) 
def GetClimiateMaxSupportedTemp(self):  return max(self._DaikinClimateInfo_Object.MaxCoolTemp, self._DaikinClimateInfo_Object.MaxHeatTemp)

#UpdateTempSensorDataProcess
#Function to cycle though the internal and refrigerant temp sensors..
def UpdateTempSensorDataProcess(self):
    #update using 'service' mode (prevent changing AC unit 'guide' temp)
    #whilst lockout is present delay for 1s and check again
    while(self._SyncLockout == 1):
        time.sleep(1)
   
    #Enter service mode (b2)
    self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.SERVICE
    SendReceiveFrame(self,"SetInternalAcMode")
    
    #now cycle through all Internal and Refrigerant sensors (CurrentSelected is updated via BasicInfo request)
    
   #Refrigerant
    self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT

    #poll unit switch and wait for 1.5 to get updated temp value.
    for x in range (0, C_DaikinDelay_ServiceModeInfoUpdate):
        SendReceiveFrame(self, "GetServiceRequestData")
        time.sleep(C_DaikinDelay_ServiceRequest)

    #check CurrentSelected is not Internal.
    if(self._DaikinClimateSettings_Object.SelectedSensor != SensorIndex.Internal):
        #internal
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.INTERNAL

        #poll unit switch and wait for 1.5 to get updated temp value.
        SendReceiveFrame(self,"GetServiceRequestData")
         
        #set service back to internal mode for next call 
        #Refrig
        time.sleep(C_DaikinDelay_ServiceRequest)
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT
        SendReceiveFrame(self,"GetServiceRequestData")
        
    #Exit service mode
    self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.NORMAL
    SendReceiveFrame(self, "SetInternalAcMode")

#UpdateTempSensorDataProcess
#Function to cycle though the external temp sensors.
#Function should not be used if either sensor can have wildly different values.
#Even though the sensor is selected for a brief time, the Daikin AC unit will 'keep' the value for ~3mins before releasing it.
#This means if you have warm and cool 'zone', the unit will constantly start/stop whenever the logic is run.
#Not recommended  to be used unless you 'alter' the target temp to keep the unit functional across all zones.
def UpdateExternalTempSensorDataProcess(self):
    #Lockout SynchClimateInfo whilst checking temp sensors.
    self._SyncClimateInfoLockout = 1

    #Store CurrentSensor incase external temp sensors are fitted to AC.
    CurrentSensor = self._DaikinClimateSettings_Object.SelectedSensor
      
    #update 'external sensors'
    #only method is to change selected sensor and wait for updated temp.
    #side affect is that if other external sensor is higher/lower than current heating/cooling temp, AC unit may switch modes briefly whilst the sensors are switched
    #full process takes ~20s to switch.
    if((self._PollExternalSensors == 1) and (self._DaikinClimateInfo_Object.NumberOfSensors >1) ):        
    
        #Enter service mode (b2) and set read to CurrentSetting (room temp sensors)
        self._DaikinClimateSettings_Object.InternalAcMode = InternalAcMode.SERVICE
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.CURRENTSETTING
        SendReceiveFrame(self,"SetInternalAcMode")
        SendReceiveFrame(self, "GetServiceRequestData")

        #check for sensor 1 (ext1) and 2 (ext2)
        for x in range (1, self._DaikinClimateInfo_Object.NumberOfSensors):
        
            #skip 'CurrentSensor if PowerisOn, otherwise read as during PowerOff, CurrentTemp value isn't updated.
            if( (x == 1) and ( (CurrentSensor != SensorIndex.Sensor1) or (self._DaikinClimateSettings_Object.PowerOnState != AcPowerState.ON)) ):
                if(self._DebugModeLevel >= 1):
                    _LOGGER.debug('Sensor to int. Sensor1: %s', SensorIndex.Sensor1)   
                self._DaikinClimateSettings_Object.SelectedSensor = SensorIndex.Sensor1
                SendReceiveFrame(self, "SetAcTempReadSensor")
                time.sleep(C_DaikinDelay_TempSensorChange)
                
                #poll unit switch and wait for 1.5 to get updated temp value.
                for x in range (0, C_DaikinDelay_ServiceModeInfoUpdate):
                    SendReceiveFrame(self, "GetServiceRequestData")
                    time.sleep(C_DaikinDelay_ServiceRequest)
                
            if( (x == 2) and ( (CurrentSensor != SensorIndex.Sensor2) or (self._DaikinClimateSettings_Object.PowerOnState != AcPowerState.ON)) ):
                if(self._DebugModeLevel >= 1):
                    _LOGGER.debug('Sensor to int. Sensor2: %s', SensorIndex.Sensor2) 
                self._DaikinClimateSettings_Object.SelectedSensor = SensorIndex.Sensor2
                SendReceiveFrame(self, "SetAcTempReadSensor")
                time.sleep(C_DaikinDelay_TempSensorChange)
                
                #poll unit switch and wait for 1.5 to get updated temp value.
                for x in range (0, C_DaikinDelay_ServiceModeInfoUpdate):
                    SendReceiveFrame(self, "GetServiceRequestData")
                    time.sleep(C_DaikinDelay_ServiceRequest)
                    
        #reset back to refrig for other sensor read
        self._DaikinClimateSettings_Object.ServiceModeSensor = SensorSelect.REFRIGERANT
        #set sensor back to original value if External sensors present
        while(self._DaikinClimateSettings_Object.SelectedSensor != CurrentSensor):
            _LOGGER.debug('Reset sensor back to: %s', CurrentSensor)   
            self._DaikinClimateSettings_Object.SelectedSensor = CurrentSensor
            SendReceiveFrame(self, "SetAcTempReadSensor")
            time.sleep(C_DaikinDelay_TempSensorChange)
            SendReceiveFrame(self, "BasicInfoServiceMode")
            
    #release lock
    self._SyncClimateInfoLockout = 0

#Interfaces used to generate frames to get/set SkyZone unit via network interface 
def CreateIntialInfoFrame(self):
   return CreateRequestFrame(self, C_REQUEST_GETUP,C_PCD_InitialInfo)
    
def CreateBasicInfoFrame(self):
    return CreateRequestFrame(self, C_REQUEST_GETUP,C_PCD_BasicInfo)   
    
def CreateSyncControInfoFrame(self):
    return CreateRequestFrame(self, C_REQUEST_SET,C_PCD_ControlInfo)
    
def CreateGetServiceRequestDataFrame(self):
    return CreateRequestFrame(self, C_REQUEST_GET,C_PCD_GetLocalSetting)
    
def CreateSetInternalAcModeFrame(self):
    return CreateRequestFrame(self, C_REQUEST_SET,C_PCD_InternalAcMode)
    
def CreateSetAcTempReadSensorFrame(self):
    return CreateRequestFrame(self, C_REQUEST_SET,C_PCD_SelectSensor)
    
def CreateGetZoneNamesFrame(self):
    return CreateRequestFrame(self, C_REQUEST_GETUP,C_PCD_GetZoneNames)
    
def CreateGetSensorZoneNamesFrame(self):
    return CreateRequestFrame(self, C_REQUEST_GETUP,C_PCD_GetSensorNames)

    
C_DaikinRequest = { 'InitialInfo' : CreateIntialInfoFrame,
                           'BasicInfo' : CreateBasicInfoFrame,
                           'BasicInfoServiceMode' : CreateBasicInfoFrame,
                           'SyncControInfo' : CreateSyncControInfoFrame,
                           'GetServiceRequestData' : CreateGetServiceRequestDataFrame,
                           'SetInternalAcMode' : CreateSetInternalAcModeFrame,
                           'SetAcTempReadSensor' : CreateSetAcTempReadSensorFrame,
                           'GetZoneNames' : CreateGetZoneNamesFrame,
                           'GetSensorZoneNames' : CreateGetSensorZoneNamesFrame
}

#SendReceiveFrame
#Function to send frame onto Network and wait for response from SkyZone.
def SendReceiveFrame(self, FrameIndex):
    #perform TCP SYN
    TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPsocket.settimeout(5.0)
    PORT = 80
    if(self._IpAdd!='0.0.0.0'):
        try:
            TCPsocket.connect((self._IpAdd, PORT))
            
            #Get initial info to create instance.
            conn = http.client.HTTPConnection(self._IpAdd, PORT)
            #Generate Init request and prcoess response
            #lock out basic info
            if( (FrameIndex == "BasicInfo") and (self._SyncClimateInfoLockout == 1) ):
                #skip generating frame as lockout is in progress
                pass
            else:
                RequestFrame = C_DaikinRequest[FrameIndex](self);
                conn.request("GET", "/node/object?frame={}".format(RequestFrame))
                resp = conn.getresponse()
                data = resp.read().decode()
                conn.close()
                TCPsocket.close()
                ProcessReceivedPacket(self,data)
            
        except OSError as e:
            _LOGGER.error("Could not send TCP Request: %s", e )
            TCPsocket.close()

#ProcessReceivedPacket        
#Function to process incoming response from SkyZone.
def ProcessReceivedPacket(self, incomingPacket):
    #trim start, parse to decoder
    if(incomingPacket[0:13] == 'ret=OK,frame='): DecodeFrame(self, incomingPacket[13: len(incomingPacket)] )
    else: 
        if(self._DebugModeLevel >= 1):
            _LOGGER.debug('Error: %s', incomingPacket[0:13])

#DecodeFrame
# Function decodes incoming string from SkyZone and calls required sub-service to process information returned.            
def DecodeFrame(self, incomingString):

    IncomingInfo = bytearray()
    #get frame=xxx values
    decodedMsg = base64.b64decode(incomingString)
    
    if(decodedMsg[4]!=0):
        #Pw not corret
        _LOGGER.error('Password is not correct. Please check and re-enter!')
        self._IpAdd = '0.0.0.0'
        return
    elif len(decodedMsg) == 17 :
        #set request response level message
        IncomingInfo = decodedMsg
    else:
        #get request response level message
        #read byte 14 to get response info
        infosize = int(decodedMsg[14])
        # add response code for case selection.
        IncomingInfo.append(decodedMsg[13])
        if infosize > 0 :
            for d in decodedMsg[15:(15+infosize)]: IncomingInfo.append(d)
     
    if(self._DebugModeLevel >= 3):
        _LOGGER.debug('Incoming Type  : %s', (decodedMsg[13]))
        #for e in IncomingInfo : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )
    
    ProcessingIncomingGetResponse(self, IncomingInfo)

    return IncomingInfo

#ProcessingIncomingGetResponse
#Determines which AC frame has been transmitted and calls according function to process information. Unused/invalid frames are ignored.
def ProcessingIncomingGetResponse(self, IncomingInfo):
    
    if(IncomingInfo[0] in C_DaikinIncomingResonse) : C_DaikinIncomingResonse[IncomingInfo[0]](self, IncomingInfo[1:len(IncomingInfo)])
    elif len(IncomingInfo) == 17 :
        #Confirmation response from unit
        if(IncomingInfo[13] in C_DaikinIncomingResonse) : C_DaikinIncomingResonse[IncomingInfo[13]](self, IncomingInfo)
        #for e in IncomingInfo : _LOGGER.debug("%5x"%e," / " ,e, " / ", chr(int(e)) )
    # else:
        if(self._DebugModeLevel >= 3):
            _LOGGER.debug('Not Supported: %s', "%5x"%IncomingInfo[0] )
    return        
                    