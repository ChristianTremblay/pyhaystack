# -*- coding: utf-8 -*-
"""
State machine interface.  This is a base class for implementing state machines.
"""

from ..operation import BaseHaystackOperation
from collections.abc import Awaitable


class HaystackOperation(BaseHaystackOperation, Awaitable):
    """
    Awaitable version of BaseHaystackOperation.  This is provided for later
    versions of Python 3 (3.5 and up) that support the `await` keyword.
    """

    def __await__(self):
        """
        Return a future object which can be awaited by asyncio-aware
        tools like ipython and in asynchronous scripts.
        """
        res = yield from self.future
        return res
