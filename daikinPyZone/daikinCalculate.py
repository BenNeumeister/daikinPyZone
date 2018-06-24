import base64

from daikinPyZone.daikinConstants import *
from daikinPyZone.daikinClasses import( ResolveFanSpeedForDataFrame, ResolveSensorNameToIndex, GetZoneBitMaskFromZoneState)

#CalcPasswordHiByte          
#Function calculates the high byte based on the local PIN/Password          
def CalcPasswordHiByte(password):
    return ( (int(int(password)/1000) << 4) + int((int(password)% 1000) / 100) )


#CalcPasswordLowByte
#Function calculates the Low byte based on the local PIN/Password          
def CalcPasswordLowByte(password):
    return ( (int((int(password)%100)/10)<< 4) + (int(password)% 10)  )


#CalculateDaikinChecksum
# Function calculates the checksum for the frame
def CalculateDaikinChecksum ( Headerbytes, Databtyes):

    # Add all values in Header/Data bytes. Checksum= total /256& 0xFF and total & 0xFF
    #Note: Android app doesn't appear to do checksum verification. Assuming SkyZone controller does.
    dataA = bytes(Headerbytes)
    dataB = bytes(Databtyes)
    byteSum = 0;
    
    for d in dataA : byteSum += d;
    for e in dataB : byteSum += e;
    
    Checksum = C_DaikinChecksum
    Checksum[0] = int((byteSum)/256) & 0xFF
    Checksum[1] = (byteSum) & 0xFF
    
    return Checksum
    
#AssembleTransmissionFrame
# Function assembles the frame for transmission, merging together the header, data and checksum bytes
def AssembleTransmissionFrame ( HeaderBytes, DataBtyes, ChecksumBytes):

    #Ensure all items are in byte format
    dataA = bytearray(HeaderBytes)
    dataB = bytearray(DataBtyes)
    dataC = bytearray(ChecksumBytes)

    AssembledArray = dataA
    for a in dataB : AssembledArray.append(a)
    for b in dataC : AssembledArray.append(b)
    
    #encode into base64
    encoded = base64.b64encode(AssembledArray)
    return encoded
    
 #  CreateDataRequestDataFrame
 # Function creates a DataRequest array from the template and inserts PCD type.
def CreateDataRequestDataFrame(PCD):
    Data = C_DaikinDataRequest
    Data[5] = PCD
    return Data

#CreateAcStateDataFrame
#  Function creates a set AcState Data array from the template and inserts current settings from PiZone instance for tranmissions
def CreateAcStateDataFrame(self):
    Data = C_DaikinDataAcState

    Data[7] = self._DaikinClimateSettings_Object.AcStateModeValue + (self._DaikinClimateSettings_Object.PowerOnState << 3)
    Data[8] = self._DaikinClimateSettings_Object.CoolSetTemp
    Data[10]  = self._DaikinClimateSettings_Object.HeatSetTemp 
    Data[12] = ( (self._DaikinClimateSettings_Object.CoolFanState.FanMode.value) << 4)  + (ResolveFanSpeedForDataFrame(self._DaikinClimateSettings_Object.CoolFanState.FanSpeed) & 0x0F)
    Data[13] = ( (self._DaikinClimateSettings_Object.HeatFanState.FanMode) << 4)  + (ResolveFanSpeedForDataFrame(self._DaikinClimateSettings_Object.HeatFanState.FanSpeed) & 0x0F)
    Data[14] = GetZoneBitMaskFromZoneState(self)
    
    return Data

#CreateInternalAcModeDataFrame
#  Function creates a set AcMode Data array from the template and inserts the mode PiZone wants to switch to
def CreateInternalAcModeDataFrame(self):
    Data = C_DaikinDataInternalMode
    Data[7] = self._DaikinClimateSettings_Object.InternalAcMode.value
    return Data

#CreateLocalSettingDataFrame
#  Function creates a set LocalSettings Data array from the template and inserts the Sensor PiZone wants to switch to
def CreateLocalSettingDataFrame(self):
    Data = C_DaikinDataControlInfoTemp
    Data[8] = self._DaikinClimateSettings_Object.ServiceModeSensor .value
    return Data

#CreateSensorSetDataFrame
# Function creates a set Sensor Data array from the template and inserts the Sensor PiZone wants to switch to
def CreateSensorSetDataFrame(self):
    Data = C_DaikinDataSensorSelect
    Data[7] = ResolveSensorNameToIndex(self, self._DaikinClimateInfo_Object.TempSensorName[self._DaikinClimateSettings_Object.SelectedSensor])
    return Data
    
#CreateRequestFrame
#  Function creates the request frame based on given parameters
def CreateRequestFrame (self,  RequestType, PCD):
    Header = C_DaikinHeader
    Header[3] = RequestType
    #Only populate password if set. Otherwise default (0xFF, 0xFF) is ok.
    if(self._Pwd != 0000):
        Header[5] = CalcPasswordHiByte(self._Pwd)
        Header[6] = CalcPasswordLowByte(self._Pwd)
        
    #0xA0 - Get all info from unit
    if(PCD == C_PCD_BasicInfo):
        Data = CreateDataRequestDataFrame(C_PCD_BasicInfo)
    #0xA1 - Get unit type and limits
    elif(PCD == C_PCD_InitialInfo):
        Data = CreateDataRequestDataFrame(C_PCD_InitialInfo)
    #0xB0 -  Get service info data
    elif(PCD == C_PCD_ControlInfo):
        Data = CreateAcStateDataFrame(self)
    #0xB2 -  Set InternalAcMode
    elif(PCD == C_PCD_InternalAcMode):
        Data = CreateInternalAcModeDataFrame(self)
    #0xB3 - Set ref sensor
    elif(PCD == C_PCD_SelectSensor):
        Data = CreateSensorSetDataFrame(self)
    #0xC0 - Request service mode
    elif(PCD == C_PCD_GetLocalSetting):
        Data = CreateLocalSettingDataFrame(self)
    #0xD0 - Request zone names
    elif(PCD == C_PCD_GetZoneNames):
        Data = CreateDataRequestDataFrame(C_PCD_GetZoneNames)
    #0xD2 - Get sensor names
    elif(PCD == C_PCD_GetSensorNames):
        Data = CreateDataRequestDataFrame(C_PCD_GetSensorNames)
    else:
        pass
        # if(self._DebugModeLevel >= 1):
            # print('Not supported')
            
    # if(self._DebugModeLevel >= 4):
        # for e in Data : print ("%5x"%e," / " ,e, " / ", chr(int(e)) )
            
    Checksm = CalculateDaikinChecksum(Header, Data)

    Frame = AssembleTransmissionFrame(Header, Data, Checksm)
    
    return Frame.decode('UTF-8')