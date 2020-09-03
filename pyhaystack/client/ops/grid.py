#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Low-level grid state machines.  These are state machines that perform GET or
POST requests involving Haystack ZINC grids.
"""

import hszinc
import fysom

from ...util import state
from ...exception import HaystackError, AuthenticationProblem
from ...util.asyncexc import AsynchronousException
from six import string_types
from time import time


def dict_to_grid(d):
    if not "id" in d.keys():
        raise ValueError('Dict must contain an "id" key.')
    new_grid = hszinc.Grid()
    new_grid.metadata["id"] = d["id"]
    for k, v in d.items():
        new_grid.column[k] = {}
    new_grid.append(d)
    return new_grid


class BaseAuthOperation(state.HaystackOperation):
    """
    A base class authentication operations.
    """

    def __init__(self, session, uri, retries=2, cache=False):
        """
        Initialise a request for the authenticating with the given URI and arguments.

        It also contains the state machine for reconnection if needed.

        :param session: Haystack HTTP session object.
        :param uri: Possibly partial URI relative to the server base address
                    to perform a query.  No arguments shall be given here.
        :param retries: Number of retries permitted in case of failure.
        :param cache: Whether or not to cache this result.  If True, the
                      result is cached by the session object.
        """

        super(BaseAuthOperation, self).__init__()

        self._retries = retries
        self._session = session
        self._uri = uri
        self._headers = {}

        self._cache = cache

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("auth_ok", "init", "check_cache"),
                ("auth_not_ok", "init", "auth_attempt"),
                ("auth_ok", "auth_attempt", "check_cache"),
                ("auth_not_ok", "auth_attempt", "auth_failed"),
                ("auth_failed", "auth_attempt", "done"),
                ("cache_hit", "check_cache", "done"),
                ("cache_miss", "check_cache", "submit"),
                ("response_ok", "submit", "done"),
                ("exception", "*", "failed"),
                ("retry", "failed", "init"),
                ("abort", "failed", "done"),
            ],
            callbacks={
                "onretry": self._check_auth,
                "onenterauth_attempt": self._do_auth_attempt,
                "onenterauth_failed": self._do_auth_failed,
                "onentercheck_cache": self._do_check_cache,
                "onentersubmit": self._do_submit,
                "onenterfailed": self._do_fail_retry,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        """
        Start the request.
        """
        self._check_auth()

    def _check_auth(self, *args):
        """
        Check authentication.
        """
        # Are we logged in?
        try:
            if self._session.is_logged_in:
                self._state_machine.auth_ok()
            else:
                self._state_machine.auth_not_ok()
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Authentication check fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_auth_attempt(self, event):
        """
        Tell the session object to log in, then call us back.
        """
        try:
            self._session.authenticate(callback=self._on_authenticate)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_authenticate(self, *args, **kwargs):
        """
        Retry the authentication check.
        """
        self._log.debug("Authenticated, trying again")
        self.go()

    def _do_check_cache(self, event):
        """
        Implement if needed
        """
        self._state_machine.cache_miss()  # Nope
        return

    def _on_response(self, response):
        raise NotImplementedError()

    def _do_fail_retry(self, event):
        """
        Determine whether we retry or fail outright.
        """
        if self._retries > 0:
            self._retries -= 1
            self._state_machine.retry()
        else:
            self._state_machine.abort(result=event.result)

    def _do_auth_failed(self, event):
        """
        Raise and capture an authentication failure.
        """
        try:
            raise AuthenticationProblem()
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class BaseGridOperation(BaseAuthOperation):
    """
    A base class for GET and POST operations involving grids.
    """

    def __init__(
        self,
        session,
        uri,
        args=None,
        expect_format=hszinc.MODE_ZINC,
        multi_grid=False,
        raw_response=False,
        retries=2,
        cache=False,
        cache_key=None,
        accept_status=None,
        headers=None,
        exclude_cookies=None,
    ):
        """
        Initialise a request for the grid with the given URI and arguments.

        :param session: Haystack HTTP session object.
        :param uri: Possibly partial URI relative to the server base address
                    to perform a query.  No arguments shall be given here.
        :param expect_format: Request that the grid be sent in the given format.
        :param args: Dictionary of key-value pairs to be given as arguments.
        :param multi_grid: Boolean indicating if we are to expect multiple
                           grids or not.  If True, then the operation will
                           _always_ return a list, otherwise, it will _always_
                           return a single grid.
        :param raw_response: Boolean indicating if we should try to parse the
                             result.  If True, then we should just pass back the
                             raw HTTPResponse object.
        :param retries: Number of retries permitted in case of failure.
        :param cache: Whether or not to cache this result.  If True, the
                      result is cached by the session object.
        :param cache_key: Name of the key to use when the object is cached.
        :param accept_status: What status codes to accept, in addition to the
                            usual ones?
        :param exclude_cookies:
                        If True, exclude all default cookies and use only
                        the cookies given.  Otherwise, this is an iterable
                        of cookie names to be excluded.
        """

        super(BaseGridOperation, self).__init__(session, uri)
        if args is not None:
            # Convert scalars to strings
            args = dict(
                [
                    (
                        param,
                        hszinc.dump_scalar(value)
                        if not isinstance(value, string_types)
                        else value,
                    )
                    for param, value in args.items()
                ]
            )

        self._retries = retries
        self._session = session
        self._multi_grid = multi_grid
        self._uri = uri
        self._args = args
        self._expect_format = expect_format
        self._raw_response = raw_response
        self._headers = headers if headers else {}
        self._accept_status = accept_status
        self._exclude_cookies = exclude_cookies

        self._cache = cache
        if cache and (cache_key is None):
            cache_key = uri
        self._cache_key = cache_key

        if expect_format == hszinc.MODE_ZINC:
            self._headers[b"Accept"] = "text/zinc"
        elif expect_format == hszinc.MODE_JSON:
            self._headers[b"Accept"] = "application/json"
        elif expect_format is not None:
            raise ValueError(
                "expect_format must be one onf hszinc.MODE_ZINC " "or hszinc.MODE_JSON"
            )

    def _do_check_cache(self, event):
        """
        See if there's cache for this grid.
        """
        if not self._cache:
            self._state_machine.cache_miss()  # Nope
            return

        # Initialise data
        op = None
        grid = None
        expiry = 0.0

        with self._session._grid_lk:
            try:
                (op, expiry, grid) = self._session._grid_cache[self._cache_key]
            except KeyError:
                # Not in cache
                pass

            if (grid is None) or (expiry <= time()):
                # We have a cache miss.
                op = self
                grid = None
                self._session._grid_cache[self._cache_key] = (op, expiry, grid)

        if grid is not None:
            self._state_machine.cache_hit(result=grid)
            return

        if op is self:
            # We're it, go and get it.
            self._state_machine.cache_miss()
        else:
            # Wait for that state machine to finish and proxy its result.
            def _proxy(op):
                try:
                    res = op.result
                except:
                    self._state_machine.exception(AsynchronousException())
                    return

                self._state_machine.cache_hit(res)

            op.done_sig.connect(_proxy)

    def _on_response(self, response):
        """
        Process the response given back by the HTTP server.
        """
        # When problems occur :
        # print("RESPONSE", response.__dict__)
        try:
            # Does the session want to invoke any relevant hooks?
            # This allows a session to detect problems in the session and
            # abort the operation.
            if hasattr(self._session, "_on_http_grid_response"):
                self._session._on_http_grid_response(response)

            # Process the HTTP error, if any.
            if isinstance(response, AsynchronousException):
                response.reraise()

            # If we're expecting a raw response back, then just hand the
            # request object back and finish here.
            if self._raw_response:
                self._state_machine.response_ok(result=response)
                return

            # What format grid did we get back?
            content_type = response.content_type
            body = response.text

            if content_type in ("text/zinc", "text/plain"):
                # We have been given a grid in ZINC format.
                decoded = hszinc.parse(body, mode=hszinc.MODE_ZINC, single=False)
            elif content_type == "application/json":
                # We have been given a grid in JSON format.
                decoded = hszinc.parse(body, mode=hszinc.MODE_JSON, single=False)
            elif content_type in ("text/html"):
                # We probably fell back to a login screen after auto logoff.
                self._state_machine.exception(AsynchronousException())
            else:
                # We don't recognise this!
                raise ValueError("Unrecognised content type %s" % content_type)

            # Check for exceptions
            def _check_err(grid):
                try:
                    if "err" in grid.metadata:
                        raise HaystackError(
                            grid.metadata.get("dis", "Unknown Error"),
                            grid.metadata.get("traceback", None),
                        )
                    return grid
                except:
                    return AsynchronousException()

            decoded = [_check_err(g) for g in decoded]
            if not self._multi_grid:
                decoded = decoded[0]

            # If we get here, then the request itself succeeded.
            if self._cache:
                with self._session._grid_lk:
                    self._session._grid_cache[self._cache_key] = (
                        None,
                        time() + self._session._grid_expiry,
                        decoded,
                    )
            self._state_machine.response_ok(result=decoded)
        except:  # Catch all exceptions for the caller.
            self._log.debug("Parse fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())


class GetGridOperation(BaseGridOperation):
    """
    A state machine that performs a GET operation then reads back a ZINC grid.
    """

    def __init__(self, session, uri, args=None, multi_grid=False, **kwargs):
        """
        Initialise a GET request for the grid with the given URI and arguments.

        :param session: Haystack HTTP session object.
        :param uri: Possibly partial URI relative to the server base address
                    to perform a query.  No arguments shall be given here.
        :param args: Dictionary of key-value pairs to be given as arguments.
        :param multi_grid: Boolean indicating if we are to expect multiple
                           grids or not.  If true, then the operation will
                           _always_ return a list, otherwise, it will _always_
                           return a single grid.
        """
        self._log = session._log.getChild("get_grid.%s" % uri)
        super(GetGridOperation, self).__init__(
            session=session, uri=uri, args=args, multi_grid=multi_grid, **kwargs
        )

    def _do_submit(self, event):
        """
        Submit the GET request to the haystack server.
        """

        try:
            self._session._get(
                self._uri,
                params=self._args,
                headers=self._headers,
                callback=self._on_response,
                accept_status=self._accept_status,
                exclude_cookies=self._exclude_cookies,
            )
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Get fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())


class PostGridOperation(BaseGridOperation):
    """
    A state machine that performs a POST operation with a ZINC grid then may
    read back a ZINC grid.
    """

    def __init__(
        self, session, uri, grid, args=None, post_format=hszinc.MODE_ZINC, **kwargs
    ):
        """
        Initialise a POST request for the grid with the given grid,
        URI and arguments.

        :param session: Haystack HTTP session object.
        :param uri: Possibly partial URI relative to the server base address
                    to perform a query.  No arguments shall be given here.
        :param grid: Grid (or grids) to be posted to the server.
        :param post_format: What format to post grids in?
        :param args: Dictionary of key-value pairs to be given as arguments.
        """
        self._log = session._log.getChild("post_grid.%s" % uri)
        super(PostGridOperation, self).__init__(
            session=session, uri=uri, args=args, **kwargs
        )
        # Convert the grids to their native format
        self._body = hszinc.dump(grid, mode=post_format).encode("utf-8")
        if post_format == hszinc.MODE_ZINC:
            self._content_type = "text/zinc"
        else:
            self._content_type = "application/json"

    def _do_submit(self, event):
        """
        Submit the POST request to the haystack server.
        """
        try:
            self._session._post(
                self._uri,
                body=self._body,
                body_type=self._content_type,
                params=self._args,
                headers=self._headers,
                callback=self._on_response,
                accept_status=self._accept_status,
                exclude_cookies=self._exclude_cookies,
            )
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Post fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())
