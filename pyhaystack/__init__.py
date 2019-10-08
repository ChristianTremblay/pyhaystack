#!python
# -*- coding: utf-8 -*-
"""
Main init file

Loading hszinc
Creating "connect" shortcut for get_instance

This file will also automatically disable SubjectAltNameWarning when dealing with 
CA certificate. See docs for more information about that.

"""

try:
    from hszinc import Quantity, use_pint

    Q_ = Quantity
    from .client.loader import get_instance as connect
    import requests.packages.urllib3
    from requests.packages.urllib3.exceptions import SubjectAltNameWarning

    requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)


except ImportError:
    pass
