# -*- coding: utf-8 -*-

from .utils import PY3K, logger


class SensorState(dict):
    def __init__(self, bridge, sensor_id):
        self._bridge = bridge
        self._sensor_id = sensor_id

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._bridge.set_sensor_state(self._sensor_id, self)


class SensorConfig(dict):
    def __init__(self, bridge, sensor_id):
        self._bridge = bridge
        self._sensor_id = sensor_id

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._bridge.set_sensor_config(self._sensor_id, self)


class Sensor(object):

    """ Hue Sensor object

    Sensor config and state can be read and updated via the properties of this object

    """
    def __init__(self, bridge, sensor_id):
        self.bridge = bridge
        self.sensor_id = sensor_id

        self._name = None
        self._model = None
        self._swversion = None
        self._type = None
        self._uniqueid = None
        self._manufacturername = None
        self._state = SensorState(bridge, sensor_id)
        self._config = {}
        self._recycle = None

    def __repr__(self):
        # like default python repr function, but add sensor name
        return '<{0}.{1} object "{2}" at {3}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self)))

    # Wrapper functions for get/set through the bridge
    def _get(self, *args, **kwargs):
        return self.bridge.get_sensor(self.sensor_id, *args, **kwargs)

    def _set(self, *args, **kwargs):
        return self.bridge.set_sensor(self.sensor_id, *args, **kwargs)

    @property
    def name(self):
        '''Get or set the name of the sensor [string]'''
        if PY3K:
            self._name = self._get('name')
        else:
            self._name = self._get('name').encode('utf-8')
        return self._name

    @name.setter
    def name(self, value):
        old_name = self.name
        self._name = value
        self._set('name', self._name)

        logger.debug("Renaming sensor from '{0}' to '{1}'".format(
            old_name, value))

        self.bridge.sensors_by_name[self.name] = self
        del self.bridge.sensors_by_name[old_name]

    @property
    def modelid(self):
        '''Get a unique identifier of the hardware model of this sensor [string]'''
        self._modelid = self._get('modelid')
        return self._modelid

    @property
    def swversion(self):
        '''Get the software version identifier of the sensor's firmware [string]'''
        self._swversion = self._get('swversion')
        return self._swversion

    @property
    def type(self):
        '''Get the sensor type of this device [string]'''
        self._type = self._get('type')
        return self._type

    @property
    def uniqueid(self):
        '''Get the unique device ID of this sensor [string]'''
        self._uniqueid = self._get('uniqueid')
        return self._uniqueid

    @property
    def manufacturername(self):
        '''Get the name of the manufacturer [string]'''
        self._manufacturername = self._get('manufacturername')
        return self._manufacturername

    @property
    def state(self):
        ''' A dictionary of sensor state. Some values can be updated, some are read-only. [dict]'''
        data = self._get('state')
        self._state.clear()
        self._state.update(data)
        return self._state

    @state.setter
    def state(self, data):
        self._state.clear()
        self._state.update(data)

    @property
    def config(self):
        ''' A dictionary of sensor config. Some values can be updated, some are read-only. [dict]'''
        data = self._get('config')
        self._config.clear()
        self._config.update(data)
        return self._config

    @config.setter
    def config(self, data):
        self._config.clear()
        self._config.update(data)

    @property
    def recycle(self):
        ''' True if this resource should be automatically removed when the last reference to it disappears [bool]'''
        self._recycle = self._get('manufacturername')
        return self._manufacturername
