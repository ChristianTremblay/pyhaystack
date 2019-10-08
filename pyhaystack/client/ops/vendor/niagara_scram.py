#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Niagara 4 operation implementations.
"""

import fysom
import hmac
import re

from hashlib import sha256
from binascii import unhexlify, b2a_base64, hexlify

from ....util import state, scram
from ....util.asyncexc import AsynchronousException
from ...http.exceptions import HTTPStatusError


class Niagara4ScramAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for Niagara4.  The procedure
    is as follows:


    1. Log to the prelogin screen and send the username
    2. First Message -> Send an authentication request to the server using the salted user name and a nonce
    3. Second Message -> Send an encoded message that proves we have the password.
    4. Validate server message
    5. Send final request to j_security_check as a proof
    6. Logged

    Future requests should use the JSESSIONID cookies returned.
    """

    _COOKIE_RE = re.compile(r"^cookie[ \t]*:[ \t]*([^=]+)=(.*)$")

    def __init__(self, session, retries=0):
        """
        Attempt to log in to the Niagara 4 server.

        :param session: Haystack HTTP session object.
        :param retries: Number of retries permitted in case of failure.
        """

        super(Niagara4ScramAuthenticateOperation, self).__init__()
        self._retries = retries
        self._session = session
        self._cookie = None
        self._nonce = None
        self._username = None
        self._user_salt = None
        self._digest = None

        self._algorithm = None
        self._handshake_token = None
        self._server_first_msg = None
        self._server_nonce = None
        self._server_salt = None
        self._server_iterations = None
        self._auth_token = None
        self._auth = None

        self._login_uri = "%s" % (session._client.uri)
        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event               Current State         New State
                ("get_new_session", "init", "newsession"),
                ("do_prelogin", "newsession", "prelogin"),
                ("do_first_msg", "prelogin", "first_msg"),
                ("do_second_msg", "first_msg", "second_msg"),
                ("do_validate_login", "second_msg", "validate_login"),
                ("login_done", "validate_login", "done"),
                ("exception", "*", "failed"),
                ("retry", "failed", "newsession"),
                ("abort", "failed", "done"),
            ],
            callbacks={
                "onenternewsession": self._do_new_session,
                "onenterprelogin": self._do_prelogin,
                "onenterfirst_msg": self._do_first_msg,
                "onentersecond_msg": self._do_second_msg,
                "onentervalidate_login": self._do_validate_login,
                "onenterfailed": self._do_fail_retry,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        """
        Start the request.
        """
        try:
            self._state_machine.get_new_session()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_new_session(self, event):
        """
        Reach the prelogin page and clear everything
        """
        try:
            self._session._get(
                "%s/prelogin?clear=true" % self._login_uri,
                callback=self._on_new_session,
                cookies={},
                headers={},
                exclude_cookies=True,
                exclude_headers=True,
                api=False,
            )
        except:  # Catch all exceptions to pass to caller.
            pass

    def _on_new_session(self, response):
        if isinstance(response, AsynchronousException):
            self._state_machine.exception(result=AsynchronousException())
        else:
            try:
                if response.status_code == 200:
                    self._state_machine.do_prelogin()
                else:
                    raise HTTPStatusError("Unable to connect to server")

            except Exception as e:  # Catch all exceptions to pass to caller.
                self._state_machine.exception(result=AsynchronousException())

    def _do_prelogin(self, event):
        """
        Send the username to the prelogin page
        """
        try:
            self._session._post(
                "%s/prelogin" % self._login_uri,
                params={"j_username": self._session._username},
                callback=self._on_prelogin,
                cookies={},
                headers={},
                exclude_cookies=True,
                exclude_headers=True,
                api=False,
            )

        except:  # Catch all exceptions to pass to caller.
            pass

    def _on_prelogin(self, response):
        """
        Retrieve the log-in parameters.
        """
        try:
            self._nonce = scram.get_nonce_16()
            self._salt_username = scram.base64_no_padding(self._session._username)
            self.client_first_msg = "n=%s,r=%s" % (self._session._username, self._nonce)
            self._state_machine.do_first_msg()

        except Exception as e:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_first_msg(self, event):
        """
        Send the client first message to server
        """
        msg = (
            "action=sendClientFirstMessage&clientFirstMessage=n,,%s"
            % self.client_first_msg
        )
        cookies = dict(niagara_userid=self._session._username)

        try:
            self._session._post(
                "%s/j_security_check" % (self._login_uri),
                body=msg.encode("utf-8"),
                callback=self._on_first_msg,
                headers={"Content-Type": "application/x-niagara-login-support"},
                cookies=cookies,
                api=False,
            )

        except Exception as e:
            self._state_machine.exception(result=AsynchronousException())

    def _on_first_msg(self, response):
        """
        Retrieve the security parameters from the response.
        This includes the JSESSIONID
        """
        try:
            self.jsession = get_jession(response.headers["set-cookie"])
            self.server_first_msg = response.body.decode("utf-8")
            tab_response = self.server_first_msg.split(",")
            self.server_nonce = scram.regex_after_equal(tab_response[0])
            self.server_salt = hexlify(
                scram.b64decode(scram.regex_after_equal(tab_response[1]))
            )
            self.server_iterations = scram.regex_after_equal(tab_response[2])
            self._algorithm_name = "sha256"
            self._algorithm = sha256

            self._state_machine.do_second_msg()

        except Exception as e:
            self._state_machine.exception(result=AsynchronousException())

    def _do_second_msg(self, event):
        """
        Send the client second (final) message to server
        """
        self.salted_password = scram.salted_password_2(
            self.server_salt,
            self.server_iterations,
            self._algorithm_name,
            self._session._password,
        )
        client_final_without_proof = "c=%s,r=%s" % (
            scram.standard_b64encode(b"n,,").decode(),
            self.server_nonce,
        )
        self.auth_msg = "%s,%s,%s" % (
            self.client_first_msg,
            self.server_first_msg,
            client_final_without_proof,
        )

        client_proof = _createClientProof(
            self.salted_password, self.auth_msg, self._algorithm
        )
        client_final_message = client_final_without_proof + ",p=" + client_proof
        final_msg = "action=sendClientFinalMessage&clientFinalMessage=%s" % (
            client_final_message
        )

        cookies = dict(niagara_userid=self._session._username, JSESSIONID=self.jsession)
        try:
            self._session._post(
                "%s/j_security_check" % self._login_uri,
                body=final_msg.strip().encode("utf-8"),
                callback=self._on_second_msg,
                headers={"Content-Type": "application/x-niagara-login-support"},
                cookies=cookies,
                api=False,
            )
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _on_second_msg(self, response):
        """
        Retrieve the security parameters from the second response.
        We will compare signatures to validate the authentication
        """
        try:
            server_final_message = response.body.decode("utf-8")
            server_key = hmac.new(
                unhexlify(self.salted_password),
                "Server Key".encode("UTF-8"),
                self._algorithm,
            ).hexdigest()
            server_signature = hmac.new(
                unhexlify(server_key), self.auth_msg.encode(), self._algorithm
            ).hexdigest()
            remote_server_signature = hexlify(
                scram.b64decode(scram.regex_after_equal(server_final_message))
            )

            if server_signature == remote_server_signature.decode():
                cookies = dict(
                    JSESSIONID=self.jsession, niagara_userid=self._session._username
                )
                self._session._client.cookies = cookies
                self._state_machine.do_validate_login()

            else:
                raise Exception(
                    "Login Failed, local and remote signature are different"
                )

        except Exception as e:
            self._state_machine.exception(result=AsynchronousException())

    def _do_validate_login(self, event):
        """
        We need to send another request to the server to validate the login
        """
        try:
            self._session._post(
                "%s/j_security_check" % self._login_uri,
                body=None,
                callback=self._on_validate_login,
                headers={"Content-Type": "application/x-niagara-login-support"},
                api=False,
            )
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _on_validate_login(self, response):
        """
        Retrieve the response and set authenticated status
        """
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()
            if response.status_code == 200:
                self._state_machine.login_done(result={"authenticated": True})
            else:
                raise HTTPStatusError("Server refused the last message")

        except Exception as e:
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


def binary_encoding(string, encoding="utf-8"):
    """
    This helper function will allow compatibility with Python 2 and 3
    """
    try:
        return bytes(string, encoding)
    except TypeError:  # We are in Python 2
        return str(string)


def get_jession(arg_header):
    set_cookie = arg_header.split(",")
    for key in set_cookie:
        if "JSESSIONID=" in key:
            jsession = scram.regex_after_equal(key)
            jsession = jsession.split(";")[0]
            return jsession


def _createClientProof(salted_password, auth_msg, algorithm):
    client_key = hmac.new(
        unhexlify(salted_password), "Client Key".encode("UTF-8"), algorithm
    ).hexdigest()
    stored_key = scram._hash_sha256(unhexlify(client_key), algorithm)
    client_signature = hmac.new(
        unhexlify(stored_key), auth_msg.encode(), algorithm
    ).hexdigest()
    client_proof = scram._xor(client_key, client_signature)
    return b2a_base64(unhexlify(client_proof)).decode("utf-8")
