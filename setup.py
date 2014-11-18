#!/usr/bin/env python
"""
Setup file for pyhaystack
"""
from pyhaystack.client.HaystackConnection import HaystackConnection
from pyhaystack.client.NiagaraAXConnection import NiagaraAXConnection
from pyhaystack import pyhaystack as ph

#from setuptools import setup
from distutils.core import setup

import re
import os
import requests

os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'


setup(name='pyhaystack',
      version=ph.__version__,
	description='Python Haystack Utility',
      author='Christian Tremblay',
      author_email='christian.tremblay@servisys.com',
      url='http://www.project-haystack.com/',
	long_description = "\n".join(ph.__doc__.split('\n')),
	install_requires = ['requests','setuptools'],
      packages=['pyhaystack'],
      entry_points={
          'console_scripts': ['pyhaystack=pyhaystack:main'],
      },
      )