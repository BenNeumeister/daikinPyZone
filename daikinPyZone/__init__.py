#Library to handle connection with Daikin Skyzone
import requests
import socket
import logging
from daikinPyZone.daikinProcess import *

_LOGGER = logging.getLogger(__name__)

class DaikinSkyZone(object):

    BROADCAST_ADDRESS = '255.255.255.255'
    #Target UDP port for Daikin SkyZone
    BROADCAST_PORT = 30050
    SOCKET_BUFSIZE = 1024

    def __init__(self, name = 'Daikin Skyzone', ipAddress = '0.0.0.0', debugLvl = 0, pollExtSns = 0):
        #create info structs for Info and Settings classes.
        self._DaikinClimateInfo_Object = DaikinClimateInformation()
        self._DaikinClimateSettings_Object = DaikinClimateSettings()
        
        #set name
        self._name = name
        
        #Set  default IPAdd.
        self._IpAdd = ipAddress
                
        #Set debug mode
        self._DebugModeLevel = debugLvl
        
        #Set value if polling external sensors
        self._PollExternalSensors = pollExtSns
        
        #SyncClimateInfoLockout: Lockout SynchClimateInfo whilst checking temp sensors, incase multi process is used.
        self._SyncClimateInfoLockout = 0
        
        #SyncLockout: Lockout whilst piZone syching with Skyzone. Prevents loss of data if temp/setting change is done during sync.
        self._SyncLockout = 0
        
        
    #Discover function for SkyZone   
    def discover_skyzoneController(self):
        #only attemp if ipADD is not set;
        if (self._IpAdd == '0.0.0.0'):
            # Attempt to find SkyZone controller
            # Broadcast and wait for response from SkyZone controller target port 30050
            UDPsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            UDPsocket.settimeout(10.0)  #wait 10sec for timeout
            UDPsocket.bind(('0.0.0.0', 36999))  #resp. will come in port 36999
            UDPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #set socket to broadcast mode
            
            try:
                UDPsocket.sendto(bytes("DAIKIN_UDP/common/basic_info", "utf-8"), (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))
                            
                while True:
                    #wait for response
                    data, addr = UDPsocket.recvfrom(self.SOCKET_BUFSIZE)
                    
                    #check for SkyZone response (just incase something else reports on the same broadcast/port)
                    if ((data.decode("utf-8"))[0:23] == 'ret=OK,type=Duct Aircon'):              
                   
                       self._IpAdd = addr[0]
                       _LOGGER.info('Daikin SkyZone found at IP: %s', addr)
                       break

            except socket.timeout:
                _LOGGER.error('Daikin SkyZone: UDP timeout (10 seconds)')
                UDPsocket.close()
                return False
                    
            except OSError as error:
                _LOGGER.error('Could not broadcast UDP : %s', error )
                UDPsocket.close()
                return False
            
            UDPsocket.close()
    
        #else, attemp connection;
                        
        #IP for SkyZone now received. Begin getting initial data from unit to populate locate data instances
        if(self._IpAdd != '0.0.0.0'):
            SendReceiveFrame(self, "InitialInfo")
            SendReceiveFrame(self, "BasicInfo")
            SendReceiveFrame(self, "GetZoneNames")
            SendReceiveFrame(self, "GetSensorZoneNames")
            if(self._PollExternalSensors == 0):
                #poll internal/coolant if not polling externals
                UpdateTempSensorDataProcess(self)
        #check for valid serial
        return (IsUnitDataPresent(self) == 1)


    #-------------------------------------------#
    # Get/Set Functions Definitions #
    #-------------------------------------------#

    #UnitConnected
    #Function determins if PiZone has successfully been connected to SkyZone.
    def IsUnitConnected(self):  return IsUnitDataPresent(self)
    
    #Function returns part numbers for indoor/outdoor unit
    def GetIndoorUnitPartNumber(self): return GetIndoorPartNumber(self)
    def GetOutdoorUnitPartNumber(self): return GetOutdoorPartNumber(self)
    
    
    #ACMode
    # Functions to get/set the ACMode, i.e. Fan, Dry, Heating, Cooling and Auto
    def GetCurrentMode(self):   return GetClimateMode(self)
    def SetCurrentMode(self, SetAcMode):
        if isinstance(SetAcMode, AcStateMode):  SetClimateMode(self, SetAcMode)
            
    #TargetTemp
    # Functions to get/set the TargetTemp for Heating/Cooling (Unit has two separate entries for heating/cooling temp)
    def GetTargetTemp(self):    return GetTargetClimateTemp(self)
    def SetTargetTemp(self, SetTemp):   SetTargetClimateTemp(self, int(SetTemp))
     
    #TempSensor
    # Functions to get current temp of the selected sensor.
    def GetCurrentTempValue(self):         return GetClimateCurrentTempValue(self)
    # Functions to get/set the 'Sensor' which is used at the reference for Heating/Cooling.
    def GetSelectedTempSensor(self):    return GetClimateTempSensor(self)
    def SetSelectedTempSensor(self, SetSensorIndex):
        SetClimateTempSensor(self, (SensorIndex)(SetSensorIndex))
        
    #Function gets the number of external sensors connected/configured to Daikin Unit
    def GetNumberExternalSensors(self): return GetClimateExternalSensorCount(self)
         
    #Function gets the name of the sensor as given by the Daikin Unit for the given Sensor Index
    def GetSensorName(self, SensorValue):
        return GetClimateSensorName(self, (SensorIndex)(SensorValue))
        
    #Function gets the state (if its been selected or not) of the sensor as for the given Sensor Index
    #Only the sesnor which is currently selected will return 'True'. All other will return 'False'
    def GetSensorState(self, SensorValue):
        return GetClimateSensorState(self, (SensorIndex)(SensorValue))
        
    #Function gets the temperture of the SensorIndex.
    #If the value is '0' it will return 'None'. 
    #If pollExtSns is 0, it will return 'None' for any external sensor which is not the selected sensor.
    def GetSensorValue(self, SensorValue):
        return GetClimateSensorValue(self, (SensorIndex)(SensorValue))
 
    #Zones   
    #Function returns the number of zones configured to the Daikin Unit
    def GetNumberOfZones(self):         return GetClimateNumberOfZones(self)
    
    #Function returns the name of the zones as given by the Daikin Unit for the Given zoneIndex
    def GetZoneName(self, zoneIndex):   return GetClimateZoneName(self, zoneIndex)

    #Function returns the state (active/inactive) of the given zoneIndex
    def GetZonesState(self, zoneIndex): return GetClimateZoneState(self, zoneIndex)
   
    #Function sets the given zoneIndex to active/inactive.
    def SetZoneActive(self, zoneIndex): SetClimateZoneActive(self, zoneIndex)
    def SetZoneInactive(self, zoneIndex):
        SetClimateZoneInactive(self, zoneIndex)
     
    #FanSpeed
    # Functions to get/set the FanSpeed which is used at for Heating/Cooling. (Unit has two separate entries for heating/cooling temp)
    def GetFanSpeed(self):  return GetClimateFanSpeed(self)
    def SetFanSpeed(self, SetFanSpeedValue):
        if isinstance(SetFanSpeedValue, FanSpeed):  SetSelectedFanSpeed(self, SetFanSpeedValue)
            
    #OtherInterfaces
    def GetMinSupportTemp(self): return GetClimiateMinSupportedTemp(self)
    def GetMaxSupportTemp(self): return GetClimiateMaxSupportedTemp(self)
    def GetErrorCodes(self): return GetClimateErrorCodes(self)
    def GetHistoryErrorCodes(self): return GetClimateHistoryErrorCodes(self)
    def GetClearFilterFlag(self): return GetClimateClearFilterFlag(self)
            
    #SyncFunctions
    # Functions to trigger update in local data or sync controller updates from changes made to local data.
    #Sync base info to get PowerState, AcMode, SelectTemp Sensor, TargetTemp, FanSpeed and Zone settings.
    def SyncClimateInfo(self):  SendReceiveFrame(self, "BasicInfo")
    
    #Sync updated setting from PiZone to SkyZone controller (i.e. send). If not done, changes will be lost next time "BasicInfo" is called
    def SyncClimateSettingsData(self):  
        SendReceiveFrame(self,"SyncControInfo")
        time.sleep(C_DaikinDelay_SyncSetting)
        self.SyncUpdate()
        
    #Sync update TempSensor selection from PiZone to SkyZone controller
    def SyncClimateSensor(self):    
        SendReceiveFrame(self, "SetAcTempReadSensor")
        time.sleep(C_DaikinDelay_SyncSetting)
        self.SyncUpdate()
        
    #Sync all temp sensor data from SkyZone to PiZone. Use ServiceMode to get refrigerant, internal and external values.
    def SyncTempInfoViaServiceMode(self):   UpdateTempSensorDataProcess(self)
    
    #Sync all temp sensor data from SkyZone to PiZone. Use ServiceMode external values.
    def SyncExternalTempInfoViaServiceMode(self):   UpdateExternalTempSensorDataProcess(self)
    
    #Update call from HA
    def BasicUpdate(self):
        #lockout required to prevent loss of updated HA settings during sync
        self._SyncLockout = 1
        self.SyncClimateInfo()
        self._SyncLockout = 0
    
    def TempSensorUpdate(self):    
        #no lockout required as only using service mode without modifying logic.
        self.SyncTempInfoViaServiceMode()
    
    def ExternalTempSensorUpdate(self):
        #lockout required as logic modifies items which otherwise would be updated by user.
        #check logic has been enabled
        if(self._PollExternalSensors == 1):
            self._SyncLockout = 1        
            self.SyncExternalTempInfoViaServiceMode()
            self._SyncLockout = 0
        
    def SyncUpdate(self): 
        #Check for lockout incase sync is called during update cycle.
        while(self._SyncLockout == 1):
            time.sleep(1)
            
        self._SyncLockout = 1
        self.SyncClimateInfo()
        self._SyncLockout = 0
        