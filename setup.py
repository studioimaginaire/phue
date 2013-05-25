# -*- coding: utf-8 -*-

from setuptools import setup
from phue import __version__

readme = open('README.md').read()

setup(name='phue',
      version=__version__,
      author='Nathanaël Lécaudé',
      url='https://github.com/studioimaginaire/phue',
      license='WTFPL',
      description='A Philips Hue Python library',
      long_description=readme,
      py_modules=['phue'],
      )
