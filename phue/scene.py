# -*- coding: utf-8 -*-


class Scene(object):
    """ Container for Scene """

    def __init__(self, sid, appdata=None, lastupdated=None,
                 lights=None, locked=False, name="", owner="",
                 picture="", recycle=False, version=0):
        self.scene_id = sid
        self.appdata = appdata or {}
        self.lastupdated = lastupdated
        if lights is not None:
            self.lights = sorted([int(x) for x in lights])
        else:
            self.lights = []
        self.locked = locked
        self.name = name
        self.owner = owner
        self.picture = picture
        self.recycle = recycle
        self.version = version

    def __repr__(self):
        # like default python repr function, but add sensor name
        return '<{0}.{1} id="{2}" name="{3}" lights={4}>'.format(
            self.__class__.__module__,
            self.__class__.__name__,
            self.scene_id,
            self.name,
            self.lights)
