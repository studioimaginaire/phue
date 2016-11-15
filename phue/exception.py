# -*- coding: utf-8 -*-


class PhueException(Exception):
    def __init__(self, id, message):
        self.id = id
        self.message = message


class PhueRegistrationException(PhueException):
    pass


class PhueRequestTimeout(PhueException):
    pass
