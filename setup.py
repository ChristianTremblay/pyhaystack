#!/usr/bin/env python
"""
Setup file for pyhaystack
"""
import pyhaystack
import os

os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

from distutils.core import setup
setup(name='pyhaystack',
      version=pyhaystack.__version__,
	  description='Python Haystack Utility',
      author='Christian Tremblay',
      author_email='christian.tremblay@servisys.com',
      url='http://www.project-haystack.com/',
	  long_description = "\n".join(pyhaystack.__doc__.split('\n')),
	  py_modules=['pyhaystack'],
	  install_requires = ['requests','setuptools']
      )