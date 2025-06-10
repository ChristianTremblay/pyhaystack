# -*- coding: utf-8 -*-
"""
Tests for BaseHaystackOperation object
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

from sys import exc_info
from threading import Event, Thread, Timer

from six import reraise
from tornado.gen import coroutine
from tornado.ioloop import IOLoop

from pyhaystack.util.asyncexc import AsynchronousException
from pyhaystack.util.operation import BaseHaystackOperation, NotReadyError


# Make a sub-class that we can test against.
class HaystackOperation(BaseHaystackOperation):
    def __init__(self, state_machine, on_go, result_copy=True, result_deepcopy=True):
        super(HaystackOperation, self).__init__(result_copy, result_deepcopy)
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


class TestHaystackOperation(object):
    """
    Test the base Operation class works as expected.
    """

    # -- wait operation --

    def test_wait_infinite(self):
        """
        Test that calling wait blocks until the operation is complete.
        """
        RESULT = DummyResult()

        def _on_go(op):
            def _on_timeout():
                op._done(RESULT)

            Timer(1.0, _on_timeout).start()

        op = HaystackOperation(None, _on_go, False, False)
        op.go()
        assert op._result is None, "Should not be done yet"

        op.wait()
        assert op._result is RESULT, "Should be done now"

    def test_wait_finite(self):
        """
        Test that calling wait blocks for the time period prescribed.
        """
        RESULT = DummyResult()

        def _on_go(op):
            def _on_timeout():
                op._done(RESULT)

            Timer(1.0, _on_timeout).start()

        op = HaystackOperation(None, _on_go, False, False)
        op.go()
        assert op._result is None, "Should not be done yet"

        op.wait(0.5)
        assert op._result is None, "Should not be done yet"

        op.wait(1.0)
        assert op._result is RESULT, "Should be done now"

    # -- future --

    def test_future_not_done(self):
        """
        Test that the 'future' returns a future that resolves on done.
        """
        # Our IO loop which we'll run in a thread
        ioloop = IOLoop()

        # The dummy result
        RESULT = DummyResult()

        def _on_go(op):
            def _on_timeout():
                op._state_machine.finished = True
                op._done(RESULT)

            ioloop.add_timeout(ioloop.time() + 1.0, _on_timeout)

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
        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)

        @coroutine
        def _test_coroutine():
            try:
                # Kick things off, we shouldn't be done yet.
                op.go()
                assert op._result is None, "Should not be done yet"

                result["success"] = yield op.future
            except:
                # Ooopsie
                result["error"] = exc_info()
            finally:
                # Finish up the IO loop
                ioloop.add_callback(ioloop.stop)
                done.set()

        # Launch our test
        ioloop.add_callback(_test_coroutine)
        thread = Thread(target=ioloop.start)
        thread.start()
        done.wait()
        thread.join()

        # Did we succeed?
        if "error" in result:
            # Nope
            reraise(*result["error"])

        assert result["success"] is RESULT

    def test_future_failed(self):
        """
        Test that the 'future' returns exception if operation fails.
        """

        # The error we'll raise
        class MyError(RuntimeError):
            pass

        # Our IO loop which we'll run in a thread
        ioloop = IOLoop()

        def _on_go(op):
            def _on_timeout():
                try:
                    raise MyError("Whoopsie!")
                except:
                    op._state_machine.finished = True
                    op._done(AsynchronousException())

            ioloop.add_timeout(ioloop.time() + 1.0, _on_timeout)

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
        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)

        @coroutine
        def _test_coroutine():
            try:
                # Kick things off, we shouldn't be done yet.
                op.go()
                assert op._result is None, "Should not be done yet"

                yield op.future
                assert False, "Should not have passed"
            except:
                # Ooopsie
                result["error"] = exc_info()
            finally:
                # Finish up the IO loop
                ioloop.add_callback(ioloop.stop)
                done.set()

        # Launch our test
        ioloop.add_callback(_test_coroutine)
        thread = Thread(target=ioloop.start)
        thread.start()
        done.wait()
        thread.join()

        # We expect an error
        assert "error" in result

        try:
            reraise(*result["error"])
        except MyError:
            pass

    def test_future_done(self):
        """
        Test that the 'future' resolves immediately if the operation is done
        """
        RESULT = DummyResult()

        def _on_go(op):
            assert False, "This should not have been called"

        # Mock state machine
        class DummyStateMachine(object):
            def is_finished(self):
                return True

        # Capture the result and exception that happens in the thread
        result = {}
        done = Event()

        # Our IO loop which we'll run in a thread
        ioloop = IOLoop()

        # The operation under test
        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)

        # Seed it with a result
        op._result = RESULT

        @coroutine
        def _test_coroutine():
            try:
                result["success"] = yield op.future
            except:
                # Ooopsie
                result["error"] = exc_info()
            finally:
                # Finish up the IO loop
                ioloop.add_callback(ioloop.stop)
                done.set()

        # Launch our test
        ioloop.add_callback(_test_coroutine)
        thread = Thread(target=ioloop.start)
        thread.start()
        done.wait()
        thread.join()

        # Did we succeed?
        if "error" in result:
            # Nope
            reraise(*result["error"])

        assert result["success"] is RESULT

    # -- state --

    def test_state(self):
        """
        Test that .state returns the current state machine state.
        """

        class DummyStateMachine(object):
            def __init__(self):
                self.current = "init"

        sm = DummyStateMachine()
        op = HaystackOperation(sm, lambda: None, False, False)

        assert op.state == "init"

        sm.current = "anotherstate"
        assert op.state == "anotherstate"

    # -- is_done --

    def test_is_done(self):
        """
        Test that .is_done returns True if the state machine is done.
        """

        class DummyStateMachine(object):
            def __init__(self):
                self.finished = False

            def is_finished(self):
                return self.finished

        sm = DummyStateMachine()
        op = HaystackOperation(sm, lambda: None, False, False)

        assert not op.is_done

        sm.finished = True
        assert op.is_done

    # -- is_failed --

    def test_is_failed(self):
        """
        Test that .is_failed returns True if the result is an error.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            try:
                raise RuntimeError("Test error")
            except:
                op._done(AsynchronousException())

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)
        assert not op.is_failed

        op.go()

        assert op.is_failed

    # -- result --

    def test_result_notready(self):
        """
        Test that .result raises an error if the result isn't ready yet.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return False

        def _on_go(op):
            assert False, "Should not have worked"

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)

        try:
            assert op.result is None
            assert False, "Should not have worked"
        except NotReadyError:
            pass

    def test_result_failed(self):
        """
        Test that .result re-raises the received error if failed.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        class MyError(RuntimeError):
            pass

        def _on_go(op):
            try:
                raise MyError("Test error")
            except:
                op._done(AsynchronousException())

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)
        op.go()
        op.wait()

        try:
            assert op.result is None
            assert False, "Should not have worked"
        except MyError:
            pass

    def test_result_nocopy(self):
        """
        Test that .result returns the given object if result_copy=False.
        """
        RESULT = DummyResult()

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            op._done(RESULT)

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)
        op.go()
        op.wait()

        assert op.result is RESULT

    def test_result_shallowcopy(self):
        """
        Test that .result returns a shallow copy if result_deepcopy=False.
        """
        RESULT = CopyableDummyResult()

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            op._done(RESULT)

        op = HaystackOperation(DummyStateMachine(), _on_go, True, False)
        op.go()
        op.wait()

        assert op.result is not RESULT
        assert isinstance(op.result, CopyableDummyResult)
        assert op.result.parent is RESULT
        assert op.result.copied == "shallow"

    def test_result_deepcopy(self):
        """
        Test that .result returns a shallow copy if result_deepcopy=True.
        """
        RESULT = CopyableDummyResult()

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            op._done(RESULT)

        op = HaystackOperation(DummyStateMachine(), _on_go, True, True)
        op.go()
        op.wait()

        assert op.result is not RESULT
        assert isinstance(op.result, CopyableDummyResult)
        assert op.result.parent is RESULT
        assert op.result.copied == "deep"

    # -- repr --

    def test_repr_failed(self):
        """
        Test that .__repr__() returns whether an operation failed.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            try:
                raise RuntimeError("Test error")
            except:
                op._done(AsynchronousException())

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)
        op.go()

        assert repr(op) == "<HaystackOperation failed>"

    def test_repr_done(self):
        """
        Test that .__repr__() returns a representation of the result if done.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        def _on_go(op):
            op._done(12345)

        op = HaystackOperation(DummyStateMachine(), _on_go, False, False)
        op.go()

        assert repr(op) == "<HaystackOperation done: 12345>"

    def test_repr_in_progress(self):
        """
        Test that .__repr__() returns a representation of the result if done.
        """

        class DummyStateMachine(object):
            def __init__(self):
                self.current = "mystate"

            def is_finished(self):
                return False

        op = HaystackOperation(DummyStateMachine(), lambda: None, False, False)

        assert repr(op) == "<HaystackOperation mystate>"

    # -- _done --

    def test_done(self):
        """
        Test that ._done stores the result and triggers notifications.
        """

        class DummyStateMachine(object):
            def is_finished(self):
                return True

        done_call = {}

        op = HaystackOperation(DummyStateMachine(), lambda: None, False, False)
        op.done_sig.connect(lambda **kwa: done_call.update(kwa))

        assert op._result is None
        assert not op._done_evt.is_set()
        assert len(done_call) == 0

        op._done("my result")

        assert op._result == "my result"
        assert op._done_evt.is_set()
        assert len(done_call) == 1
        assert done_call["operation"] is op
