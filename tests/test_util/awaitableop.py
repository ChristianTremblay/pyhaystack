# -*- coding: utf-8 -*-
"""
Tests for WideSky session object
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

from threading import Timer, Event, Thread
from sys import exc_info

from asyncio import new_event_loop, ensure_future

from six import reraise

from pyhaystack.util.awaitable.operation import HaystackOperation


# Make a sub-class that we can test against.
class TestHaystackOperation(HaystackOperation):
    def __init__(self, state_machine, on_go, result_copy=True, result_deepcopy=True):
        super(TestHaystackOperation, self).__init__(result_copy, result_deepcopy)
        self._state_machine = state_machine
        self._on_go = on_go

    def go(self):
        self._on_go(self)


# A dummy result class for testing
class DummyResult(object):
    pass


# A dummy result which is copyable
class CopyableDummyResult(DummyResult):
    def __init__(self, parent=None):
        self.parent = parent
        self.copied = None

    def __copy__(self):
        c = CopyableDummyResult(self)
        c.copied = "shallow"
        return c

    def __deepcopy__(self, memo):
        c = CopyableDummyResult(self)
        c.parent = self
        c.copied = "deep"
        return c


class TestHaystackOperationAwait(object):
    """
    Test the awaitable Operation class works as expected.
    """

    def test_await_not_done(self):
        """
        Test that awaiting an operation works as expected.
        """
        # Our IO loop which we'll run in a thread
        ioloop = new_event_loop()

        # The dummy result
        RESULT = DummyResult()

        def _on_go(op):
            def _on_timeout():
                op._state_machine.finished = True
                op._done(RESULT)

            ioloop.call_later(1.0, _on_timeout)

        # Mock state machine
        class DummyStateMachine(object):
            def __init__(self):
                self.finished = False

            def is_finished(self):
                return self.finished

        # Capture the result and exception that happens in the thread
        result = {}
        done = Event()

        # The operation under test
        op = TestHaystackOperation(DummyStateMachine(), _on_go, False, False)

        async def _test_coroutine():
            try:
                # Kick things off, we shouldn't be done yet.
                op.go()
                assert op._result is None, "Should not be done yet"

                result["success"] = await op.future
            except:
                # Ooopsie
                result["error"] = exc_info()
            finally:
                # Finish up the IO loop
                ioloop.call_soon(ioloop.stop)
                done.set()

        # Launch our test
        def _launch_test():
            try:
                ensure_future(_test_coroutine())
            except:
                # Finish up the IO loop early!
                result["error"] = exc_info()
                ioloop.call_soon(ioloop.stop)
                done.set()

        ioloop.call_soon(_launch_test)
        thread = Thread(target=ioloop.run_forever)
        thread.start()
        done.wait()
        thread.join()

        # Did we succeed?
        if "error" in result:
            # Nope
            reraise(*result["error"])

        assert result["success"] is RESULT
