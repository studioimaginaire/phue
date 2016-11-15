# -*- coding: utf-8 -*-

from phue import __version__
from distutils.core import setup

setup(
    name = 'phue',
    version = __version__,
    description = 'A Philips Hue Python library',
    author = 'Nathanaël Lécaudé',
    license='MIT',
    url = 'https://github.com/studioimaginaire/phue',
    py_modules=['phue'],
)
