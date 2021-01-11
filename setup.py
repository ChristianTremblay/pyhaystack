#!/usr/bin/env python
"""
Setup file for pyhaystack
"""
import pyhaystack.info as info

from setuptools import setup

import os

os.environ["COPY_EXTENDED_ATTRIBUTES_DISABLE"] = "true"
os.environ["COPYFILE_DISABLE"] = "true"


setup(
    name="pyhaystack",
    version=info.__version__,
    description="Python Haystack Utility",
    author=info.__author__,
    author_email=info.__author_email__,
    url="http://www.project-haystack.com/",
    keywords=["tags", "hvac", "project-haystack", "building", "automation", "analytic"],
    install_requires=[
        "requests",
        "setuptools",
        "pandas",
        "iso8601",
        "hszinc",
        "six",
        "fysom",
        "signalslot",
        "semver",
        "certifi",
    ],
    packages=[
        "pyhaystack",
        "pyhaystack.client",
        "pyhaystack.client.mixins",
        "pyhaystack.client.mixins.vendor",
        "pyhaystack.client.mixins.vendor.widesky",
        "pyhaystack.client.mixins.vendor.skyspark",
        "pyhaystack.client.mixins.vendor.niagara",
        "pyhaystack.client.http",
        "pyhaystack.client.ops",
        "pyhaystack.client.ops.vendor",
        "pyhaystack.client.entity",
        "pyhaystack.client.entity.mixins",
        "pyhaystack.client.entity.models",
        "pyhaystack.client.entity.ops",
        "pyhaystack.util",
        "pyhaystack.server",
        "pyhaystack.util",
    ],
    long_description=open("README.rst").read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
)
