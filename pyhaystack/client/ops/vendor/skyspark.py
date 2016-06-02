#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skyspark operation implementations.
"""

import fysom
import hmac
import base64
import hashlib
import re

from ....util import state
from ....util.asyncexc import AsynchronousException

class SkysparkAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for Skyspark.  The procedure
    is as follows:

    1. Retrieve the log-in URL (GET request).
    2. Parse the key-values pairs returned, pick up 'username', 'userSalt' and
       'nonce'.
    3. Compute
        mac = Base64(HMAC_SHA1(key=password, msg="${username}:${userSalt}"))
    4. Compute
        digest = Base64(SHA1("${mac}:${nonce}"))
    5. POST to log-in URL:
        nonce: ${nonce}
        digest: ${digest}
    6. Stash received cookies given in the returned body.

    Future requests should the cookies returned.
    """

    _COOKIE_RE = re.compile(r'^cookie[ \t]*:[ \t]*([^=]+)=(.*)$')

    def __init__(self, session, retries=2):
        """
        Attempt to log in to the Skyspark server.

        :param session: Haystack HTTP session object.
        :param retries: Number of retries permitted in case of failure.
        """

        super(SkysparkAuthenticateOperation, self).__init__()
        print('init ops vendor skyspark')
        self._retries = retries
        self._session = session
        self._cookie = None
        self._mac = None
        self._nonce = None
        self._username = None
        self._user_salt = None
        self._digest = None
        self._login_uri = '%s/auth/%s/api?%s' % \
                (session._client.uri, session._project, session._username)
        self._salt_uri = '%s/auth/%s/api?%s' % \
                        (session._client.uri, session._project, session._username)

        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event             Current State       New State
                    ('get_new_session', 'init',             'newsession'),
                    ('do_login',        'newsession',       'login'),
                    ('login_done',      'login',            'done'),
                    ('exception',       '*',                'failed'),
                    ('retry',           'failed',           'newsession'),
                    ('abort',           'failed',           'done'),
                ], callbacks={
                    'onenternewsession':    self._do_new_session,
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
            self._state_machine.get_new_session()
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_new_session(self, event):
        """
        Request the log-in parameters.
        """
        try:
            print('do new session', self._session)
            self._session._get(self._salt_uri,
                    callback=self._on_new_session,
                    
                    cookies={}, headers={}, exclude_cookies=True,
                    exclude_headers=True, api=False)
                    #args={'username': self._session._username},
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_new_session(self, response):
        """
        Retrieve the log-in parameters.
        """
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()

            login_params = {}
            # TODO: Is this really how they send it, or is it JSON?
            # Can someone dump a sanitised version as a comment?  Seems weird
            # to have to manually parse like this.
            # RESPONSE :     
            #username:username
            #userSalt:/U7IWO9C+0DpsOhQm2x8b5gtSov0wDy1pNW8S6frD+s=
            #realm:demo
            #nonce:97029b7e8037ae40e8932b2094148423
            #onAuthEnabled:false
            for line in response.text.split('\n'):
                key, value = line.split(':')
                login_params[key] = value

            self._username = login_params['username']
            self._user_salt = login_params['userSalt']
            self._nonce = login_params['nonce']
            #self._cookies = response.cookies.copy()
            self._state_machine.do_login()
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_login(self, event):
        try:
            # Compute log-in body
#            mac = hmac.new(key=self._session._password.encode('UTF-8'),
#                    msg=("%s:%s" % (self._username, self._user_salt)).encode('UTF-8'),
#                    digestmod=hashlib.sha1)
#            digest = hashlib.sha1()
#            digest_string = '%s:%s' % (base64.b64encode(mac.digest()),(self._nonce))
#            digest.update(digest_string.encode('UTF-8'))
            mac = hmac.new(key=bytearray(self._session._password.encode('UTF-8')),
                    msg=("%s:%s" % (self._username, self._user_salt)).encode('UTF-8'),
                    digestmod=hashlib.sha1)
            
            digest = hashlib.sha1()
            digest_string = ('%s:%s' % (mac.digest(),self._nonce)).encode('UTF-8')
            digest.update(base64.b64encode(digest_string))
            # Post
            self._session._post(self._login_uri,
                    callback=self._on_login,
                    body='nonce:%s\ndigest:%s' % \
                            (self._nonce, digest.hexdigest()),
                    body_type='text/plain; charset=utf-8',
                    headers={}, exclude_cookies=True,
                    exclude_headers=True, api=False)
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_login(self, response):
        """
        See if the login succeeded.
        """
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()

            # Locate the cookie in the response.
            cookie_match = self._COOKIE_RE.match(response.text)
            if not cookie_match:
                raise IOError('No cookie in response, log-in failed.')

            (cookie_name, cookie_value) = cookie_match.groups()

            self._state_machine.login_done(result={cookie_name: cookie_value})
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
