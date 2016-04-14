# -*- coding: utf-8 -*-
"""
State machine interface.  This is a base class for implementing state machines.
"""

from copy import deepcopy
from signalslot import Signal
from threading import Event

from .asyncexc import AsynchronousException


class NotReadyError(Exception):
    """
    Exception raised when an attempt is made to retrieve the result of an
    operation before it is ready.
    """
    pass


class HaystackOperation(object):
    """
    A core state machine object.  This implements the basic interface presented
    for all operations in pyhaystack.
    """
    def __init__(self, result_deepcopy=True):
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
        self.done_sig = Signal(name='done', threadsafe=True)

        # Result returned by operation
        self._result = None
        self._result_deepcopy = result_deepcopy

    def go(self):
        """
        Start processing the operation.  This is called by the caller (so after
        all __init__ functions have executed) in order to begin the asynchronous
        operation.
        """
        # This needs to be implemented in the subclass.
        raise NotImplementedError("To be implemented in subclass %s" \
                % self.__class__.__name__)

    def wait(self, timeout=None):
        """
        Wait for an operation to finish.  This should *NOT* be called in the
        same thread as the thread executing the operation as this will
        deadlock.
        """
        self._done_evt.wait(timeout)

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
    def result(self):
        """
        Return the result of the operation or raise its exception.
        Raises NotReadyError if not ready.
        """
        if not self.is_done:
            raise NotReadyError()

        if isinstance(self._result, AsynchronousException):
            self._result.reraise()

        if self._result_deepcopy:
            # Return a deep copy
            return deepcopy(self._result)
        else:
            # Return a shallow copy
            return self._result.copy()

    def _done(self, result):
        """
        Return the result of the operation to any listeners.
        """
        self._result = result
        self._done_evt.set()
        self.done_sig.emit(operation=self)
