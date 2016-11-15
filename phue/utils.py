# -*- coding: utf-8 -*-

import sys
import platform
import logging

if sys.version_info[0] > 2:
    PY3K = True
else:
    PY3K = False

if platform.system() == 'Windows':
    USER_HOME = 'USERPROFILE'
else:
    USER_HOME = 'HOME'

if 'iPad' in platform.machine() or 'iPhone' in platform.machine() or 'iPad' in platform.machine():
    MOBILE = True
else:
    MOBILE = False

logger = logging.getLogger('phue')


def is_string(data):
    """Utility method to see if data is a string."""
    if PY3K:
        return isinstance(data, str)
    else:
        return isinstance(data, (str, unicode)) # noqa
