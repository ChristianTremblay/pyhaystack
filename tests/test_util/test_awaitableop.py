# -*- coding: utf-8 -*-
"""
Tests for awaitable HaystackOperation class
"""

# This is a wrapper around awaitableop to hide the tests from Python 2.
from sys import version_info

if version_info.major < 3:
    pass
elif version_info.minor < 5:
    pass
else:
    from .awaitableop import TestHaystackOperationAwait

    assert TestHaystackOperationAwait
