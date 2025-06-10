# -*- coding: utf-8 -*-
"""
State machine interface.  This is a base class for implementing state machines.
"""

from .operation import HAVE_FUTURE, NotReadyError, BaseHaystackOperation
from copy import deepcopy
from ..signalslot.signalslot import Signal
from threading import Event

from .asyncexc import AsynchronousException


assert NotReadyError
assert BaseHaystackOperation

# Exclude these branches from coverage as it's likely the
# `HAVE_FUTURE == 'asyncio'` branch will only work on Python 3 (and will always
# work there) whereas Python 2.7 will never trigger this branch.
if HAVE_FUTURE == "asyncio":  # pragma: no cover
    from .awaitable.operation import HaystackOperation
else:  # pragma: no cover

    class HaystackOperation(BaseHaystackOperation):
        pass
