# Library to handle connection with Daikin Skyzone
from daikinPyZone.daikinProcess import *

from daikinPyZone.daikinClasses import (
    DaikinClimateInformation,
    DaikinClimateSettings)

_LOGGER = logging.getLogger(__name__)


class DaikinSkyZone(object):

    BROADCAST_ADDRESS = '255.255.255.255'
    # Target UDP port for Daikin SkyZone
    BROADCAST_PORT = 30050
    SOCKET_BUFFER_SIZE = 1024

    def __init__(self,
                 password=None,
                 name='Daikin Skyzone',
                 ip_address='0.0.0.0',
                 debug_level=0,
                 poll_external_sensors=0):
        # Create info structs for Info and Settings classes.
        self._DaikinClimateInfo_Object = DaikinClimateInformation()
        self._DaikinClimateSettings_Object = DaikinClimateSettings()

        # set name
        self._name = name

        # Set default IPAdd.
        self._IpAdd = ip_address

        # Set password
        self._Pwd = password

        # Set debug mode
        self._DebugModeLevel = debug_level

        # Set value if polling external sensors
        self._PollExternalSensors = poll_external_sensors

        # SyncClimateInfoLockout: Lockout SyncClimateInfo whilst checking temp sensors, in-case multi process is used.
        self._SyncClimateInfoLockout = 0

        # SyncLockout: Lockout whilst piZone syncing with Skyzone.
        # Prevents loss of data if temp/setting change is done during sync.
        self._SyncLockout = 0

    # Discover function for SkyZone
    def discover_skyzone_controller(self):

        while self._SyncLockout == 1:
            time.sleep(0.25)

        current_ip_address = self._IpAdd

        # Attempt to find SkyZone controller
        # Broadcast and wait for response from SkyZone controller target port 30050
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)       # UDP
        udp_socket.settimeout(10.0)                                         # Wait 10sec for timeout
        udp_socket.bind(('0.0.0.0', 36999))                                 # Resp. will come in port 36999
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    # Set socket to broadcast mode

        try:
            udp_socket.sendto(bytes("DAIKIN_UDP/common/basic_info", "utf-8"),
                              (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))

            while True:
                # Wait for response
                data, address = udp_socket.recvfrom(self.SOCKET_BUFFER_SIZE)

                # Check for SkyZone response (just in-case something else reports on the same broadcast/port)
                if (data.decode("utf-8"))[0:23] == 'ret=OK,type=Duct Aircon':
                    self._IpAdd = address[0]
                    _LOGGER.info('Daikin SkyZone found at IP: %s', address)
                    break

        except socket.timeout:
            _LOGGER.error('Daikin SkyZone: UDP timeout (10 seconds)')
            udp_socket.close()
            return False

        except OSError as error:
            _LOGGER.error('Could not broadcast UDP : %s', error)
            udp_socket.close()
            return False

        udp_socket.close()

        # IP for SkyZone now received.
        # Begin getting initial data from unit to populate locate data instances
        send_receive_frame(self, "InitialInfo")
        send_receive_frame(self, "BasicInfo")

        # Only get 'Zones/Sensors on 'new' connection
        if self._IpAdd != current_ip_address:
            send_receive_frame(self, "GetZoneNames")
            send_receive_frame(self, "GetSensorZoneNames")

            # Poll internal/coolant if not polling externals
            if self._PollExternalSensors == 0:
                update_temp_sensor_data_process(self)

        # Check for valid serial
        return is_unit_data_present(self) is True

    # -------------------------------------------#
    # Get/Set Functions Definitions #
    # -------------------------------------------#

    # Function determines if PiZone has successfully been connected to SkyZone.
    def is_unit_connected(self):
        return is_unit_data_present(self)

    # Function returns part numbers for indoor/outdoor unit
    def get_indoor_unit_part_number(self):
        return get_indoor_part_number(self)

    def get_outdoor_unit_part_number(self):
        return get_outdoor_part_number(self)

    # ACMode
    # Functions to get/set the ACMode, i.e. Fan, Dry, Heating, Cooling and Auto
    def get_current_mode(self):
        return get_climate_mode(self)

    def set_current_mode(self, ac_mode):
        if isinstance(ac_mode, AcStateMode):
            set_climate_mode(self, ac_mode)

    # TargetTemp
    # Functions to get/set the TargetTemp for Heating/Cooling (Unit has two separate entries for heating/cooling temp)
    def get_target_temp(self):
        return get_target_climate_temp(self)

    def set_target_temp(self, temp):
        set_target_climate_temp(self, int(temp))

    # TempSensor
    # Functions to get current temp of the selected sensor.
    def get_current_temp(self):
        return get_climate_current_temperature(self)

    # Functions to get/set the 'Sensor' which is used at the reference for Heating/Cooling.
    def get_selected_temp_sensor(self):
        return get_climate_temp_sensor(self)

    def set_selected_temp_sensor(self, sensor_index):
        set_climate_temp_sensor(self, SensorIndex(sensor_index))

    # Function gets the number of external sensors connected/configured to Daikin Unit
    def get_number_of_external_sensors(self):
        return get_climate_external_sensor_count(self)

    # Function gets the name of the sensor as given by the Daikin Unit for the given Sensor Index
    def get_sensor_name(self, sensor_value):
        return get_climate_sensor_name(self, SensorIndex(sensor_value))

    # Function gets the state (if its been selected or not) of the sensor as for the given Sensor Index
    # Only the sensor which is currently selected will return 'True'. All other will return 'False'
    def get_sensor_state(self, sensor_value):
        return get_climate_sensor_state(self, SensorIndex(sensor_value))

    # Function gets the temperature of the SensorIndex.
    # If the value is '0' it will return 'None'.
    # If pollExtSns is 0, it will return 'None' for any external sensor which is not the selected sensor.
    def get_sensor_temperature(self, sensor_value):
        return get_climate_sensor_temperature(self, SensorIndex(sensor_value))

    # Zones
    # Function returns the number of zones configured to the Daikin Unit
    def get_number_of_zones(self):
        return get_climate_number_of_zones(self)

    # Function returns the name of the zones as given by the Daikin Unit for the Given zoneIndex
    def get_zone_name(self, zone_index):
        return get_climate_zone_name(self, zone_index)

    # Function returns the state (active/inactive) of the given zoneIndex
    def get_zone_state(self, zone_index):
        return get_climate_zone_state(self, zone_index)

    # Function sets the given zoneIndex to active/inactive.
    def set_zone_active(self, zone_index):
        return set_climate_zone_active(self, zone_index)

    def set_zone_inactive(self, zone_index):
        set_climate_zone_inactive(self, zone_index)

    # FanSpeed
    # Functions to get/set the FanSpeed which is used at for Heating/Cooling.
    # (Unit has two separate entries for heating/cooling temp)
    def get_fan_speed(self):
        return get_climate_fan_speed(self)

    def set_fan_speed(self, fan_speed):
        if isinstance(fan_speed, FanSpeed):
            set_climate_fan_speed(self, fan_speed)

    # OtherInterfaces
    def get_min_supported_temp(self):
        return get_climate_min_supported_temp(self)

    def get_max_supported_temp(self):
        return get_climate_max_supported_temp(self)

    def get_error_codes(self):
        return get_climate_error_codes(self)

    def get_history_error_codes(self):
        return get_climate_history_error_codes(self)

    def get_clear_filter_flag(self):
        return get_climate_clear_filter_flag(self)

    # SyncFunctions
    # Functions to trigger update in local data or sync controller updates from changes made to local data.

    # Sync updated setting from PiZone to SkyZone controller (i.e. send).
    # If not done, changes will be lost next time "BasicInfo" is called
    def sync_climate_request(self):
        # Check for lockout in-case sync is called during update cycle.
        while self._SyncLockout == 1:
            time.sleep(0.25)

        self._SyncLockout = 1
        send_receive_frame(self, "SyncControlInfo")
        time.sleep(C_DaikinDelay_SyncSetting)
        self._SyncLockout = 0
        self.update()

    # Sync update TempSensor selection from PiZone to SkyZone controller
    def update_temperate_sensor(self):
        # Check for lockout in-case sync is called during update cycle.
        while self._SyncLockout == 1:
            time.sleep(0.25)

        # Check for lockout in-case sync is called during update cycle.
        self._SyncLockout = 1
        send_receive_frame(self, "SetAcTempReadSensor")
        time.sleep(C_DaikinDelay_SyncSetting)
        self._SyncLockout = 0
        self.update()

    def update_additional_temperature_sensors(self):
        # Lockout required as logic modifies items which otherwise would be updated by user.
        # Check for lockout in-case sync is called during update cycle.
        while self._SyncLockout == 1:
            time.sleep(0.25)

        # Check logic has been enabled
        if self._PollExternalSensors == 1:
            self._SyncLockout = 1
            update_external_temp_sensor_data_process(self)
            self._SyncLockout = 0

        self._SyncLockout = 1
        update_temp_sensor_data_process(self)
        self._SyncLockout = 0

    # Sync basic info to get PowerState, AcMode, SelectTemp Sensor, TargetTemp, FanSpeed and Zone settings.
    def update(self):
        while self._SyncLockout == 1:
            time.sleep(0.25)

        self._SyncLockout = 1
        send_receive_frame(self, "BasicInfo")
        self._SyncLockout = 0
