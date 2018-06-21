#PCD 
C_PCD_BasicInfo =0xA0                # Get all info from unit
C_PCD_InitialInfo = 0xA1                # Get unit type and limits
C_PCD_ControlInfo = 0xB0            # Set ac control inputs to unit
C_PCD_InternalAcMode = 0xB2        # Set internal ac mode/state
C_PCD_SelectSensor = 0xB3            # Set temp sensor
C_PCD_GetLocalSetting = 0xC0        # Get 'service' info
C_PCD_SetLocalSetting = 0xC3        # Set 'service' settings 
C_PCD_GetZoneNames = 0xD0        # Get zone names
C_PCD_GetSensorNames = 0xD2    # Get sensor names

#Unused
C_PCD_OnOffTimer = 0xB1;
C_PCD_ClearFilter = 0xB4;
C_PCD_Clock = 0xB5;
C_PCD_Set7DaysTimer = 0xB6;
C_PCD_ClearErrorCode = 0xBD;
C_PCD_SetAirFlow = 0xBE;        #might be of use to create custom fan speed blending logic
C_PCD_Get7DaysTimer = 0xC1;
C_PCD_GetAirFlow = 0xC2            # Get airflow settings
C_PCD_EnergySaving = 0xD1;         # Controlled via hand controller. HA has no need. Controlled via Automation
C_PCD_DealerContact = 0xD3
C_PCD_SYUInfo = 0xD5;

#Daiking Request Types
C_REQUEST_GETUP = 0x62;
C_REQUEST_GET = 0x66;
C_REQUEST_SET = 0x61;

#Daikin Header - 8 bytes. Byte 3 is used for RequestType
C_DaikinHeader = bytearray([0xC1, 0x00, 0x01, 0xFF , 0x00, 0x12, 0x34, 0x00])

#Daikin Data  Request - 7 bytes. Byte 5 is used for PCD
C_DaikinDataRequest = bytearray([0xE1, 0x01, 0x13, 0x01, 0x01, 0xFF, 0x00])

#Daikin Data Requests
#Request = 0x61   - 15 bytes. Byte 7 -> 14 is used for AC state setting
C_DaikinDataAcState = bytearray([0xE1, 0x01, 0x13, 0x01, 0x01, 0xB0, 0x08, 0xFF, 0xFF, 0x0, 0xFF, 0x0, 0xFF, 0xFF, 0xFF])

#Daiken Data Request - 8 bytes. Byte 8 is used to select ac internal mode 
C_DaikinDataInternalMode = bytearray([0xE1, 0x01, 0x13, 0x01, 0x01, 0xB2, 0x01, 0xFF])

#Request = 0x61  - 8 bytes. Byte 8 is used to select sensor ID
C_DaikinDataSensorSelect = bytearray([0xE1, 0x01, 0x13, 0x01, 0x01, 0xB3, 0x01, 0xFF])

#Daiken Data Request - 9 bytes. Byte 8 is used to select desired temp sensor (in this case refrigerant)
C_DaikinDataControlInfoTemp = bytearray([0xE1, 0x01, 0x13, 0x01, 0x01, 0xC0, 0x02, 0x41, 0xFF])

#DakingChecksum - 2bytes.
C_DaikinChecksum = bytearray([0xFF, 0xFF])
   
#Delay Constants for switching
C_DaikinDelay_InternalAcModeChange = 3      #Takes 3 seconds from internal AC mode (i.e. Service/Normal)   
C_DaikinDelay_TempSensorChange = 6          #Takes 6 seconds from requesting 'temp' sensor till value is switched   
C_DaikinDelay_ServiceModeInfoUpdate = 2     #Takes 2 transmissions  to update info on service mode.   
C_DaikinDelay_ServiceRequest = 1.5          #ServiceMode takes 1.5s to update request buffer 
C_DaikinDelay_SyncSetting = 5               #Deley between submitting a 'new' setting and being able to read it back again   