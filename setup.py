# -*- coding: utf-8 -*-

from setuptools import setup
from phue import __version__

setup(name='phue',
      version=__version__,
      author='Nathanaël Lécaudé',
      url='https://github.com/studioimaginaire/phue',
      license='MIT',
      description='A Philips Hue Python library',
      long_description='A Philips Hue Python library',
      py_modules=['phue'],
      )
