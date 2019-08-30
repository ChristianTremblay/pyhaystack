#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Niagara AX operation implementations.
"""

import fysom
import re

from ....util import state
from ....util.asyncexc import AsynchronousException
from ...http.auth import BasicAuthenticationCredentials
from ...http.exceptions import HTTPStatusError


class NiagaraAXAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for Niagara AX.  The procedure
    is as follows:

    1. Do a request of the log-in URL, without credentials.  This sets session
       cookies in the client.  Response should be code 200.
    2. Pick up the session cookie named 'niagara_session', submit this in
       a GET request for the login URL with a number of other parameters.
       Response should NOT include the word 'login'.

    Future requests should include the basic authentication credentials.
    """

    _LOGIN_RE = re.compile("login", re.IGNORECASE)

    def __init__(self, session, retries=0):
        """
        Attempt to log in to the Niagara AX server.

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

        super(NiagaraAXAuthenticateOperation, self).__init__()
        self._retries = retries
        self._session = session
        self._cookies = {}
        self._auth = BasicAuthenticationCredentials(
            session._username, session._password
        )

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("get_new_session", "init", "newsession"),
                ("do_login", "newsession", "login"),
                ("login_done", "login", "done"),
                ("exception", "*", "failed"),
                ("retry", "failed", "newsession"),
                ("abort", "failed", "done"),
            ],
            callbacks={
                "onenternewsession": self._do_new_session,
                "onenterlogin": self._do_login,
                "onenterfailed": self._do_fail_retry,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        """
        Start the request.
        """
        # Are we logged in?
        try:
            self._state_machine.get_new_session()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_new_session(self, event):
        """
        Request the log-in cookie.
        """
        try:
            self._session._get(
                "login",
                self._on_new_session,
                cookies={},
                headers={},
                exclude_cookies=True,
                exclude_headers=True,
                api=False,
            )
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_new_session(self, response):
        """
        Retrieve the log-in cookie.
        """
        try:
            if isinstance(response, AsynchronousException):
                try:
                    response.reraise()
                except HTTPStatusError as e:
                    if e.status == 404:
                        pass
                    else:
                        raise

            self._cookies = response.cookies.copy()
            self._state_machine.do_login()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_login(self, event):
        try:
            # Cover Niagara AX 3.7 where cookies are handled differently...
            try:
                niagara_session = self._cookies["niagara_session"]
            except KeyError:
                niagara_session = ""
            self._session._post(
                "login",
                self._on_login,
                params={
                    "token": "",
                    "scheme": "cookieDigest",
                    "absPathBase": "/",
                    "content-type": "application/x-niagara-login-support",
                    "Referer": self._session._client.uri + "login/",
                    "accept": "text/zinc; charset=utf-8",
                    "cookiePostfix": niagara_session,
                },
                headers={},
                cookies=self._cookies,
                exclude_cookies=True,
                exclude_proxies=True,
                api=False,
                auth=self._auth,
            )
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_login(self, response):
        """
        See if the login succeeded.
        """
        try:
            if isinstance(response, AsynchronousException):
                try:
                    response.reraise()
                except HTTPStatusError as e:
                    if e.status == 404:
                        pass
                    else:
                        raise

            else:
                if self._LOGIN_RE.match(response.text):
                    # No good.
                    raise IOError("Login failed")

            self._state_machine.login_done(result=(self._auth, self._cookies))
        except:  # Catch all exceptions to pass to caller.
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
