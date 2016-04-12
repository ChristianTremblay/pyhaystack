#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Low-level grid state machines.  These are state machines that perform GET or
POST requests involving Haystack ZINC grids.
"""

import hszinc
import fysom

import shlex
from ...util import state
from ...exception import HaystackError
from ...util.asyncexc import AsynchronousException

class BaseGridOperation(state.HaystackOperation):
    """
    A base class for GET and POST operations involving grids.
    """

    def __init__(self, session, uri, args=None,
            expect_format=hszinc.MODE_ZINC, multi_grid=False,
            raw_response=False, retries=2):
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
        """

        super(BaseGridOperation, self).__init__()
        self._retries = retries
        self._session = session
        self._multi_grid = multi_grid
        self._uri = uri
        self._args = args
        self._expect_format = expect_format
        self._raw_response = raw_response
        self._headers = {}

        if not raw_response:
            if expect_format == hszinc.MODE_ZINC:
                self._headers['Accept'] = 'text/zinc'
            elif expect_format == hszinc.MODE_JSON:
                self._headers['Accept'] = 'application/json'
            elif expect_format is not None:
                raise ValueError(
                        'expect_format must be one onf hszinc.MODE_ZINC '\
                        'or hszinc.MODE_JSON')

        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event             Current State       New State
                    ('auth_ok',         'init',             'submit'),
                    ('auth_not_ok',     'init',             'auth_attempt'),
                    ('auth_ok',         'auth_attempt',     'submit'),
                    ('auth_not_ok',     'auth_attempt',     'done'),
                    ('auth_failed',     'auth_attempt',     'done'),
                    ('response_ok',     'submit',           'done'),
                    ('exception',       '*',                'failed'),
                    ('retry',           'failed',           'init'),
                    ('abort',           'failed',           'done'),
                ], callbacks={
                    'onenterauth_attempt':  self._do_auth_attempt,
                    'onentersubmit':        self._do_submit,
                    'onenterfailed':        self._do_fail_retry,
                    'onenterdone':          self._do_done,
                })

    def go(self):
        """
        Start the request.
        """
        # Are we logged in?
        try:
            if self._session.is_logged_in:
                self._state_machine.auth_ok()
            else:
                self._state_machine.auth_not_ok()
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Authentication check fails', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_auth_attempt(self, event):
        """
        Tell the session object to log in, then call us back.
        """
        try:
            self._session.authenticate(callback=self._on_authenticate)
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_authenticate(self, **kwargs):
        """
        Retry the authentication check.
        """
        self._log.debug('Authenticated, trying again')
        self.go()

    def _on_response(self, response):
        """
        Process the response given back by the HTTP server.
        """
        try:
            # Process the HTTP error, if any.
            if isinstance(response, AsynchronousException):
                response.reraise()

            # What format grid did we get back?
            content_type = response.headers.get('Content-Type')
            if content_type is None:
                raise ValueError('Content-Type header missing in reply')

            # Is content encoding shoehorned in there?
            if ';' in content_type:
                (content_type, content_type_args) = content_type.split(';',1)
                content_type = content_type.strip()
                content_type_args = dict([tuple(kv.split('=',1)) for kv in 
                        shlex.split(content_type_args)])
            else:
                content_type_args = {}

            # TODO: Unicode characters are supposed to be escaped,
            # but are they?  Inspect content_type_args to make sure.

            # If we're expecting a raw response back, then just hand the
            # request object back and finish here.
            if self._raw_response:
                self._state_machine.response_ok(result=response)
                return

            if content_type in ('text/zinc', 'text/plain'):
                # We have been given a grid in ZINC format.
                decoded = hszinc.parse(response.body, mode=hszinc.MODE_ZINC)
            elif content_type == 'application/json':
                # We have been given a grid in JSON format.
                decoded = [hszinc.parse(response.body, mode=hszinc.MODE_JSON)]
            else:
                # We don't recognise this!
                raise ValueError('Unrecognised content type %s' % content_type)

            # Check for exceptions
            def _check_err(grid):
                try:
                    if 'err' in grid.metadata:
                        raise HaystackError(
                                grid.metadata.get('dis', 'Unknown Error'),
                                grid.metadata.get('traceback', None))
                    return grid
                except:
                    return AsynchronousException()
            decoded = [_check_err(g) for g in decoded]
            if not self._multi_grid:
                decoded = decoded[0]

            # If we get here, then the request itself succeeded.
            self._state_machine.response_ok(result=decoded)
        except: # Catch all exceptions for the caller.
            self._log.debug('Parse fails', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_fail_retry(self, event):
        """
        Determine whether we retry or fail outright.
        """
        if self._retries > 0:
            self._retries -= 1
            self._state_machine.retry()
        else:
            self._state_machine.abort(result=event.result)

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


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
        self._log = session._log.getChild('get_grid.%s' % uri)
        super(GetGridOperation, self).__init__(
                session=session, uri=uri, args=args,
                multi_grid=multi_grid, **kwargs)

    def _do_submit(self, event):
        """
        Submit the GET request to the haystack server.
        """

        try:
            self._session._get(self._uri, params=self._args,
                    headers=self._headers, callback=self._on_response)
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Get fails', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())


class PostGridOperation(BaseGridOperation):
    """
    A state machine that performs a POST operation with a ZINC grid then may
    read back a ZINC grid.
    """

    def __init__(self, session, uri, grid, args=None,
            post_format=hszinc.MODE_ZINC, **kwargs):
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
        self._log = session._log.getChild('post_grid.%s' % uri)
        super(PostGridOperation, self).__init__(
                session=session, uri=uri, args=args, **kwargs)

        # Convert the grids to their native format
        self._body = hszinc.dump(grid, mode=post_format)
        if post_format == hszinc.MODE_ZINC:
            self._content_type = 'text/zinc'
        else:
            self._content_type = 'application/json'

    def _do_submit(self, event):
        """
        Submit the GET request to the haystack server.
        """
        try:
            self._session._post(self._uri, body=self._body,
                    body_type=self._content_type, params=self._args,
                    headers=self._headers, callback=self._on_response)
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Post fails', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())
