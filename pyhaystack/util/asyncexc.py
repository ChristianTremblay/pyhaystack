# -*- coding: utf-8 -*-
"""
Asynchronous Exception Handler.  This implements a small lightweight object for
capturing an exception in a manner that can be passed in callback arguments then
re-raised elsewhere for handling in the callback function.

Typical usage::

    def _some_async_function(…, callback_fn):
        try:
            do some async op that may fail
            result = ...
        except: # Capture all exceptions
            result = AsynchronousException()
        callback_fn(result)

"""


from sys import exc_info
from six import reraise


class AsynchronousException(object):
    def __init__(self):
        self._exc_info = exc_info()

    def reraise(self):
        reraise(*self._exc_info)
