# -*- coding: utf-8 -*-
"""
State machine interface.  This is a base class for implementing state machines.
"""

from copy import copy, deepcopy
from signalslot import Signal
from threading import Event

from .asyncexc import AsynchronousException

# Exclude the imports below from coverage, as we can't exercise all code paths
# in unit tests, and Python 3.3+ ships with asyncio.futures, so will always
# execute this code path ignoring the Tornado support.

# Support for asyncio
try:  # pragma: no cover
    from asyncio.futures import Future

    HAVE_FUTURE = "asyncio"
except ImportError:  # pragma: no cover
    HAVE_FUTURE = None

if HAVE_FUTURE is None:  # pragma: no cover
    # Try Tornado
    try:
        from tornado.concurrent import Future

        HAVE_FUTURE = "tornado"
    except ImportError:
        pass


class NotReadyError(Exception):
    """
    Exception raised when an attempt is made to retrieve the result of an
    operation before it is ready.
    """

    pass


class BaseHaystackOperation(object):
    """
    A core state machine object.  This implements the basic interface presented
    for all operations in pyhaystack.
    """

    def __init__(self, result_copy=True, result_deepcopy=True):
        """
        Initialisation.  This should be overridden by subclasses to accept and
        validate the inputs presented for the operation, raising an appropriate
        Exception subclass if the inputs are found to be invalid.

        These should be stored here by the initialisation function as private
        variables in suitably sanitised form.  The core state machine object
        shall then be created and stored before the object is returned to the
        caller.
        """
        # Event object to represent when this operation is "done"
        self._done_evt = Event()

        # Signal emitted when the operation is "done"
        self.done_sig = Signal(name="done", threadsafe=True)

        # Result returned by operation
        self._result = None
        self._result_copy = result_copy
        self._result_deepcopy = result_deepcopy

    def go(self):  # pragma: no cover
        """
        Start processing the operation.  This is called by the caller (so after
        all __init__ functions have executed) in order to begin the asynchronous
        operation.
        """
        # This needs to be implemented in the subclass.
        raise NotImplementedError(
            "To be implemented in subclass %s" % self.__class__.__name__
        )

    def wait(self, timeout=None):
        """
        Wait for an operation to finish.  This should *NOT* be called in the
        same thread as the thread executing the operation as this will
        deadlock.
        """
        self._done_evt.wait(timeout)

    @property
    def future(self):
        """
        Return a Future object (asyncio or Tornado).
        """
        # Exclude this if-statement from coverage as it's only older Python 2
        # users that are likely to encounter this and we can't control this
        # branch in a unit test context anyway.
        if HAVE_FUTURE is None:  # pragma: no cover
            raise NotImplementedError(
                "Futures require either asyncio and/or Tornado (>=4) to work"
            )

        # Both Tornado and asyncio future classes work the same.
        future = Future()
        if self.is_done:
            self._set_future(future)
        else:
            # Not done yet, wait for it
            def _on_done(*a, **kwa):
                self._set_future(future)

            self.done_sig.connect(_on_done)

        # Return the future for the caller
        return future

    @property
    def state(self):
        """
        Return the current state machine's state.
        """
        return self._state_machine.current

    @property
    def is_done(self):
        """
        Return true if the operation is complete.
        """
        return self._state_machine.is_finished()

    @property
    def is_failed(self):
        """
        Return true if the result is an Exception.
        """
        return isinstance(self._result, AsynchronousException)

    @property
    def result(self):
        """
        Return the result of the operation or raise its exception.
        Raises NotReadyError if not ready.
        """
        if not self.is_done:
            raise NotReadyError()

        if self.is_failed:
            self._result.reraise()

        if not self._result_copy:
            # Return the original instance (do not copy)
            return self._result
        elif self._result_deepcopy:
            # Return a deep copy
            return deepcopy(self._result)
        else:
            # Return a shallow copy
            return copy(self._result)

    def __repr__(self):
        """
        Return a representation of this object's state.
        """
        if self.is_failed:
            return "<%s failed>" % self.__class__.__name__
        elif self.is_done:
            return "<%s done: %s>" % (self.__class__.__name__, self._result)
        else:
            return "<%s %s>" % (self.__class__.__name__, self.state)

    def _done(self, result):
        """
        Return the result of the operation to any listeners.
        """
        self._result = result
        self._done_evt.set()
        self.done_sig.emit(operation=self)

    def _set_future(self, future):
        """
        Set the given future to the operation result, if known
        or raise an exception otherwise.
        """
        # It's already done
        try:
            future.set_result(self.result)
        except Exception as e:
            future.set_exception(e)
