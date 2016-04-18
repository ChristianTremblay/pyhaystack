#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VRT WideSky operation implementations.
"""

import fysom
import json
import base64

from ....util import state
from ....util.asyncexc import AsynchronousException

class WideskyAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for WideSky.  WideSky uses
    a M2M variant of OAuth2.0 to authenticate users.
    """

    def __init__(self, session, retries=2):
        """
        Attempt to log in to the VRT WideSky server.  The procedure is as
        follows:

            POST to auth_dir URI:
                Headers:
                    Accept: application/json
                    Authorization: Basic [BASE64:"[ID]:[SECRET]"]
                    Content-Type: application/json
                Body: {
                    username: "[USER]", password: "[PASSWORD]",
                    grant_type: "password"
                }
            EXPECT reply:
                Headers:
                    Content-Type: application/json
                Body:
                    {
                        access_token: ..., refresh_token: ...,
                        expires_in: ..., token_type: ...
                    }

        :param session: Haystack HTTP session object.
        :param retries: Number of retries permitted in case of failure.
        """

        super(WideskyAuthenticateOperation, self).__init__()
        self._auth_headers = {
                'Authorization': 'Basic %s' % base64.b64encode(
                    ':'.join([session._client_id,
                        session._client_secret]).encode()),
                'Accept': 'application/json',
                'Content-Type': 'application/json',
        }
        self._auth_body = json.dumps({
            'username': session._username,
            'password': session._password,
            'grant_type': 'password',
        })
        self._session = session
        self._retries = retries
        self._auth_result = None

        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event             Current State       New State
                    ('do_login',        ['init', 'failed'], 'login'),
                    ('login_done',      'login',            'done'),
                    ('exception',       '*',                'failed'),
                    ('retry',           'failed',           'login'),
                    ('abort',           'failed',           'done'),
                ], callbacks={
                    'onenterlogin':         self._do_login,
                    'onenterfailed':        self._do_fail_retry,
                    'onenterdone':          self._do_done,
                })

    def go(self):
        """
        Start the request.
        """
        # Are we logged in?
        try:
            self._state_machine.do_login()
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_login(self, event):
        try:
            self._session._post(self._session._auth_dir,
                self._on_login, body=self._auth_body,
                    headers=self._auth_headers, exclude_headers=True,
                    api=False)
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_login(self, response):
        """
        See if the login succeeded.
        """
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()

            content_type = response.headers.get('Content-Type')
            if content_type is None:
                raise ValueError('No content-type given in reply')

            if ';' in content_type:
                content_type = content_type.split(';',1)[0].strip()

            if content_type != 'application/json':
                raise ValueError('Invalid content type received: %s' % \
                        content_type)

            # Decode JSON reply
            reply = json.loads(response.body)
            for key in ('token_type', 'access_token', 'expires_in'):
                if key not in reply:
                    raise ValueError('Missing %s in reply :%s' % (key, reply))

            self._state_machine.login_done(result=reply)
        except: # Catch all exceptions to pass to caller.
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
